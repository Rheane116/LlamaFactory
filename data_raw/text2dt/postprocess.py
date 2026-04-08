import json


def read_txt(path):
    dict_list = list()
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        #print(line)
        line = line.strip()
        line = line.replace("(", "[")
        line = line.replace(")", "]")
        line = line.replace("'", "\"")
        line = line.replace("'", "\"")
        if not line:
            continue
        dict_list.append(json.loads(line))
    return dict_list

def read_jsonl(path):
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
  datalist = []
  for line in lines:
    datalist.append(json.loads(line.strip()))
  return datalist 

def write_json(datalist, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datalist, f, indent=4, ensure_ascii=False)

gold_list = read_jsonl("train.json")
gold_list_new = list()
for line in gold_list:
    text = line["text"]
    sample = {"text":text, "relations":list()}
    for rel in line["relation"]:
        rel_type = rel["type"]
        head = rel["args"][0]
        tail = rel["args"][1]
        sample["relations"].append([[head["offset"][0], head["offset"][-1] + 1, text[head["offset"][0] : head["offset"][-1] + 1]], rel_type, [tail["offset"][0], tail["offset"][-1] + 1, text[tail["offset"][0] : tail["offset"][-1] + 1]]])
    gold_list_new.append(sample)
write_json(gold_list_new, "test_train.json")

pred_list = read_jsonl("test_preds_record.txt")
sample_list = list()
for i, line in enumerate(pred_list):
    
    text = gold_list[i]["text"]
    #print("\n")
    #print(text)
    sample = {"text":text, "relations":list()}
    for rel in line["relation"]["offset"]:
        #print(rel)
        rel_type = rel[0]
        head_span = (rel[2][0], rel[2][-1] + 1)
        if len(rel[4]) == 0:
            continue
        tail_span = (rel[4][0], rel[4][-1] + 1)
        sample["relations"].append([[head_span[0], head_span[1], text[head_span[0]: head_span[1]]], rel_type, [tail_span[0], tail_span[1], text[tail_span[0]: tail_span[1]]]])
    sample_list.append(sample)
write_json(sample_list, "test_cases_train.json")

pred_num_tot = 0
gold_num_tot = 0
tp_tot = 0
cnt = 0
assert len(gold_list) == len(sample_list)
for (gold, pred) in zip(gold_list_new, sample_list):
    cnt += 1
    assert gold["text"] == pred["text"]
    print(f"样本{cnt}:{gold['text']}")
    pred_num = 0
    gold_num = 0
    tp = 0
    pred_rels = pred["relations"]
    gold_rels = gold["relations"]
    pred_rels_new = list()
    gold_rels_new = list()
    for pred_rel in pred_rels:
        if pred_rel not in pred_rels_new:
            pred_rels_new.append(pred_rel)
    for gold_rel in gold_rels:
        if gold_rel not in gold_rels_new:
            gold_rels_new.append(gold_rel)
    pred_num += len(pred_rels_new)
    gold_num += len(gold_rels_new)
    pred_num_tot += len(pred_rels_new)
    gold_num_tot += len(gold_rels_new)
    for rel in pred_rels_new:
        if rel in gold_rels_new:
            tp += 1
            tp_tot += 1
        else:
            print(f"pred not in gold:{rel}")
    print("\n")
    for rel in gold_rels_new:
        if rel not in pred_rels_new:
            print(f"gold not in pred:{rel}")
    print(f"pred_num:{pred_num}")
    print(f"gold_num:{gold_num}")
    print(f"tp:{tp}")
    if pred_num :
        prec = tp / pred_num
    else:
        prec = -1
    if gold_num:
        rec = tp / gold_num
    else:
        rec = -1
    if prec == -1 or rec == -1 or (prec + rec) == 0:
        f1 = -1
    else:
        f1 = 2 * prec * rec / (prec + rec)
    print(f"prec:{prec}")
    print(f"rec:{rec}")
    print(f"f1:{f1}")

    print("\n")

print("==============Final===============")
print(f"pred_num:{pred_num_tot}")
print(f"gold_num:{gold_num_tot}")
print(f"tp:{tp_tot}")
if pred_num_tot :
    prec_tot = tp_tot / pred_num_tot
else:
    prec_tot = -1
if gold_num_tot:
    rec_tot = tp_tot / gold_num_tot
else:
    rec_tot = -1
if prec_tot == -1 or rec_tot == -1 or (prec_tot + rec_tot) == 0:
    f1_tot = -1
else:
    f1_tot = 2 * prec_tot * rec_tot / (prec_tot + rec_tot)
print(f"prec:{prec_tot}")
print(f"rec:{rec_tot}")
print(f"f1:{f1_tot}")

print("\n")