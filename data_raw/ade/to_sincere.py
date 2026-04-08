import json
def read_json(path):
  with open(path, "r", encoding="utf-8") as f:
    datalist = json.load(f)
    return datalist
def write_json(datalist, path):
  with open(path, "w", encoding="utf-8") as f:
    json.dump(datalist, f, indent=4, ensure_ascii=False)

final_dict = {"train":[], "dev":[], "test":[]}
for split in ['train', 'dev', 'test']:
  datalist = read_json(f"new_{split}.json")
  for data in datalist:
    sample = {
      "tokens": data["sentence"].split(" "),
      "entities": [],
      "relations": []
    }
    span2entidx = dict()
    for i, ner in enumerate(data["entities"]):
      entity = {"type": ner["type"], "start": ner["start"], "end": ner["end"]}
      span2entidx[(ner["start"], ner["end"])] = i
      sample["entities"].append(entity)
    for i, rel in enumerate(data["relations"]):
      relation = {"type": rel["type"], "head": span2entidx[(rel["head"]["pos"][0], rel["head"]["pos"][1])], "tail": span2entidx[(rel["tail"]["pos"][0], rel["tail"]["pos"][1])]}
      sample["relations"].append(relation)
    final_dict[split].append(sample)

with open("ade.json", "w", encoding="utf-8") as f:
  json.dump(final_dict, f, indent=4, ensure_ascii=False)