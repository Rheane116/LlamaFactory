#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统计实体抽取与关系抽取的 P/R/F1。
评估关系时，要求：头实体提及、头实体类型、关系类型、尾实体提及、尾实体类型全部匹配。
"""

import json
from pathlib import Path
import sys
from file_utils import *
import copy


args = sys.argv
if len(args) < 4:
    print("Usage: python evaluate.py <dataset> <mode> <run_time> <eval_mode>")
    sys.exit(1)
    
dataset = args[1]
mode = args[2]
time = args[3]
eval = args[4] if len(args) >= 5 else "strict"

GOLD_PATH = Path(f"data_raw/{dataset}/test_graph.jsonl")
PRED_PATH = Path(f"data_raw/{dataset}/post_results/post_test_llm_answer_{mode}{time}.jsonl")


SYMMETRIC_RELS = ["COMPARE", "CONJUNCTION", "PER-SOC"]
def normalize_triple(triple):
    if len(triple) == 5:
        head, head_type, relation, tail, tail_type= triple
        # 如果是对称关系，对头尾实体按字典序重新排序
        if relation in SYMMETRIC_RELS:
            # 保证字典序小的实体在前面，消除方向性
            if head > tail:
                return (tail, tail_type, relation, head, head_type)
        return triple
    elif len(triple) == 3:
        head, relation, tail = triple
        # 如果是对称关系，对头尾实体按字典序重新排序
        if relation in SYMMETRIC_RELS:
            # 保证字典序小的实体在前面，消除方向性
            if head > tail:
                return (tail, relation, head)
        return triple     
    return triple   

def safe_div(num, den):
    if den == 0:
        return 0.0
    return num / den

# def evaluate(golds, preds, mode="strict"):


def main():
    # 统计实体
    tp_ent = fp_ent = fn_ent = 0
    # 统计关系
    tp_rel = fp_rel = fn_rel = 0

    samplelist_new = list()
    with GOLD_PATH.open("r", encoding="utf-8") as f_gold, \
            PRED_PATH.open("r", encoding="utf-8") as f_pred:

        for i, (line_g, line_p) in enumerate(zip(f_gold, f_pred), start=1):
            
            tp_ent1 = fp_ent1 = fn_ent1 = 0
            tp_rel1 = fp_rel1 = fn_rel1 = 0
            line_g = line_g.strip()
            line_p = line_p.strip()
            if not line_g and not line_p:
                continue

            golds = json.loads(line_g)
            preds = json.loads(line_p)

            sample = copy.deepcopy(preds)

            doc_id_g = golds.get("doc_id")
            sent_id_g = golds.get("sent_id")
            doc_id_p = preds.get("doc_id")
            sent_id_p = preds.get("sent_id")

            #print(f"\n样本{i}:")
            #print(golds.get("sentences"))
            #print(preds.get("sentences"))
            #assert golds.get("sentences") == preds.get("sentences")

            # ---------- 实体统计 ----------
            gold_nodes = golds.get("entities", {}) or {}
            pred_nodes = preds.get("entities", {}) or {}

            gold_ent_set = set(
                (name.replace("_", " ").lower(), info.get("type"))
                for name, info in gold_nodes.items()
            )
            pred_ent_set = set(
                (name.replace("_", " ").lower(), info.get("type"))
                for name, info in pred_nodes.items()
            )

            tp_ent1 += len(gold_ent_set & pred_ent_set)
            fp_ent1 += len(pred_ent_set - gold_ent_set)
            fn_ent1 += len(gold_ent_set - pred_ent_set)

            # ---------- 关系统计 (核心修改部分) ----------
            gold_edges = golds.get("relations", []) or []
            pred_edges = preds.get("relations", []) or []

            # 定义关系为 (doc_id, sent_id, 头名, 头类型, 关系名, 尾名, 尾类型)
            # 使用 .get("type") 确保即使预测中实体不存在也不会报错
            gold_rel_set = set()
            for h, r, t in gold_edges:
                if eval == "strict":
                    h_type = gold_nodes.get(h, {}).get("type")
                    t_type = gold_nodes.get(t, {}).get("type")
                    gold_rel_set.add(normalize_triple((h.replace("_", " ").lower(), h_type, r, t.replace("_", " ").lower(), t_type)))
                else:
                    gold_rel_set.add(normalize_triple((h.replace("_", " ").lower(), r, t.replace("_", " ").lower())))

            pred_rel_set = set()
            for h, r, t in pred_edges:
                if eval == "strict":
                    h_type = pred_nodes.get(h, {}).get("type")
                    t_type = pred_nodes.get(t, {}).get("type")
                    pred_rel_set.add(normalize_triple((h.replace("_", " ").lower(), h_type, r, t.replace("_", " ").lower(), t_type)))
                else:
                    pred_rel_set.add(normalize_triple((h.replace("_", " ").lower(), r, t.replace("_", " ").lower())))

            
            tp_rel1 += len(gold_rel_set & pred_rel_set)
            fp_rel1 += len(pred_rel_set - gold_rel_set)
            fn_rel1 += len(gold_rel_set - pred_rel_set)

            # ---------- 指标计算 ----------
            prec_ent1 = safe_div(tp_ent1, tp_ent1 + fp_ent1)
            rec_ent1 = safe_div(tp_ent1, tp_ent1 + fn_ent1)
            f1_ent1 = safe_div(2 * prec_ent1 * rec_ent1, prec_ent1 + rec_ent1)

            prec_rel1 = safe_div(tp_rel1, tp_rel1 + fp_rel1)
            rec_rel1 = safe_div(tp_rel1, tp_rel1 + fn_rel1)
            f1_rel1 = safe_div(2 * prec_rel1 * rec_rel1, prec_rel1 + rec_rel1)

            if eval == "strict":
                sample["f1_ent"] = f1_ent1
                sample["prec_ent"] = prec_ent1
                sample["recall_ent"] = rec_ent1
                sample["f1_rel"] = f1_rel1
                sample["prec_rel"] = prec_rel1
                sample["recall_rel"] = rec_rel1
            samplelist_new.append(sample)

            tp_ent += tp_ent1
            fp_ent += fp_ent1
            fn_ent += fn_ent1

            tp_rel += tp_rel1
            fp_rel += fp_rel1
            fn_rel += fn_rel1

    # ---------- 指标计算 ----------
    prec_ent = safe_div(tp_ent, tp_ent + fp_ent)
    rec_ent = safe_div(tp_ent, tp_ent + fn_ent)
    f1_ent = safe_div(2 * prec_ent * rec_ent, prec_ent + rec_ent)

    prec_rel = safe_div(tp_rel, tp_rel + fp_rel)
    rec_rel = safe_div(tp_rel, tp_rel + fn_rel)
    f1_rel = safe_div(2 * prec_rel * rec_rel, prec_rel + rec_rel)

    print(f"===== 实体抽取 {mode} =====")
    print(f"TP={tp_ent}, FP={fp_ent}, FN={fn_ent}")
    print(f"Precision: {prec_ent:.4f} | Recall: {rec_ent:.4f} | F1: {f1_ent:.4f}")

    print(f"\n===== 关系抽取 {mode} ({eval}) =====")
    print(f"TP={tp_rel}, FP={fp_rel}, FN={fn_rel}")
    print(f"Precision: {prec_rel:.4f} | Recall: {rec_rel:.4f} | F1: {f1_rel:.4f}")

    write_json(f"data_raw/{dataset}/post_results/post_test_llm_answer_{mode}{time}.json", samplelist_new)

if __name__ == "__main__":
    main()