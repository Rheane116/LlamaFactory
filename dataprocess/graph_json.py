import re
import json
from collections import defaultdict
from file_utils import *
import copy
import sys


def get_text_order(main_str, sub_str):
    """ 在文本中定位实体起始索引，用于排序 """
    if not sub_str: return -1
    # 按照原文件逻辑，精确匹配单词边界
    escaped_sub = re.escape(sub_str)
    pattern = re.compile(r'(?<!\w)' + escaped_sub + r'(?!\w)')
    match = pattern.search(main_str)
    return match.start() if match else -1

def reorder(json_dict, text, version):
  entities_tmp = json_dict["entities"]
  relations_tmp = json_dict["relations"]
  if version == "type":
    nodes_items = sorted(entities_tmp.items(), key = lambda x : get_text_order(text, x[0]))
    json_dict["entities"] = {k : v for k, v in nodes_items}
  elif version == "span-type":
    nodes_items = sorted(entities_tmp, key = lambda x : get_text_order(text, x["span"]))
    json_dict["entities"] = nodes_items
  json_dict["relations"] = sorted(relations_tmp, key = lambda x: ((get_text_order(text, x[0])), get_text_order(text, x[-1])))  
  return json_dict

def serialize_type(entities, relations, text):
  json_dict = {"entities":dict(), "relations": relations}
  for span, typ in entities.items():
    json_dict["entities"][span] = {"type": typ}
  json_dict = reorder(json_dict, text, "type")
  return json_dict

def serialize_span_type(entities, relations, text):
  assert type(entities) == dict
  json_dict = {"entities":list(), "relations": relations}
  for span, typ in entities.items():
    json_dict["entities"].append({"span": span, "type": typ})
  json_dict = reorder(json_dict, text, "span-type")
  return json_dict


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
    versions = ["json-type", "json-span-type"]

    for dataset in datasets:
        for split in splits:
            datalist = read_jsonl(f"data_raw/{dataset}/{split}_graph_mapped.jsonl")
            datalist_new_type = list()
            datalist_new_span_type = list()

            for i, data in tqdm(enumerate(datalist)):
                print(f"Processing {i + 1}th data...")
                if len(data['entities']) < 1:
                    serialized_list = "[]"
                else:       
                    text = data['sentences']
                    G = {"entities": data['entities'], "relations": data['relations']}

                    # 序列化
                    # 执行序列化
                    serialized_type = serialize_type(G["entities"], G["relations"], text)
                    serialized_span_type = serialize_span_type(G["entities"], G["relations"], text)

                    #print("--- 序列化结果 (JSON List) ---")
                    #print(json.dumps(serialized_list, indent=2, ensure_ascii=False))

                data_new_type = copy.deepcopy(data)
                data_new_span_type = copy.deepcopy(data)
                #data_new["serialized"] = json.dumps(serialized_list, ensure_ascii=False)
                data_new_type["serialized"] = serialized_type
                data_new_span_type["serialized"] = serialized_span_type
                datalist_new_type.append(data_new_type)
                datalist_new_span_type.append(data_new_span_type)
            write_jsonl_w(f"data_raw/{dataset}/{split}_graph_serialized_json_type.jsonl", datalist_new_type)
            write_jsonl_w(f"data_raw/{dataset}/{split}_graph_serialized_json_spantype.jsonl", datalist_new_span_type)


    '''text = "Holding a framed picture of her son , serving with the Army 's 3rd Infantry Division in Iraq , she said she did n't know whether he was dead or alive ."

    G = {
       "entities": {"3rd Infantry Division": {"type": "ORG"}, "Army": {"type": "ORG"}, "Iraq": {"type": "GPE"}, "he": {"type": "PER"}, "her": {"type": "PER"}, "she": {"type": "PER"}, "son": {"type": "PER"}}, "relations": [["3rd Infantry Division", "GEN-AFF", "Iraq"], ["3rd Infantry Division", "PART-WHOLE", "Army"], ["her", "PER-SOC", "son"], ["son", "ORG-AFF", "3rd Infantry Division"], ["son", "PHYS", "Iraq"]]}

    # 执行序列化
    #serialized_list = serialize(G["entities"], G["relations"], text)
    
    #print("--- 序列化结果 (JSON List) ---")
    serialized_list = "[{\"span\": \"propylthiouracil\", \"type\": \"Drug\"}, {\"span\": \"PTU\", \"type\": \"Drug\", \"relation\": \"adverse_effect\", \"ref\": \"propylthiouracil\"}, {\"span\": \"Acute hepatic failure\", \"type\": \"Adverse-Effect\", \"targets\": [{\"relation\": \"adverse_effect\", \"ref\": \"propylthiouracil\"}, {\"relation\": \"adverse_effect\", \"ref\": \"PTU\"}]}]"
    #print(json.dumps(serialized_list, indent=2, ensure_ascii=False))
    serialized_list = json.loads(serialized_list)
    # 执行解析
    restored_G = deserialize_list_format(serialized_list)
    print("\n--- 还原后的数据结构 ---")
    print(json.dumps(restored_G, indent=2, ensure_ascii=False))
    #print(f"Matched:{verify(G, restored_G)}")'''