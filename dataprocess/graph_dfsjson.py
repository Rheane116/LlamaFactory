import re
import json
from collections import defaultdict
from file_utils import *
import copy
import sys

# =============== 1. 辅助工具 (保持原有风格) ==================

def get_text_order(main_str, sub_str):
    """ 在文本中定位实体起始索引，用于排序 """
    if not sub_str: return -1
    # 按照原文件逻辑，精确匹配单词边界
    escaped_sub = re.escape(sub_str)
    pattern = re.compile(r'(?<!\w)' + escaped_sub + r'(?!\w)')
    match = pattern.search(main_str)
    return match.start() if match else -1

# =============== 2. 序列化逻辑 (List + Nested + New Keys) ==================

def serialize_to_list_format(entities, relations, text):
    """
    将图序列化为：[{"span": "...", "type": "...", "targets": [...]}, ...]
    """
    if not entities:
        return []

    # 1. 建立邻接表
    adj = defaultdict(list)
    for head, rel, tail in relations:
        adj[head].append((rel, tail))
    
    # 2. 邻接节点按文本顺序排序
    for head in adj:
        adj[head].sort(key=lambda x: get_text_order(text, x[1]))

    # 3. 获取所有可能的根节点初始排序 (文本中出现顺序)
    all_entity_names = sorted(entities.keys(), key=lambda en: get_text_order(text, en))
    
    visited = set()

    def build_branch(node_name, rel_type=None):
        """ 递归构建分支 """
        # 情况 A: 重复访问 -> 使用 ref
        if node_name in visited:
            res = {"ref": node_name}
            if rel_type: res = {"relation": rel_type, "ref": node_name}
            return res
        
        # 标记访问
        visited.add(node_name)
        
        # 情况 B: 第一次访问 -> 完整定义
        node_data = {
            "span": node_name,
            "type": entities[node_name]
        }
        
        # 递归处理下游 targets
        targets = []
        for rel, tail in adj.get(node_name, []):
            targets.append(build_branch(tail, rel))
        
        if targets:
            node_data["targets"] = targets
            
        # 如果带有关系类型（即不是根节点），则合并字段
        if rel_type:
            return {"relation": rel_type, **node_data}
        return node_data

    # 构建最终的 List 结构
    final_output = []
    for entity in all_entity_names:
        # 按照 DFS 逻辑：如果某实体已经在之前其他实体的路径中被访问过，
        # 在顶层列表中它将显示为 {"if type(json_list) != dict:
        if entity in visited:
            continue
        final_output.append(build_branch(entity))

    return final_output

# =============== 3. 解析还原逻辑 ==================

def deserialize_list_format(json_list):
    """
    将 JSON 列表还原回原始的 entities 和 relations 格式
    """
    entities = {}
    relations = []

    def traverse(item, parent_name=None):
        # 先处理实体定义（如果存在）
        node_name = None
        if "span" in item:
            node_name = item["span"]
            try: 
                node_type = item["type"]
            except Exception as e:
                node_type = "UNKNOWN"
            
            if node_name not in entities:
                entities[node_name] = node_type
        
        # 处理关系引用（如果存在）
        if "ref" in item:
            ref_name = item["ref"]
            if parent_name and "relation" in item:
                relations.append([parent_name, item["relation"], ref_name])
            # 如果只有引用没有实体定义，直接返回
            if node_name is None:
                return
        
        # 如果有实体定义，记录与父节点的关系（如果有）
        if node_name and parent_name and "relation" in item:
            relations.append([parent_name, item["relation"], node_name])
            
        # 递归遍历子节点
        for target in item.get("targets", []):
            traverse(target, node_name)

    #print(json_list)
    if len(json_list) == 0 or type(json_list[0]) != dict:
        return {"entities": {}, "relations": []}
     
    # 遍历顶层节点
    for root_item in json_list:
        traverse(root_item)

    # 关系去重
    unique_rels = []
    for r in relations:
        if r not in unique_rels: unique_rels.append(r)

    return {"entities": entities, "relations": unique_rels}

