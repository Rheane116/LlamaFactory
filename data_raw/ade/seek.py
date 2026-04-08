import json
import copy
def read_json(path):
  with open(path, "r", encoding="utf-8") as f:
    datalist = json.load(f)
    return datalist
def write_json(datalist, path):
  with open(path, "w", encoding="utf-8") as f:
    json.dump(datalist, f, indent=4, ensure_ascii=False)

sent2sample = dict()
all_datalist = read_json("./wb_all.json")
for data in all_datalist:
  sent2sample[data["sentence"]] = data

cnt = 1
for split in ["train", "dev", "test"]:
  path = f"{split}.json"
  datalist = read_json(path)
  #new_datalist = list()
  for data in datalist:
    #new_data = copy.deepcopy(data)
    #print(f"{split}:{data['sentence']}")
    sample = sent2sample[data["sentence"]]
    #print(f"2222222{sample}")
    #rellist = list()
    data["entities"] = sample["entities"]
    for rel in data["relations"]:
      #rel = copy.deepcopy(rel)
      head_mention = rel["head"]["name"]
      tail_mention = rel["tail"]["name"]
      for wb_ent in sample["entities"]:
        if " ".join(sample["tokens"][wb_ent["start"] : wb_ent["end"]]) == head_mention:
          #print("3333333333333333")
          #print(f"--------{wb_ent}")
          rel["head"]["type"] = wb_ent["type"]
          rel["head"]["pos"] = [wb_ent["start"], wb_ent["end"]]
        if " ".join(sample["tokens"][wb_ent["start"] : wb_ent["end"]]) == tail_mention:
          #print(wb_ent)
          rel["tail"]["type"] = wb_ent["type"]
          rel["tail"]["pos"] = [wb_ent["start"], wb_ent["end"]]
      #rellist.append(rel)
    #data["relations"] = rellist
  write_json(datalist, f"new_{split}.json")