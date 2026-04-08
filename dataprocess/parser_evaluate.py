import json
import re
from file_utils import *
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional


class JsonParser:
    def __init__(self, ans: str):
        self.ans = ans

    def _rm_duplicated_rels(self):
      unique_rels = []
      for r in self.relations:
        if r not in unique_rels:
          unique_rels.append(r)
      self.relations = unique_rels

    def _fix_json(self, s):
      if s.endswith("\"]}]}") or s.endswith("\"]]}}") or s.endswith("\"}]]}"):
          return s[:-4] + "]]}"
      elif s.endswith("\"]}") or s.endswith("\"]]"):
          return  s[:-2] + "]]}" 
      return s   
     
    def parse(self):
        try:
          ans_fixed = self._fix_json(self.ans)
          json_list = json.loads(ans_fixed)
        except Exception as e:
          print(f"Invalid Json Format: {e}")
          return {"entities":{}, "relations":[]}

        self.entities = dict()
        self.relations = list()

        ents_raw = json_list.get("entities", {})
        if type(ents_raw) != dict:
            return {"entities": {}, "relations": []}
        for ent_span, info in ents_raw.items():
            if type(info) != dict:
                continue
            ent_type = info.get("type", "UNKNOWN")
            if type(ent_type) == str:
                self.entities[ent_span] = ent_type

        rels_raw = json_list.get("relations",[])
        if type(rels_raw) != list:
            return {"entities": self.entities, "relations": []}
        for rel in rels_raw:
            if type(rel) != list:
                continue
            if len(rel) != 3:
                continue
            rel_type = rel[1]
            head_span = rel[0]
            tail_span = rel[-1]
            if type(rel_type) == str and type(head_span) == str and type(tail_span) == str:
                self.relations.append([head_span, rel_type, tail_span])

        self._rm_duplicated_rels()
        return {"entities": self.entities, "relations": self.relations}  

