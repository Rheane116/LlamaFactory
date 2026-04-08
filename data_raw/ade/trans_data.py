output_path = "./wb_all.json"
import json
def read_json(path):
  with open(path, "r", encoding="utf-8") as f:
    datalist = json.load(f)
    return datalist
def write_json(datalist, path):
  with open(path, "w", encoding="utf-8") as f:
    json.dump(datalist, f, indent=4, ensure_ascii=False)
datalist = read_json("./train_split.json") + read_json("./test_split.json")
for data in datalist:
  data["sentence"] = " ".join(data["tokens"])
write_json(datalist, output_path)