import collections
import re
import json
import copy
import sys
from file_utils import *



def get_text_order(main_str, sub_str):
    """
    在母串中全字匹配子串（考虑空格/特殊字符），返回第一个匹配位置的起始索引
    :param main_str: 母串（被搜索的字符串）
    :param sub_str: 子串（需全字匹配，可包含空格、单引号等特殊字符）
    :return: int，第一个匹配的起始索引；无匹配返回 -1
    """
    #sub_str = sub_str.replace("_", " ")
    # 1. 转义子串中的正则特殊字符（如'、.、*等），确保按字面量匹配
    escaped_sub = re.escape(sub_str)
    
    # 2. 构建全字匹配规则：子串前后是「非单词字符/字符串边界」
    # (?<!\w)：前面不是单词字符（字母/数字/下划线）；(?!\w)：后面不是单词字符
    # \s* 兼容子串前后可能的空格（可选，根据实际需求）
    pattern = re.compile(r'(?<!\w)' + escaped_sub + r'(?!\w)')
    
    # 3. 搜索第一个匹配项
    match = pattern.search(main_str)
    
    # 4. 返回结果：有匹配返回起始索引，无匹配返回-1
    return match.start() if match else -1


# =============== GRAPH UTILS ==================

# 建立邻接表
# 格式： {v1:[(e12, v2)], v2:[(e23, v3), (e25, v5)}
def build_adj(graph):
    adj = collections.defaultdict(list)
    for s, r, t in graph["relations"]:
        adj[s].append((r, t))
    #adj = sorted(adj, key = )
    return adj

def choose_root(graph):
    # 优先选择有出边的节点，如果没有，则选字母序第一个
    sources = {s for s, _, _ in graph["relations"]}
    if sources:
        return sorted(list(sources))[0]
    return sorted(graph["entities"].keys())[0]

def build_spanning_tree(graph, text): # 增加 text 参数
    adj = build_adj(graph)
    visited = set()
    tree_edges = set()
    
    def dfs(u):
        visited.add(u)
        # 排序：邻居节点 (v) 按照在文本中出现的先后顺序排序
        neighbors = adj.get(u, [])
        # 自定义排序规则，先按get_text_order(x[1], text)排序再按x[0]排序
        sorted_neighbors = sorted(neighbors, key=lambda x: (get_text_order(text, x[1]), x[0]))
        
        for rel, v in sorted_neighbors:
            if v not in visited:
                tree_edges.add((u, rel, v))
                dfs(v)
    
    # 按照节点在文本中出现的先后顺序尝试访问，处理非连通森林
    all_nodes_sorted = sorted(graph["entities"].keys(), key=lambda n: get_text_order(text, n))
    for n in all_nodes_sorted:
        if n not in visited:
            dfs(n)
            
    return tree_edges



def serialize_graph(graph, text): # 增加 text 参数
    print(text)
    # 建立邻接表
    adj = build_adj(graph)
    nodes = graph["entities"]

    body_parts = []
    # 核心修改：ROOT 下的多个顶级节点按文本序排列
    all_nodes_sorted = sorted(nodes.keys(), key=lambda n: get_text_order(text, n))
    #print(all_nodes_sorted)
    for mention in all_nodes_sorted:
        body_parts.append(f"[{mention}:{nodes[mention]}")
        #print(f"{mention}:{adj[mention]}")
        edges_sorted = sorted(adj[mention], key = lambda x: get_text_order(text, x[1]))
        #print(f"{mention}:{edges_sorted}")
        #print("\n")
        for edge in edges_sorted:
            body_parts.append(f"[{edge[0]}:{edge[1]}]")
        body_parts.append("]")

    return f"[{''.join(body_parts)}]"




# =============== DESERIALIZATION（SEL 新格式） ==================

import re

# \s 代表任意空白符（空格、制表符、换行等），[^...] 是「非匹配」，+ 表示「至少一个」
TOKEN_RE_SEL = re.compile(r'\[|\]|[^\[\]]+')

