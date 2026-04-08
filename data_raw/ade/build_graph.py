import json
from tqdm import tqdm

def read_json(path):
  with open(path, "r", encoding="utf-8") as f:
    datalist = json.load(f)
  return datalist
def write_jsonl_w(path, datalist):
  with open(path, "w", encoding="utf-8") as f:
    for data in datalist:
      f.write(json.dumps(data) + "\n")
  return

path = "/data/wengxiaolong/zhouyuanyun/LlamaFactory/data_raw/ade/new_dev.json"
datalist = read_json(path)
new_datalist = list()
for i, data in tqdm(enumerate(datalist)):
  new_data = dict()
  new_data["sent_id"] = i
  new_data["sentences"] = data["sentence"]
  new_data["entities"] = dict()
  new_data["relations"] = list()
  for relation in data["relations"]:
    head = relation["head"]
    tail = relation["tail"]
    new_data["entities"][head["name"]] = {"type":head["type"]}
    new_data["entities"][tail["name"]] = {"type":tail["type"]}
    new_data["relations"].append([head["name"], relation["type"], tail["name"]])

    new_datalist.append(new_data)
write_jsonl_w("data_raw/ade/dev_graph.jsonl", new_datalist)