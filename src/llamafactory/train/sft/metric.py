# Copyright 2025 HuggingFace Inc., THUDM, and the LlamaFactory team.
#
# This code is inspired by the HuggingFace's transformers library and the THUDM's ChatGLM implementation.
# https://github.com/huggingface/transformers/blob/v4.40.0/examples/pytorch/summarization/run_summarization.py
# https://github.com/THUDM/ChatGLM-6B/blob/main/ptuning/main.py
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np
import torch
from transformers.utils import is_nltk_available
from collections import defaultdict

import json

from ...extras.constants import IGNORE_INDEX
from ...extras.misc import numpify
from ...extras.packages import is_jieba_available, is_rouge_available


if TYPE_CHECKING:
    from transformers import EvalPrediction, PreTrainedTokenizer


if is_jieba_available():
    import jieba  # type: ignore


if is_nltk_available():
    from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu  # type: ignore


if is_rouge_available():
    from rouge_chinese import Rouge  # type: ignore


def eval_logit_processor(logits: "torch.Tensor", labels: "torch.Tensor") -> "torch.Tensor":
    r"""Compute the token with the largest likelihood to reduce memory footprint."""
    if isinstance(logits, (list, tuple)):
        if logits[0].dim() == 3:  # (batch_size, seq_len, vocab_size)
            logits = logits[0]
        else:  # moe models have aux loss
            logits = logits[1]

    if logits.dim() != 3:
        raise ValueError("Cannot process the logits.")

    return torch.argmax(logits, dim=-1)


# 1. 导入 dataclass（让类自动生成构造方法，更简洁）
@dataclass
class ComputeAccuracy:
    r"""Compute accuracy and support `batch_eval_metrics`."""
     # ------------------------------
    # 核心：调用类时自动执行（评估入口）
    # 输入：模型预测结果 + 标签
    # 输出：平均准确率
    # ------------------------------
    def _dump(self) -> Optional[dict[str, float]]:
        result = None
        if hasattr(self, "score_dict"):
            result = {k: float(np.mean(v)) for k, v in self.score_dict.items()}

        self.score_dict = {"accuracy": []}
        return result

     # ------------------------------
    # dataclass 专用：初始化后自动执行
    # ------------------------------
    def __post_init__(self):
        self._dump()

     # ------------------------------
    # 核心：调用类时自动执行（评估入口）
    # 输入：模型预测结果 + 标签
    # 输出：平均准确率
    # ------------------------------
    def __call__(self, eval_preds: "EvalPrediction", compute_result: bool = True) -> Optional[dict[str, float]]:
        preds, labels = numpify(eval_preds.predictions), numpify(eval_preds.label_ids)
        for i in range(len(preds)):
            pred, label = preds[i, :-1], labels[i, 1:]
            label_mask = label != IGNORE_INDEX
            self.score_dict["accuracy"].append(np.mean(pred[label_mask] == label[label_mask]))

        if compute_result:
            return self._dump()


@dataclass
class ComputeSimilarity:
    r"""Compute text similarity scores and support `batch_eval_metrics`.

    Wraps the tokenizer into metric functions, used in CustomSeq2SeqTrainer.
    """

    tokenizer: "PreTrainedTokenizer"

    def _dump(self) -> Optional[dict[str, float]]:
        result = None
        if hasattr(self, "score_dict"):
            result = {k: float(np.mean(v)) for k, v in self.score_dict.items()}

        self.score_dict = {"rouge-1": [], "rouge-2": [], "rouge-l": [], "bleu-4": []}
        return result

    def __post_init__(self):
        self._dump()

    def __call__(self, eval_preds: "EvalPrediction", compute_result: bool = True) -> Optional[dict[str, float]]:
        preds, labels = numpify(eval_preds.predictions), numpify(eval_preds.label_ids)

        preds = np.where(preds != IGNORE_INDEX, preds, self.tokenizer.pad_token_id)
        labels = np.where(labels != IGNORE_INDEX, labels, self.tokenizer.pad_token_id)

        decoded_preds = self.tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)

        for pred, label in zip(decoded_preds, decoded_labels):
            hypothesis = list(jieba.cut(pred))
            reference = list(jieba.cut(label))

            if len(" ".join(hypothesis).split()) == 0 or len(" ".join(reference).split()) == 0:
                result = {"rouge-1": {"f": 0.0}, "rouge-2": {"f": 0.0}, "rouge-l": {"f": 0.0}}
            else:
                rouge = Rouge()
                scores = rouge.get_scores(" ".join(hypothesis), " ".join(reference))
                result = scores[0]

            for k, v in result.items():
                self.score_dict[k].append(round(v["f"] * 100, 4))

            bleu_score = sentence_bleu([list(label)], list(pred), smoothing_function=SmoothingFunction().method3)
            self.score_dict["bleu-4"].append(round(bleu_score * 100, 4))

        if compute_result:
            return self._dump()


