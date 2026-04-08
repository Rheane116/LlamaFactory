from file_utils import *
from copy import deepcopy
from tqdm import tqdm

datasets = ["conll04", "scierc","ace2005"]
splits = ["train", "dev", "test"]
for dataset in tqdm(datasets):
  mapp = read_json(f"data/{dataset}/schema_map.json")
  for split in tqdm(splits):
    samplelist = read_jsonl(f"data_raw/{dataset}/{split}_graph.jsonl")
    samplelist_new = list()
    for i, sample in tqdm(enumerate(samplelist)):
      sample_new = dict()
      sample_new["sent_id"] = i
      sample_new["sentences"] = sample["sentences"]

      sample_new["entities"] = dict()
      for k, v in sample["entities"].items():
        sample_new["entities"][k] = mapp[v["type"]]

      sample_new["relations"] = list()
      for i, rel in enumerate(sample["relations"]):
         sample_new["relations"].append([rel[0],mapp[rel[1]], rel[-1]])
      samplelist_new.append(sample_new)
    write_jsonl_w(f"data_raw/{dataset}/{split}_graph_mapped.jsonl", samplelist_new)