class DfsjsonParser:
    def __init__(self, ans: str):
        self.ans = ans
        self.entities = dict()
        self.relations = list()
    
    def _traverse(self, item, parent_span=None):
        #print(item)
        #print(type(item))
        if type(item) != dict:
            return

        node_span = None
        if "span" in item:
            node_span = item["span"]
            if type(node_span) != str:
                return
            try:
                node_type = item["type"]
            except Exception as e:
                node_type = "UNKNOWN"
            if type(node_type) != str:
                node_type = "UNKNOWN"
            if node_span not in self.entities:
                self.entities[node_span] = node_type
        
        if "ref" in item:
            if type(item["ref"]) != str:
                return
            if parent_span and "relation" in item:
                if type(parent_span) != str or type(item["relation"]) != str:
                    return
                self.relations.append([parent_span, item["relation"], item["ref"]])
            if node_span is None:
                return

        if node_span and parent_span and "relation" in item:
            if type(parent_span) != str or type(item["relation"]) != str:
                return
            self.relations.append([parent_span, item["relation"], node_span])
        
        for target in item.get("targets", []):
            self._traverse(target, node_span)

    def _rm_duplicated_rels(self):
      unique_rels = []
      for r in self.relations:
        if r not in unique_rels:
          unique_rels.append(r)
      self.relations = unique_rels
     
    def parse(self):
        try:
          ans_fixed = self._fix_dfsjson(self.ans)
          json_list = json.loads(ans_fixed)
        except Exception as e:
          print(f"Invalid Json Format: {e}")
          return {"entities":{}, "relations":[]}
        
        if not isinstance(json_list, list):
          return {"entities": {}, "relations": []}
        for root_item in json_list:
          self._traverse(root_item)
        self._rm_duplicated_rels()
        return {"entities": self.entities, "relations": self.relations}

    def _fix_dfsjson(self, s):
      s = self._fix_bracket_mismatch(s)
      s = self._fix_ending_brackets(s)
      return s

    def _fix_bracket_mismatch(self, s):
      """修复括号不匹配问题"""
      # 使用栈来跟踪括号
      stack = []
      result = []
      i = 0
      
      while i < len(s):
          char = s[i]
          
          if char == '"':
              # 处理字符串（引号内的括号不参与匹配）
              if not stack or stack[-1] != '"':
                  stack.append('"')
              else:
                  stack.pop()
              result.append(char)
          elif char in '{[(' and (not stack or stack[-1] != '"'):
              stack.append(char)
              result.append(char)
          elif char in '}])' and (not stack or stack[-1] != '"'):
              if stack and stack[-1] in '{[(':
                  # 检查是否匹配
                  open_char = stack[-1]
                  if (open_char == '{' and char == '}') or \
                    (open_char == '[' and char == ']') or \
                    (open_char == '(' and char == ')'):
                      stack.pop()
                      result.append(char)
                  else:
                      # 不匹配，替换为对应的闭合括号
                      stack.pop()
                      close_map = {'{': '}', '[': ']', '(': ')'}
                      result.append(close_map[open_char])
              else:
                  # 栈为空，直接添加闭合括号
                  result.append(char)
          else:
              result.append(char)
          
          i += 1
      
      # 添加缺少的闭合括号
      while stack:
          open_char = stack.pop()
          if open_char != '"':
              close_map = {'{': '}', '[': ']', '(': ')'}
              result.append(close_map[open_char])
      
      return ''.join(result)     

    def _fix_ending_brackets(self, s):
      """
      修复末尾括号问题
      dfsjson格式要求以 }] 结尾
      """
      s = s.rstrip()
      
      if not s:
          return "[]"
      
      # 如果已经是合法的JSON，直接返回
      try:
          json.loads(s)
          return s
      except:
          pass
      
      # 暴力尝试修复：从后往前尝试不同的括号组合
      # dfsjson合法的末尾只能是 ] 或 }] 或 }]]
      for suffix_len in range(1, min(len(s) + 1, 10)):
          suffix = s[-suffix_len:]
          main = s[:-suffix_len]
          
          # 尝试不同的 }] 组合
          for num_close in range(0, 3):
              for num_end in range(0, 3):
                  if num_close == 0 and num_end == 0:
                      continue
                      
                  # 跳过以 }] 以外开头的组合
                  candidate_close = '}' * num_close
                  candidate_end = ']' * num_end
                  
                  # 确定从哪里分割suffix
                  # suffix应该被替换掉
                  candidate = main + candidate_close + candidate_end
                  
                  try:
                      parsed = json.loads(candidate)
                      # 确保是列表
                      if isinstance(parsed, list):
                          return candidate
                  except:
                      pass
      
      # 尝试完全替换末尾
      for num_close in range(0, 5):
          for num_end in range(1, 5):
              candidate = s.rstrip() + '}' * num_close + ']' * num_end
              try:
                  parsed = json.loads(candidate)
                  if isinstance(parsed, list):
                      return candidate
              except:
                  pass
      
      # 尝试从后往前删除多余的字符直到能解析
      for i in range(len(s)):
          truncated = s[:-i] if i > 0 else s
          truncated = truncated.rstrip()
          if not truncated.endswith(']') and not truncated.endswith('}'):
              truncated += ']'
          try:
              parsed = json.loads(truncated)
              if isinstance(parsed, list):
                  return truncated
          except:
              pass
      
      return s   


class DfsParser:
    def __init__(self, ans: str):
        self.ans = ans
        self.TOKEN_RE = re.compile(r"\[|\]|[^\[\]\s]+")
        self.tokens = self.TOKEN_RE.findall(ans)
        self.i = 0
        self.nodes = {}
        self.edges = []

    def _next(self):
        t = self.tokens[self.i] if self.i < len(self.tokens) else None
        self.i += 1
        return t

    def _peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _parse_node(self):
        tok = self._next()
        try:
            mention, typ = tok.split(":", 1)
        except Exception as e:
            return "ERROR"

        if typ != "REF":
            self.nodes[mention.replace("_", " ")] = typ

        while self._peek() and self._peek() != "]":
            rel = self._next()
            if self._peek() == "[":
                self._next()
                child = self._parse_node()
                if (
                    [mention, rel, child] not in self.edges
                    and mention.replace("_", " ") in self.nodes.keys()
                    and child.replace("_", " ") in self.nodes.keys()
                ):
                    self.edges.append([mention.replace("_", " "), rel, child.replace("_", " ")])

        if self._peek() == "]":
            self._next()
        return mention

    def parse(self):
        while self._peek():
            t = self._next()
            if t == "[" and self._peek() == "ROOT":
                self._next()
                while self._peek() and self._peek() != "]":
                    if self._peek() == "[":
                        self._next()
                        self._parse_node()
                    else:
                        self._next()
                if self._peek() == "]":
                    self._next()
        return {"entities": self.nodes, "relations": list(self.edges)}