@dataclass
class BaseF1Metric:
    r"""Base class for entity and relation F1 metrics.

    Provides common logic for computing entity and relation F1 scores.
    Subclasses should override the `_parse_output()` method to implement
    format-specific parsing.
    """

    tokenizer: "PreTrainedTokenizer"
    best_relation_f1: float = 0.0

    def _dump(self) -> Optional[dict[str, float]]:
        def cal_metric(tp, fp, fn):
            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0 
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0 
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            return p, r, f1

        ent_metric = cal_metric(self._ent["tp"], self._ent["fp"], self._ent["fn"])
        rel_metric = cal_metric(self._rel["tp"], self._rel["fp"], self._rel["fn"])
        result = {
            "ent_f1": ent_metric[2],
            "rel_f1": rel_metric[2],
            "ent_p": ent_metric[0],
            "ent_r": ent_metric[1],
            "rel_p": rel_metric[0],
            "rel_r": rel_metric[1],
        }
        self._reset()
        return result

    def __post_init__(self):
        self._reset()
        self.SYM_RELS = ["Compare", "Conjunction"]

    def _reset(self):
        self._ent = defaultdict(int)  # keys: tp / fp / fn
        self._rel = defaultdict(int)  # keys: tp / fp / fn      

    def _normalize_sym_rel(self, triple):
        if len(triple) == 5:
            head, head_type, relation, tail, tail_type= triple
            # 如果是对称关系，对头尾实体按字典序重新排序
            if relation in self.SYM_RELS:
                # 保证字典序小的实体在前面，消除方向性
                if head > tail:
                    return (tail, tail_type, relation, head, head_type)
            return triple
        elif len(triple) == 3:
            head, relation, tail = triple
            # 如果是对称关系，对头尾实体按字典序重新排序
            if relation in self.SYM_RELS:
                # 保证字典序小的实体在前面，消除方向性
                if head > tail:
                    return (tail, relation, head)
            return triple     
        return triple               
        

    def _parse_output(self, output_str: str) -> dict:
        raise NotImplementedError("Subclasses must implement _parse_output()")

    def _parse_to_set(self, parsed_ent_rel_dict) -> tuple[set, set]:
        ents = parsed_ent_rel_dict["entities"]
        rels = parsed_ent_rel_dict["relations"]     
        if not isinstance(ents, dict):
            return set(), set()
        ent_set = set()
        for name, typ in ents.items():
            span = name.replace("_", " ")
            ent_set.add((span, typ))

        if not isinstance(rels, list):
            return ent_set, list()
        rel_set = set()
        for rel in rels:
            if not isinstance(rel, list) or len(rel) != 3:
                continue
            head, rel_type, tail = rel[0], rel[1], rel[2]
            head_span = head.replace("_", " ")
            tail_span = tail.replace("_", " ")
            head_type = ents.get(head_span, "UNKNOWN")
            tail_type = ents.get(tail_span, "UNKNOWN")
            rel_ = (head_span, head_type, rel_type, tail_span, tail_type)
            norm_rel_ = self._normalize_sym_rel(rel_)
            # rel_set.add(rel_)
            rel_set.add(norm_rel_)
        return ent_set, rel_set

    def __call__(self, eval_preds: "EvalPrediction", compute_result: bool = True) -> Optional[dict[str, float]]:
        print("DEBUG: Metric called")
        preds, labels = numpify(eval_preds.predictions), numpify(eval_preds.label_ids)

        preds = np.where(preds != IGNORE_INDEX, preds, self.tokenizer.pad_token_id)
        labels = np.where(labels != IGNORE_INDEX, labels, self.tokenizer.pad_token_id)

        decoded_preds = self.tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)

        for pred_str, label_str in zip(decoded_preds, decoded_labels):
            pred_result = self._parse_output(pred_str)
            label_result = self._parse_output(label_str)

            pred_ents, pred_rels = self._parse_to_set(pred_result)
            label_ents, label_rels = self._parse_to_set(label_result)

            self._ent["tp"] += len(pred_ents & label_ents)
            self._ent["fp"] += len(pred_ents - label_ents)
            self._ent["fn"] += len(label_ents - pred_ents)
            self._rel["tp"] += len(pred_rels & label_rels)
            self._rel["fp"] += len(pred_rels - label_rels)
            self._rel["fn"] += len(label_rels - pred_rels)

        if compute_result:
            return self._dump()