class Parser_sel:
    """
    解析 SEL 新格式：
      [ROOT [A:TYPEA [E1:B] [E2:C]] [B:TYPEB [E3:C]] [C:TYPEC]]
    """

    def __init__(self, s):
        self.tokens = TOKEN_RE_SEL.findall(s or "")
        self.i = 0
        self.nodes = {}
        self.edges = []

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def next(self):
        t = self.peek()
        # 安全递增：确保在文件末尾时不会越界
        if t is not None:
            self.i += 1
        return t

    def _parse_entity(self):
        """
        已经消耗了实体块起始的 '['，当前 token 形如 'mention:TYPE'，
        之后是若干个关系块，每个为 '[REL:TAIL]'，最后以 ']' 结束。
        返回 True 表示解析成功，返回 False 表示遇到格式错误。
        """
        mt = self.next()
        #print(f"Debug for mt : {mt}")
        # 格式错误判断：避免原本的 NameError 和 ValueError
        if not mt or ":" not in mt:
            return False
        parts = mt.rsplit(":", 1)
        if len(parts) != 2:
            return False
        mention, typ = parts[0].strip(), parts[1].strip()
        self.nodes[mention] = typ

        while self.peek() and self.peek() != "]":
            if self.peek() == "[":
                # 关系块：[REL:TAIL]
                self.next()           # 消耗 '['
                rt = self.next()
                
                # 校验关系 token 是否合法
                if not rt or ":" not in rt:
                    return False
                
                parts = rt.split(":", 1)
                if len(parts) != 2:
                    return
                rel, tail =parts[0].strip(), parts[1].strip()
                edge = [mention, rel, tail]
                if edge not in self.edges:
                    self.edges.append(edge)
                if self.peek() == "]":
                    self.next()
            # 容错：跳过意外 token
            else: self.next()
            
        if self.peek() == "]":
            self.next()

    def parse(self):
        try:
            print("22222222222")
            if self.peek() == "[":
                self.next()
            # 解析 ROOT 内部的若干实体块，直到遇到对应的 ']'
            while self.peek() and self.peek() != "]":
                #print(self.peek())
                if self.peek() == "[":
                    self.next()  # 消耗实体块起始 '['
                    # 尝试解析实体，如果不规范则安全跳过，避免死循环
                    self._parse_entity()
                    '''if not self._parse_entity():
                        # 核心修复：更新指针跳过当前出错的实体块，直到遇到右括号
                        while self.peek() is not None and self.peek() != "]":
                            self.next()
                        if self.peek() == "]":
                            self.next() # 消耗掉该错误实体的右括号'''
                # 其他 token（例如多余空白）直接跳过
                else:self.next()

            return {"entities": self.nodes, "relations": list(self.edges)}
            
        except Exception:
            # 终极兜底：万一发生任何预料之外的严重错误（不 raise，按要求返回空结果）
            return {"entities": {}, "relations": []}


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


# =============== DEMO ==================
if __name__ == "__main__":

    '''args = sys.argv
    if len(args) != 3:
        print("Usage: python build_graph.py <dataset> <split>")
        sys.exit(1)

    dataset = args[1]
    split = args[2]'''

    from tqdm import tqdm
    datasets = ["ace2005"]
    splits = ["train", "dev", "test"]

    for dataset in datasets:
        for split in splits:
            datalist = read_jsonl(f"data_raw/{dataset}/{split}_graph_mapped.jsonl")
            datalist_new = list()
            for i, data in tqdm(enumerate(datalist)):
                print(f"Processing {i}th data...")
                if len(data['sentences']) < 1 or len(data['entities']) < 1:
                    seq = "[]"
                else:
                    text = data['sentences']
                    G = {"entities": data['entities'], "relations": data['relations']}
                    print(f"text:{text}")
                    print(f"nodes:{data['entities']}")
                    print(f"edges:{data['relations']}")
                    seq = serialize_graph(G, text)
                    print("Serialized:\n", seq)
                    #print("Token count:", count_tokens(seq))
                    G2 = Parser_sel(seq).parse()
                    print(f"G2:{G2}")
                    if_match = verify(G, G2)
                    if not if_match:
                        print("Not match!!!!")
                        sys.exit(0)
                    print("--------------------------------")
                data_new = copy.deepcopy(data)
                data_new["serialized"] = seq
                datalist_new.append(data_new)
            write_jsonl_w(f"data_raw/{dataset}/{split}_graph_serialized_sel.jsonl", datalist_new)

    '''text = "<entity_span_1> <entity_span_2> <entity_span_3> <entity_span_4> <entity_span_5> ."

    G = {
    "entities": {
        "<entity_span_1>": "<Entity_Type_1>",
        "<entity_span_2>": "<Entity_Type_2>",
        "<entity_span_3>": "<Entity_Type_3>",
        "<entity_span_4>": "<Entity_Type_4>",
        "<entity_span_5>": "<Entity_Type_5>",
    },
    "relations": [
        ["<entity_span_2>", "<Relation_Type_1>", "<entity_span_3>"],
        ["<entity_span_2>", "<Relation_Type_2>", "<entity_span_5>"],
        ["<entity_span_4>", "<Relation_Type_2>", "<entity_span_3>"],
    ]
    }

    seq = serialize_graph(G, text)
    print("Serialized:\n", seq)

    G2 = Parser_sel(seq).parse()
    print("Recovered graph:", G2)

    # 执行验证
    is_perfect = verify(G, G2)
    if is_perfect:
        print("SUCCESS: The graph was recovered perfectly!")
    else:
        print("FAILURE: There are discrepancies between the graphs.") '''