from file_utils import *
import sys

'''args = sys.argv
if len(args) != 3:
    print("Usage: python build_graph.py <dataset> <run_time>")
    sys.exit(1)
dataset = args[1]
run_time = args[2]'''

list1 = read_json("/data/wengxiaolong/zhouyuanyun/LlamaFactory/saves/Qwen2.5-7B/lora/sft-conll04-dfsjson-wofmt/output-2000/parsed_generated_predictions.jsonl")

list2 = read_json("/data/wengxiaolong/zhouyuanyun/LlamaFactory/saves/Qwen2.5-7B/lora/sft-conll04-dfs-wofmt/output-2000/parsed_generated_predictions.jsonl")

less_list = list()
for i, (s1, s2) in enumerate(zip(list1, list2)):
  if s1["rel_f1"] < s2["rel_f1"]:
    less_list.append(i + 1)
print(less_list)
print(len(less_list))

'''rel_num_dfs = sum([len(sample["relations"]) * sample["prec_rel"] for sample in dfs_list])
rel_num_sel = sum([len(sample["relations"]) * sample["prec_rel"] for sample in sel_list])
rel_num_naive = sum([len(sample["relations"]) * sample["prec_rel"] for sample in naive_list])
rel_num_dfsjson = sum([len(sample["relations"]) * sample["prec_rel"] for sample in dfsjson_list])'''
'''rel_num_dfs = sum([len(sample["relations"]) for sample in dfs_list])
rel_num_sel = sum([len(sample["relations"])  for sample in sel_list])
rel_num_naive = sum([len(sample["relations"]) for sample in naive_list])
rel_num_dfsjson = sum([len(sample["relations"])  for sample in dfsjson_list])

rel_num_gold = sum([len(sample["relations"]) for sample in gold_list])

length = 0
for sample in gold_list:
  if len(sample["relations"]) > 0:
    length += 1

print(f"naive:{rel_num_naive / length}")
print(f"dfsjson:{rel_num_dfsjson / length}")
print(f"dfs:{rel_num_dfs / length}")
print(f"sel:{rel_num_sel / length}")

print(f"gold:{rel_num_gold / length}")'''

