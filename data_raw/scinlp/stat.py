import json

def read_jsonl(path):
  datalist = list()
  with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
      datalist.append(json.loads(line))
  return datalist


folder_path = "/data/wengxiaolong/zhouyuanyun/LlamaFactory/data_raw/scinlp"
import os

splits = ["train", "dev", "test"]
ent_num, rel_num = 0, 0
ent_set = set()
ent_list = list()
rel_set = set()
for split in splits:
  no_empty = 0
  datalist = read_jsonl(os.path.join(folder_path, f"{split}.json"))
  print(f"{split}集数目：{len(datalist)}")
  for data in datalist:
    all_sents = list()
    for sent in data["sentences"]:
      all_sents += sent
    ents_ = data["ner"]
    rels_ = data["relations"]
    for ents in ents_:
      for ent in ents:
        ent_num += 1
        ent_mention = " ".join(all_sents[ent[0]: ent[1] + 1])
        ent_type = ent[-1]
        print((ent_mention, ent_type))
        ent_set.add(ent_mention)
    for rels in rels_:
      for rel in rels:
        rel_num += 1
    #ent_num += len(ents)
  print(f"{split}集非空样本数目：{no_empty}")

print(f"三个集合实体总数(mention,type)：{len(ent_set)}")
print(f"三个集合实体总数(span)：{ent_num}")
print(f"三个集合关系总数(span)：{rel_num}")
'''datalist = read_jsonl(os.path.join(folder_path, f"dev.json"))
for data in datalist:
  sentences = data["sentences"]
  sent_len = len(sentences)
  sent_start_idx = []
  idx = 0
  for sent in sentences:
    sent_start_idx.append(idx)
    idx += len(sent)
  for rel in data["relations"]'''