# =============== VALIDATION ==================
def verify(original, recovered):
    orig_edges = sorted(original["relations"])
    reco_edges = sorted(recovered["relations"])
    nodes_match = original["entities"] == recovered["entities"]
    edges_match = orig_edges == reco_edges
    
    print(f"\nNodes Match: {nodes_match}")
    print(f"Edges Match: {edges_match}")
    if not edges_match:
        print("Original edges count:", len(orig_edges))
        print("Recovered edges count:", len(reco_edges))
    return nodes_match and edges_match

# =============== 4. 运行示例 ==================

if __name__ == "__main__":
    args = sys.argv
    '''if len(args) != 3:
        print("Usage: python graph_dfs.py <dataset> <split>")
        sys.exit(1)
    dataset = args[1]
    split = args[2]'''

    from tqdm import tqdm
    #datasets = ["conll04", "scierc", "ace2005"]
    datasets = ["scierc"]
    splits = ["train", "dev", "test"]

    for dataset in datasets:
        for split in splits:
            datalist = read_jsonl(f"data_raw/{dataset}/{split}_graph_mapped.jsonl")
            datalist_new = list()

            for i, data in tqdm(enumerate(datalist)):
                print(f"Processing {i + 1}th data...")
                if len(data['entities']) < 1:
                    serialized_list = "[]"
                else:       
                    text = data['sentences']
                    G = {"entities": data['entities'], "relations": data['relations']}

                    # 序列化
                    # 执行序列化
                    serialized_list = serialize_to_list_format(G["entities"], G["relations"], text)

                    print("--- 序列化结果 (JSON List) ---")
                    print(json.dumps(serialized_list, indent=2, ensure_ascii=False))

                    # 执行解析
                    restored_G = deserialize_list_format(serialized_list)
                    print("\n--- 实际数据结构 ---")
                    print(json.dumps(G, indent=2, ensure_ascii=False))
                    print("\n--- 还原后的数据结构 ---")
                    print(json.dumps(restored_G, indent=2, ensure_ascii=False))

                    if_match = verify(G, restored_G)
                    print(f"Matched:{if_match}")

                    if not if_match:
                        print("Not match!!!!")
                        sys.exit(0)
                    print("--------------------------------")
                data_new = copy.deepcopy(data)
                #data_new["serialized"] = json.dumps(serialized_list, ensure_ascii=False)
                data_new["serialized"] = serialized_list
                datalist_new.append(data_new)
            write_jsonl_w(f"data_raw/{dataset}/{split}_graph_serialized_dfsjson.jsonl", datalist_new)
            write_json(f"data_raw/{dataset}/{split}_graph_serialized_dfsjson.json", datalist_new)


    '''text = "Holding a framed picture of her son , serving with the Army 's 3rd Infantry Division in Iraq , she said she did n't know whether he was dead or alive ."

    G = {
       "entities": {"3rd Infantry Division": {"type": "ORG"}, "Army": {"type": "ORG"}, "Iraq": {"type": "GPE"}, "he": {"type": "PER"}, "her": {"type": "PER"}, "she": {"type": "PER"}, "son": {"type": "PER"}}, "relations": [["3rd Infantry Division", "GEN-AFF", "Iraq"], ["3rd Infantry Division", "PART-WHOLE", "Army"], ["her", "PER-SOC", "son"], ["son", "ORG-AFF", "3rd Infantry Division"], ["son", "PHYS", "Iraq"]]}

    # 执行序列化
    #serialized_list = serialize_to_list_format(G["entities"], G["relations"], text)
    
    #print("--- 序列化结果 (JSON List) ---")
    serialized_list = "[{\"span\": \"propylthiouracil\", \"type\": \"Drug\"}, {\"span\": \"PTU\", \"type\": \"Drug\", \"relation\": \"adverse_effect\", \"ref\": \"propylthiouracil\"}, {\"span\": \"Acute hepatic failure\", \"type\": \"Adverse-Effect\", \"targets\": [{\"relation\": \"adverse_effect\", \"ref\": \"propylthiouracil\"}, {\"relation\": \"adverse_effect\", \"ref\": \"PTU\"}]}]"
    #print(json.dumps(serialized_list, indent=2, ensure_ascii=False))
    serialized_list = json.loads(serialized_list)
    # 执行解析
    restored_G = deserialize_list_format(serialized_list)
    print("\n--- 还原后的数据结构 ---")
    print(json.dumps(restored_G, indent=2, ensure_ascii=False))
    #print(f"Matched:{verify(G, restored_G)}")'''