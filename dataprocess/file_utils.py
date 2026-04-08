import json
from tqdm import tqdm

def read_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    datalist = []
    for i, line in enumerate(lines):
        # print(f"{i + 1}:")
        datalist.append(json.loads(line.strip()))
    return datalist
def write_jsonl_w(path, datalist):
    with open(path, 'w', encoding='utf-8') as f:
        for data in datalist:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
def write_jsonl_a(data, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        datalist = json.load(f)
    return datalist
def write_json(path, datalist):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(datalist, f, indent=2, ensure_ascii=False)
def json2jsonl(in_path, out_path):
    write_jsonl_w(out_path, read_json(in_path))
def jsonl2json(in_path, out_path):
    write_json(out_path, read_jsonl(in_path), )

def read_txt_formatted(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    #content = content.replace("\n", "\\n").replace("\t", "\\t")
    return content

#jsonl2json("data/scierc/test_graph_new.jsonl", "data/scierc/test_graph_new.json")
#jsonl2json("data/conll04/post_test_llm_answer_naive.jsonl", "data/conll04/post_test_llm_answer_naive.json")
#jsonl2json("data/conll04/test_graph.jsonl", "data/conll04/test_graph.json")

if __name__ == "__main__":
    import sys
    args = sys.argv
    '''if len(args) != 3:
        print("Usage: python graph_dfs.py <dataset> <split>")
        sys.exit(1)
    dataset = args[1]
    split = args[2]'''

    #datasets = ["conll04", "scierc", "ace2005"]
    datasets = ["scierc"]
    splits = ["train", "dev", "test"]
    #formats = ["dfsjson", "dfs", "sel"]
    #formats = ["dfs"]
    formats = ["json", "jsonspantype"]
    for dataset in tqdm(datasets):
        for split in splits:
            for fmt in formats:
                instruction = read_txt_formatted(f"data/{dataset}/prompt_{fmt}.txt")
                if fmt == "json":
                    samplelist = read_jsonl(f"data_raw/{dataset}/{split}_graph_mapped.jsonl")
                else:
                    samplelist = read_jsonl(f"data_raw/{dataset}/{split}_graph_serialized_{fmt}.jsonl")
                samplelist_new = list() 
                for sample in tqdm(samplelist):
                    #print(sample)
                    if fmt == "json":
                        answer = {"entities": sample["entities"], "relations": sample["relations"]}
                    elif fmt in ["jsontype", "jsonspantype", "dfsjson"]:
                        answer = sample["serialized"]
                    sample_new = {
                    "instruction": instruction,
                    "input": sample["sentences"],
                    "output": json.dumps(answer, ensure_ascii=False)
                    }
                    samplelist_new.append(sample_new)

                import os
                os.makedirs(f"data/{dataset}", exist_ok=True)
                write_json(f"data/{dataset}/{fmt}_{split}.json",samplelist_new)