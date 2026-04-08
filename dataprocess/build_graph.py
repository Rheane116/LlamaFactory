#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 ACE2005 句子级数据 test_new.json 构造图数据 test_graph.json。

输入: data_raw/ACE2005/test_new.json
  每行一个 JSON 对象，示例:
  {
    "doc_id": "...",
    "sent_id": 0,
    "sentences": ["...", "...", ...],
    "ner": [[start, end, "PER"], ...],
    "relations": [[h_start, h_end, t_start, t_end, "ORG-AFF"], ...]
  }

输出: data_raw/ACE2005/test_graph.json
  在原字段基础上增加:
  - "entities": { entity_name: {"type": ner_label}, ... }
  - "relations": [[head_entity_name, relation_label, tail_entity_name], ...]
"""

import json
from pathlib import Path
from file_utils import *

import sys
args = sys.argv
if len(args) != 3:
    print("Usage: python build_graph.py <dataset> <split>")
    sys.exit(1)
dataset = args[1]
split = args[2]
# print(f"args:{args}")
# 假设脚本放在 mywork 根目录下
INPUT_PATH = Path(f"data_raw/{dataset}/{split}_new.jsonl")
OUTPUT_PATH = Path(f"data_raw/{dataset}/{split}_graph.jsonl")

import re
def get_text_order(main_str, sub_str):
    """ 在文本中定位实体起始索引，用于排序 """
    if not sub_str: return -1
    # 按照原文件逻辑，精确匹配单词边界
    escaped_sub = re.escape(sub_str)
    pattern = re.compile(r'(?<!\w)' + escaped_sub + r'(?!\w)')
    match = pattern.search(main_str)
    return match.start() if match else -1

def build_nodes_and_edges(example):
    """
    从一个句子级样本中，构造 nodes 与 edges。
    """
    tokens = example.get("sentences", [])
    ner = example.get("ner", []) or []
    #ner = ner[0]
    relations = example.get("relations", []) or []
    #relations = relations[0]

    # 1. 构造实体节点
    nodes = {}
    span2name = {}  # (start, end) -> entity_name

    for idx, span in enumerate(ner):
        if len(span) < 3:
            continue
        start, end, label = span[0], span[1], span[2]

        # 取实体文本片段
        if not (0 <= start < len(tokens)) or not (0 <= end < len(tokens)) or end < start:
            # 边界异常，跳过
            continue

        print(f"tokens:{tokens}")
        surface_tokens = tokens[start : end + 1]
        print(f"surface_tokens:{surface_tokens}")
        # 用下划线连接，保证与 graph_dfs_w_reverse.py 中的风格一致
        base_name = " ".join(surface_tokens) if surface_tokens else f"ENT_{idx}"

        # 避免同名冲突: 如果已经存在同名且类型不同，则加后缀
        name = base_name
        suffix = 1
        while name in nodes and nodes[name].get("type") != label:
            name = f"{base_name}#{suffix}"
            suffix += 1

        nodes[name] = {"type": label}
        span2name[(start, end)] = name

    # 2. 构造关系边
    edges = []
    edges_existed = []
    for rel in relations:
        if len(rel) < 5:
            continue
        h_start, h_end, t_start, t_end, rel_label = (
            rel[0],
            rel[1],
            rel[2],
            rel[3],
            rel[4],
        )

        head_name = span2name.get((h_start, h_end))
        tail_name = span2name.get((t_start, t_end))

        # 若关系两端实体在 ner 中没有对应节点，则跳过该关系
        if head_name is None or tail_name is None:
            continue

        edge = [head_name, rel_label, tail_name]
        
        if edge not in edges_existed:
            edges.append([head_name, rel_label, tail_name])
            edges_existed.append([head_name, rel_label, tail_name])

    nodes_items = sorted(nodes.items(), key = lambda x : get_text_order(" ".join(tokens), x[0]))
    nodes = {k : v for k, v in nodes_items}
    edges = sorted(edges, key = lambda x: ((get_text_order(" ".join(tokens), x[0])), get_text_order(" ".join(tokens), x[-1])))
    return nodes, edges


def main():
    num_in = 0
    num_out = 0

    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"找不到输入文件: {INPUT_PATH}")

    with INPUT_PATH.open("r", encoding="utf-8") as fin, \
            OUTPUT_PATH.open("w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            num_in += 1
            example = json.loads(line)

            nodes, edges = build_nodes_and_edges(example)

            new_example = dict(example)  # 保留原字段
            new_example["sent_id"] = num_in - 1
            del new_example["ner"]
            del new_example["relations"]
            new_example["sentences"] = " ".join(new_example["sentences"])
            new_example["entities"] = nodes
            new_example["relations"] = edges

            fout.write(json.dumps(new_example, ensure_ascii=False) + "\n")
            num_out += 1

    print(f"转换完成: {num_in} 条输入样本 -> {num_out} 条输出样本")
    print(f"输出文件: {OUTPUT_PATH}")

    jsonl2json(f"data_raw/{dataset}/{split}_graph.jsonl", f"data_raw/{dataset}/{split}_graph.json")


if __name__ == "__main__":
    main()