class SelParser:
    def __init__(self, ans: str):
        self.ans = ans
        self.TOKEN_RE = re.compile(r"\[|\]|[^\s\[\]]+")
        self.tokens = self.TOKEN_RE.findall(ans or "")
        self.i = 0
        self.nodes = {}
        self.edges = []

    def _peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _next(self):
        t = self._peek()
        self.i += 1
        return t

    def _expect(self, tok):
        t = self._next()
        if t != tok:
            raise ValueError(f"Parse error: expect {tok}, got {t}")

    def _parse_entity(self):
        mt = self._next()
        if not mt or ":" not in mt:
            raise ValueError(f"Parse error: bad entity header token: {mt}")

        mention, typ = mt.split(":", 1)
        self.nodes[mention.replace("_", " ")] = typ

        while True:
            t = self._peek()
            if t is None:
                raise ValueError("Parse error: unexpected EOF in entity block")
            if t == "]":
                self._next()
                return
            if t == "[":
                self._next()
                rt = self._next()
                if not rt or ":" not in rt:
                    raise ValueError(f"Parse error: bad relation token: {rt}")
                rel, tail = rt.split(":", 1)
                self._expect("]")
                edge = [mention.replace("_", " "), rel, tail.replace("_", " ")]
                if edge not in self.edges:
                    self.edges.append(edge)
                continue

            self._next()

    def parse(self):
        while self._peek() is not None:
            if self._peek() == "[":
                self._next()
                if self._peek() == "ROOT":
                    self._next()
                    break
            else:
                self._next()

        if self._peek() is None:
            return {"entities": {}, "relations": []}

        while True:
            t = self._peek()
            if t is None:
                raise ValueError("Parse error: unexpected EOF in ROOT block")
            if t == "]":
                self._next()
                break
            if t == "[":
                self._next()
                try:
                    self._parse_entity()
                except Exception as e:
                    while t != "]":
                        self._next()
                continue
            self._next()

        return {"entities": self.nodes, "relations": list(self.edges)}



@dataclass
class MetricPerSample:
    def __post_init__(self):
        self.SYM_RELS = ["Compare", "Conjunction"]
        self._reset()
    def _reset(self):
        self._ent = defaultdict(int)  # keys: tp / fp / fn
        self._rel = defaultdict(int)  # keys: tp / fp / fn 
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
            rel_set.add(rel_)
            # rel_set.add(norm_rel_)
        return ent_set, rel_set
    def evaluate(self, pred_result, label_result):
        pred_ents, pred_rels = self._parse_to_set(pred_result)
        label_ents, label_rels = self._parse_to_set(label_result)        
        self._ent["tp"] += len(pred_ents & label_ents)
        self._ent["fp"] += len(pred_ents - label_ents)
        self._ent["fn"] += len(label_ents - pred_ents)
        self._rel["tp"] += len(pred_rels & label_rels)
        self._rel["fp"] += len(pred_rels - label_rels)
        self._rel["fn"] += len(label_rels - pred_rels)
        return self._dump()

FMT_2_PARSER = {
    "dfsjson": DfsjsonParser,
    "dfs": DfsParser,
    "sel": SelParser,
    "json": JsonParser
}
if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) != 3:
        print("Usage: python graph_dfs.py <dataset> <fmt>")
        sys.exit(1)
    dataset = args[1]
    fmt = args[2]

    in_path = f"/data/wengxiaolong/zhouyuanyun/LlamaFactory/saves/Qwen2.5-7B/lora/sft-{dataset}-{fmt}/output-4680/generated_predictions.jsonl"
    out_path = f"/data/wengxiaolong/zhouyuanyun/LlamaFactory/saves/Qwen2.5-7B/lora/sft-{dataset}-{fmt}/output-4680/generated_predictions_parsed.jsonl"

    outputs = read_jsonl(in_path)
    outputs_new = list()
    for i, output in enumerate(outputs):
        
        pred = output["predict"]
        label = output["label"]
        pred_parsed = FMT_2_PARSER[fmt](pred).parse()
        label_parsed = FMT_2_PARSER[fmt](label).parse()
        output_parsed = {
            "prompt": output["prompt"],
            "predict": pred_parsed,
            "label": label_parsed
        }
        metrics = MetricPerSample().evaluate(pred_parsed,label_parsed)
        output_merged = {**output_parsed, **metrics}
        outputs_new.append(output_merged)
    write_jsonl_w(out_path, outputs_new)

        
