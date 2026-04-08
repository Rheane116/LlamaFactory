import json
from tqdm import tqdm
from file_utils import *

import sys
args = sys.argv
if len(args) != 3:
    print("Usage: python build_graph.py <dataset> <split>")
    sys.exit(1)
dataset = args[1]
split = args[2]

def transform_doc_to_sentences(data):
    """
    将文档级数据转换为句子级数据
    
    参数:
        data: 包含文档数据的字典，包含sentences, ner, relations, clusters, doc_key等字段
    
    返回:
        sentences_data: 转换后的句子级数据列表
    """
    sentences_data = []
    
    # 获取文档信息
    doc_key = data.get("doc_key", "")
    sentences = data.get("sentences", [])
    ner = data.get("ner", [])
    relations = data.get("relations", [])
    clusters = data.get("clusters", [])
    
    # 用于记录累计的token偏移量
    token_offset = 0
    
    # 遍历每个句子
    for sent_idx, sent_tokens in enumerate(sentences):
        # 创建新的句子数据
        sent_data = {
            "doc_key": doc_key,
            "sent_idx": sent_idx,
            "sentences": sent_tokens,  # 注意：这里包装成列表以保持格式一致
            "ner": [],
            "relations": [],
            "clusters": clusters if sent_idx == 0 else [],  # 通常clusters在文档级才有意义
            "original_sent_idx": sent_idx
        }
        
        # 获取当前句子的NER标注
        if sent_idx < len(ner):
            current_ner = ner[sent_idx]
            
            # 处理当前句子的NER
            for ner_item in current_ner:
                if len(ner_item) >= 3:
                    # 调整偏移量：减去累计的token偏移量
                    start, end, label = ner_item[:3]
                    new_start = start - token_offset
                    new_end = end - token_offset
                    
                    # 确保偏移量在当前句子范围内
                    if 0 <= new_start <= new_end < len(sent_tokens):
                        # 获取实体的mention文本
                        mention_tokens = sent_tokens[new_start:new_end+1]
                        mention_text = " ".join(mention_tokens)
                        
                        # 创建新的NER条目，包含mention
                        new_ner_item = [new_start, new_end, label, mention_text]
                        
                        # 如果有额外的信息（如实体ID等），保留
                        if len(ner_item) > 3:
                            new_ner_item.extend(ner_item[3:])
                        
                        sent_data["ner"].append(new_ner_item)
        
        # 获取当前句子的关系标注
        if sent_idx < len(relations):
            current_relations = relations[sent_idx]
            
            # 处理当前句子的关系
            for rel_item in current_relations:
                if len(rel_item) >= 5:
                    # 提取关系信息
                    subj_start, subj_end, obj_start, obj_end, rel_type = rel_item[:5]
                    
                    # 调整偏移量
                    new_subj_start = subj_start - token_offset
                    new_subj_end = subj_end - token_offset
                    new_obj_start = obj_start - token_offset
                    new_obj_end = obj_end - token_offset
                    
                    # 确保关系实体都在当前句子范围内
                    if (0 <= new_subj_start <= new_subj_end < len(sent_tokens) and 
                        0 <= new_obj_start <= new_obj_end < len(sent_tokens)):
                        
                        # 获取主语和宾语的mention文本
                        subj_tokens = sent_tokens[new_subj_start:new_subj_end+1]
                        obj_tokens = sent_tokens[new_obj_start:new_obj_end+1]
                        subj_text = " ".join(subj_tokens)
                        obj_text = " ".join(obj_tokens)
                        
                        # 创建新的关系条目，包含mention文本
                        new_rel_item = [
                            new_subj_start, new_subj_end, 
                            new_obj_start, new_obj_end, 
                            rel_type, 
                            subj_text, obj_text
                        ]
                        
                        # 如果有额外的信息，保留
                        if len(rel_item) > 5:
                            new_rel_item.extend(rel_item[5:])
                        
                        sent_data["relations"].append(new_rel_item)
        
        sent_data["ner"] = sorted(sent_data["ner"], key = lambda x: (x[0], x[1]))
        sent_data["relations"] = sorted(sent_data["relations"], key = lambda x: (x[0], x[1], x[2], x[3]))
        # 添加到结果列表
        sentences_data.append(sent_data)
        
        # 更新token偏移量（当前句子的token数量）
        token_offset += len(sent_tokens)
    
    return sentences_data




output_list = list()
sample_list = list()
with open(f"./data_raw/{dataset}/{split}.json", "r") as f:
    for line in tqdm(list(map(json.loads, f.readlines()))):
        assert len(line["sentences"]) == len(line['ner'])
        assert len(line["sentences"]) == len(line['relations'])
        sample_list += transform_doc_to_sentences(line)
write_jsonl_w(f'./data_raw/{dataset}/{split}_new.jsonl', sample_list)
           