@dataclass
class JsonNaiveF1Metric(BaseF1Metric):
    r"""Compute entity and relation F1 metrics for JSON-formatted outputs.

    This metric class is designed for tasks where the model outputs
    entity and relation extraction results in standard JSON format:
    {"entities": {...}, "relations": [...]}

    It uses JsonParser for parsing.
    """

    def _parse_output(self, output_str: str) -> dict:
        from .format_parser import JsonNaiveParser

        try:
            parser = JsonNaiveParser(output_str)
            return parser.parse()
        except Exception as e:
            return {"entities": {}, "relations": []}

@dataclass
class JsonTypeF1Metric(BaseF1Metric):
    r"""Compute entity and relation F1 metrics for JSON-formatted outputs.

    This metric class is designed for tasks where the model outputs
    entity and relation extraction results in standard JSON format:
    {"entities": {...}, "relations": [...]}

    It uses JsonParser for parsing.
    """

    def _parse_output(self, output_str: str) -> dict:
        from .format_parser import JsonTypeParser

        try:
            parser = JsonTypeParser(output_str)
            return parser.parse()
        except Exception as e:
            return {"entities": {}, "relations": []}

@dataclass
class JsonSpanTypeF1Metric(BaseF1Metric):
    r"""Compute entity and relation F1 metrics for JSON-formatted outputs.

    This metric class is designed for tasks where the model outputs
    entity and relation extraction results in standard JSON format:
    {"entities": {...}, "relations": [...]}

    It uses JsonParser for parsing.
    """

    def _parse_output(self, output_str: str) -> dict:
        from .format_parser import JsonSpanTypeParser

        try:
            parser = JsonSpanTypeParser(output_str)
            return parser.parse()
        except Exception as e:
            return {"entities": {}, "relations": []}

@dataclass
class SelF1Metric(BaseF1Metric):
    r"""Compute entity and relation F1 metrics for SEL formatted outputs.

    This metric class is designed for tasks where the model outputs
    entity and relation extraction results in SEL format:
    [ROOT [mention:TYPE [relation:tail]...]...]

    It uses SelParser for parsing.
    """

    def _parse_output(self, output_str: str) -> dict:
        from .format_parser import SelParser

        try:
            parser = SelParser(output_str)
            return parser.parse()
        except Exception as e:
            return {"entities": {}, "relations": []}


@dataclass
class DfsJsonF1Metric(BaseF1Metric):
    r"""Compute entity and relation F1 metrics for DFS-JSON formatted outputs.

    This metric class is designed for tasks where the model outputs
    entity and relation extraction results in DFS-JSON format:
    [{"span": "...", "type": "...", "targets": [...]}, ...]

    It uses DfsjsonParser for parsing.
    """

    def _parse_output(self, output_str: str) -> dict:
        from .format_parser import DfsjsonParser

        try:
            parser = DfsjsonParser(output_str)
            return parser.parse()
        except Exception as e:
            return {"entities": {}, "relations": []}


@dataclass
class DfsF1Metric(BaseF1Metric):
    r"""Compute entity and relation F1 metrics for DFS formatted outputs.

    This metric class is designed for tasks where the model outputs
    entity and relation extraction results in DFS format:
    [ROOT [ID:TYPE [relation [child_ID:TYPE]]]...]

    It uses DfsParser for parsing.
    """

    def _parse_output(self, output_str: str) -> dict:
        from .format_parser_copy import DfsParser

        try:
            parser = DfsParser(output_str)
            return parser.parse()
        except Exception as e:
            return {"entities": {}, "relations": []}

if __name__ == "__main__":
    print("hello")