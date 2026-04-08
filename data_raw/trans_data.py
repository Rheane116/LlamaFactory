import json

def read_jsonl(path):
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
  datalist = []
  for line in lines:
    datalist.append(json.loads(line.strip()))
  return datalist  

final_dict = {"train":[], "dev":[], "test":[]}
for split in ['train', 'dev', 'test']:
  datalist = read_jsonl(f"scierc/inter_{split}.json")
  for data in datalist:
    sample = {
      "tokens": data["sentences"][0],
      "entities": [],
      "relations": []
    }
    span2entidx = dict()
    for i, ner in enumerate(data["ner"]):
      entity = {"type": ner[2], "start": ner[0], "end": ner[1] + 1}
      span2entidx[(ner[0], ner[1])] = i
      sample["entities"].append(entity)
    for i, rel in enumerate(data["relations"]):
      relation = {"type": rel[-3], "head": span2entidx[(rel[0], rel[1])], "tail": span2entidx[(rel[2], rel[3])]}
      sample["relations"].append(relation)
    final_dict[split].append(sample)

with open("scierc/scierc.json", "w", encoding="utf-8") as f:
  json.dump(final_dict, f, indent=4, ensure_ascii=False)