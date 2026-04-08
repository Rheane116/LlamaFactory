import json
input_path = "train_dev原始.txt"

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
        json.dump(datalist, f, ensure_ascii=False, indent=4)

def match_sublist(the_list, to_match):
    """
    :param the_list: [1, 2, 3, 4, 5, 6, 1, 2, 4, 5]
    :param to_match: [1, 2]
    :return:
        [(0, 1), (6, 7)]
    """
    len_to_match = len(to_match)
    matched_list = list()
    for index in range(len(the_list) - len_to_match + 1):
        if to_match == the_list[index:index + len_to_match]:
            matched_list += [(index, index + len_to_match)]
    return matched_list

def closest_match_sublist(the_list, to_match1, to_match2):
    matched_list1 = match_sublist(the_list, to_match1)
    matched_list2 = match_sublist(the_list, to_match2)
    assert len(matched_list1) > 0
    assert len(matched_list2) > 0
    distance_tuple = list()
    for arg1_match in matched_list1:
        for arg2_match in matched_list2:
            distance = abs(arg1_match[0] - arg2_match[0])
            distance_tuple += [(distance, arg1_match, arg2_match)]
    distance_tuple.sort()
    return distance_tuple

#datalist = read_txt(input_path)

ent_labels = ['情况', '病患', '症状', '治疗', '药物', '用法']

sample_list = {"train":list(), "dev":list(), "test":list()}
trainlist = read_txt("train_dev原始.txt")

for i, line in enumerate(trainlist):
    sample = {"text":line["text"], "entities":list(), "relations":list()}
    mention2entidx = dict()
    cnt = 0

    ent_mention_contained = list()
    rel_mention_contained = list()
    for ent in line['entities']:

        if ent[-2] not in ent_mention_contained:
            ent_mention_contained.append(ent[-2])
            matched_span_list = match_sublist(list(line["text"]), list(ent[-2]))
            start, end = matched_span_list[0][0], matched_span_list[0][1]
            sample["entities"].append({"type":ent[-1], "start": start, "end": end, "mention": ent[-2]})
            mention2entidx[ent[-2]] = cnt
            cnt += 1
        else:
           print(f"训练集样本{i+1}:{line['text']}")
           print(f"实体重复：{ent[-2]}")
           #pass
            
    for rel in line["relations"]:
        
        '''print("------head----------")
        print(sample["tokens"][rel[0][0]: rel[0][1]])
        print(rel[0][-1])'''
        assert line["text"][rel[0][0]: rel[0][1]] == rel[0][-1]
        assert line["text"][rel[-1][0]: rel[-1][1]] == rel[-1][-1]
        if (rel[0][-1], rel[1], rel[-1][-1]) not in rel_mention_contained:
            rel_mention_contained.append((rel[0][-1], rel[1], rel[-1][-1]))
            '''head_matched_list = match_sublist(sample["tokens"], list(rel[0][-1]))
            head_s, head_e = head_matched_list[0][0], head_matched_list[0][1]
            tail_matched_list = match_sublist(sample["tokens"], list(rel[-1][-1]))
            tail_s, tail_e = tail_matched_list[0][0], tail_matched_list[0][1]'''
            sample["relations"].append({"type": rel[1], "head": sample["entities"][mention2entidx[rel[0][-1]]], "tail":sample["entities"][mention2entidx[rel[-1][-1]]]})
        else:
            print(f"训练集样本{i+1}:{line['text']}")
            print(f"关系重复：({rel[0][-1]}, {rel[1]}, {rel[-1][-1]})")
            #pass
            
    sample_list["train"].append(sample)




devlist = read_txt("test.txt")
for j, line in enumerate(devlist):
    #print(line)
    sample = {"text":line["text"], "entities":list(), "relations":list()}
    mention2entidx = dict()
    '''print(f"-------样本{num}---------")
    print(line["text"])
    print(line["relations"])'''
    cnt = 0
    ent_mention_contained = list()
    rel_mention_contained = list()

    # 先将实体加入新样本（不重复），并记录：实体提及到其索引的映射
    for i, rel in enumerate(line['relations']):
        head = rel[0]
        tail = rel[-1]
        #print(f"head:{head}")
        #print(f"tail:{tail}")
        if head[-1] not in ent_mention_contained:   # 若头实体提及没有出现过
            ent_mention_contained.append(head[-1])  # 加入头实体提及列表
            match_list_head = match_sublist(list(line["text"]), list(head[-1]))   # 将头实体边界映射到first
            assert len(match_list_head) > 0
            #head = [match_list_head[0][0], match_list_head[0][1], head[-1]]     # 修改头实体span
            sample["entities"].append({"type":"药物", "start": match_list_head[0][0], "end": match_list_head[0][1], "mention":head[-1]})

            mention2entidx[head[-1]] = cnt
            cnt += 1    # 实体计数加1
        else:
            #print(f"测试集样本{j+1}实体重复：{head[-1]}")
            pass

        if tail[-1] not in ent_mention_contained:   # 若头实体提及没有出现过
            ent_mention_contained.append(tail[-1])  # 加入头实体提及列表
            match_list_tail = match_sublist(list(line["text"]), list(tail[-1]))   # 将尾实体边界映射到first
            assert len(match_list_tail) > 0
            #head = [match_list_head[0][0], match_list_head[0][1], head[-1]]     # 修改头实体span
            sample["entities"].append({"type":"药物", "start": match_list_tail[0][0], "end": match_list_tail[0][1], "mention":tail[-1]})

            mention2entidx[tail[-1]] = cnt
            cnt += 1    # 实体计数加1
        else:
            #print(f"测试集样本{j+1}实体重复：{tail[-1]}")
            pass
            
    # 将关系加入新样本（不重复），利用：实体提及到其索引的映射
    for rel in line["relations"]:
        if (rel[0][-1], rel[1], rel[-1][-1]) not in rel_mention_contained:
            rel_mention_contained.append((rel[0][-1], rel[1], rel[-1][-1]))
            sample["relations"].append({"type": rel[1], "head": sample["entities"][mention2entidx[rel[0][-1]]], "tail":sample["entities"][mention2entidx[rel[-1][-1]]]})
            '''print("--head--")
            print(sample["tokens"][rel[0][0]: rel[0][1]])
            print(rel[0][-1])
            print("--tail--")
            print(sample["tokens"][rel[-1][0]: rel[-1][1]])
            print(rel[-1][-1])'''
            #print(f"span:{rel[-1]}")
            head_s, head_e = sample["entities"][mention2entidx[rel[0][-1]]]["start"], sample["entities"][mention2entidx[rel[0][-1]]]["end"]
            tail_s, tail_e = sample["entities"][mention2entidx[rel[-1][-1]]]["start"], sample["entities"][mention2entidx[rel[-1][-1]]]["end"]
            assert line["text"][head_s: head_e] == rel[0][-1]
            assert line["text"][tail_s: tail_e] == rel[-1][-1]
        else:
            print(f"测试集样本{j+1}:{line['text']}")
            print(f"关系重复：({rel[0][-1]}, {rel[1]}, {rel[-1][-1]})")
    sample_list["dev"].append(sample)

write_json(sample_list, "text2dt_readable.json")