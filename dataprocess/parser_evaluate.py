import json
import re
from file_utils import *
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional


class JsonBaseParser:
    def __init__(self, ans: str):
        self.ans = ans

    def _fix_json(self, s):
      if s.endswith("\"]}]}") or s.endswith("\"]]}}") or s.endswith("\"}]]}"):
          return s[:-4] + "]]}"
      elif s.endswith("\"]}") or s.endswith("\"]]"):
          return  s[:-2] + "]]}" 
      return s   
     
    def _parse_entities(self, json_item):
        raise NotImplementedError("Subclasses must implement _parse_entities()")

    def _parse_relations(self, json_item):
        rels_raw = json_item.get("relations", [])
        if type(rels_raw) != list:
            self.relations = []
            return
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

    def parse(self):
        try:
          #ans_fixed = self._fix_json(self.ans)
          ans_fixed = self.ans
          json_item = json.loads(ans_fixed)
        except Exception as e:
          print(f"Invalid Json Format: {e}")
          print(self.ans)
          return {"entities":{}, "relations":[]}

        self.entities = dict()
        self.relations = list()

        self._parse_entities(json_item)
        self._parse_relations(json_item)
        return {"entities": self.entities, "relations": self.relations}  

class JsonNaiveParser(JsonBaseParser):
    def _parse_entities(self, json_item):
        ents_raw = json_item.get("entities", {})
        if type(ents_raw) != dict:
            self.entities = {}
            return
        for ent_span, ent_type in ents_raw.items():
            if type(ent_span) == str and type(ent_type) == str:
                self.entities[ent_span] = ent_type

class JsonTypeParser(JsonBaseParser):
    def _parse_entities(self, json_item):
        ent_raws = json_item.get("entities", {})
        if type(ent_raws) != dict:
            self.entities = {}
            return
        for ent_span, info in ent_raws.items():
            if type(info) != dict:
                continue
            ent_type = info.get("type", "UNKNOWN")
            if  type(ent_span) == str and type(ent_type) == str:
                self.entities[ent_span] = ent_type

class JsonSpanTypeParser(JsonBaseParser):
    def _parse_entities(self, json_item):
        ents_raw = json_item.get("entities", {})
        if type(ents_raw) != list:
            self.entities = {}
            return
        for ent_dict in ents_raw:
            if type(ent_dict) != dict:
                continue
            ent_span = ent_dict.get("span", None)
            if not ent_span:
                continue
            ent_type = ent_dict.get("type", "UNKNOWN")
            if  type(ent_span) == str and type(ent_type) == str:
                self.entities[ent_span] = ent_type

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
     
    def parse(self):
        try:
          ans_fixed = self.ans
          #ans_fixed = self._fix_dfsjson(self.ans)
          json_list = json.loads(ans_fixed)
        except Exception as e:
          print(f"Invalid Json Format: {e}")
          return {"entities":{}, "relations":[]}
        
        if not isinstance(json_list, list):
          return {"entities": {}, "relations": []}
        for root_item in json_list:
          self._traverse(root_item)
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
        self.ans = self._fix_unclosed_brackets(ans)
        self.TOKEN_RE = re.compile(r"\[|\]|[^\[\]\|]+")
        self.tokens = self.TOKEN_RE.findall(self.ans)
        self.i = 0
        self.nodes = {}
        self.edges = []

    def _fix_unclosed_brackets(self, s: str) -> str:
        """
        防止末端右括号不闭合导致解析死循环：
        若 '[' 数量多于 ']'，则在末尾补齐缺失数量的 ']'.
        """
        if not isinstance(s, str):
            return s
        diff = s.count("[") - s.count("]")
        if diff > 0:
            return s + ("]" * diff)
        return s    
    
    def _next(self):
        t = self.tokens[self.i] if self.i < len(self.tokens) else None
        self.i += 1
        return t

    def _peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _parse_node(self):
        #if self._peek() == "[":
        #    self._next()
        tok = self._next()
      
        parts = tok.rsplit(":", 1)
        #print(parts)
        if len(parts) != 2:
            return False
        else:
            mention = parts[0].strip()
            typ = parts[-1].strip()
            
        if typ != "REF":
            self.nodes[mention] = typ
        
        # 严格检查：只要后面不是 ')'，就说明有 [关系 (子节点)] 结构
        while self._peek() and self._peek() != "]":
            rel = self._next().strip()
            if self._peek() == "[":
                self._next() # 消耗 '('
                child = self._parse_node()
                '''if not child:
                    # 核心修复：更新指针跳过当前出错的实体块，直到遇到右括号
                    while self._peek() is not None and self._peek() != "]":
                        self._next()
                    if self._peek() == "]":
                        self._next() # 消耗掉该错误实体的右括号
                    return False'''
                if [mention, rel, child] not in self.edges:
                    self.edges.append([mention, rel, child]) # 存入 set
        
        # 消耗自己的 ']'
        if self._peek() == "]":
            self._next()
        return mention

    def parse(self):
        try:
            if self._peek() == "[":
                self._next()
            while self._peek() and self._peek() != "]":
                if self._peek() == "[":
                    self._next() # 消耗顶级节点的 '('
                    self._parse_node()
                    '''if not self.parse_node():
                        # 核心修复：更新指针跳过当前出错的实体块，直到遇到右括号
                        while self._peek() is not None and self._peek() != "]":
                            self._next()
                        if self._peek() == "]":
                            self._next() # 消耗掉该错误实体的右括号'''
                else: self._next() # 跳过
            return {"entities": self.nodes, "relations": list(self.edges)}
        except Exception:
            return {"entities": {}, "relations": []}


class SelParser:
    def __init__(self, ans: str):
        self.ans = self._fix_unclosed_brackets(ans)
        self.TOKEN_RE = re.compile(r"\[|\]|[^\[\]]+")
        self.tokens = self.TOKEN_RE.findall(self.ans or "")
        self.i = 0
        self.nodes = {}
        self.edges = []

    def _fix_unclosed_brackets(self, s: str) -> str:
        """
        防止末端右括号不闭合导致解析死循环：
        若 '[' 数量多于 ']'，则在末尾补齐缺失数量的 ']'.
        """
        if not isinstance(s, str):
            return s
        diff = s.count("[") - s.count("]")
        if diff > 0:
            return s + ("]" * diff)
        return s    

    def _peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _next(self):
        t = self._peek()
        self.i += 1
        return t

    def _parse_entity(self):
        """
        已经消耗了实体块起始的 '['，当前 token 形如 'mention:TYPE'，
        之后是若干个关系块，每个为 '[REL:TAIL]'，最后以 ']' 结束。
        返回 True 表示解析成功，返回 False 表示遇到格式错误。
        """
        mt = self._next()
        #print(f"Debug for mt : {mt}")
        # 格式错误判断：避免原本的 NameError 和 ValueError
        if not mt or ":" not in mt:
            return False
        parts = mt.rsplit(":", 1)
        if len(parts) != 2:
            return False
        mention, typ = parts[0].strip(), parts[1].strip()
        self.nodes[mention] = typ

        while self._peek() and self._peek() != "]":
            if self._peek() == "[":
                # 关系块：[REL:TAIL]
                self._next()           # 消耗 '['
                rt = self._next()
                
                # 校验关系 token 是否合法
                if not rt or ":" not in rt:
                    return False
                
                parts = rt.split(":", 1)
                if len(parts) != 2:
                    return
                rel, tail =parts[0].strip(), parts[1].strip()
                edge = [mention, rel, tail]
                if edge not in self.edges:
                    self.edges.append(edge)
                if self._peek() == "]":
                    self._next()
            # 容错：跳过意外 token
            else: self._next()
            
        if self._peek() == "]":
            self._next()

    def parse(self):
        try:
            if self._peek() == "[":
                self._next()
            # 解析 ROOT 内部的若干实体块，直到遇到对应的 ']'
            while self._peek() and self._peek() != "]":
                #print(self._peek())
                if self._peek() == "[":
                    self._next()  # 消耗实体块起始 '['
                    # 尝试解析实体，如果不规范则安全跳过，避免死循环
                    self._parse_entity()
                    '''if not self._parse_entity():
                        # 核心修复：更新指针跳过当前出错的实体块，直到遇到右括号
                        while self._peek() is not None and self._peek() != "]":
                            self._next()
                        if self._peek() == "]":
                            self._next() # 消耗掉该错误实体的右括号'''
                # 其他 token（例如多余空白）直接跳过
                else:self._next()

            return {"entities": self.nodes, "relations": list(self.edges)}
            
        except Exception:
            # 终极兜底：万一发生任何预料之外的严重错误（不 raise，按要求返回空结果）
            return {"entities": {}, "relations": []}  


@dataclass
class MetricSample:
    def __post_init__(self):
        self.SYM_RELS = ["Compare", "Conjunction"]
        self._global_ent_tp = 0
        self._global_rel_tp = 0
        self._global_ent_fp = 0
        self._global_rel_fp = 0
        self._global_ent_fn = 0
        self._global_rel_fn = 0
        self._metric_per_sample = list()
        self._metric_global = defaultdict(float)
        self._reset()

    def _reset(self):
        self._ent = defaultdict(int)  # keys: tp / fp / fn
        self._rel = defaultdict(int)  # keys: tp / fp / fn 

    def cal_metric(self, tp, fp, fn):
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0 
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0 
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        return p, r, f1
    def _dump(self) -> Optional[dict[str, float]]:
        ent_metric = self.cal_metric(self._ent["tp"], self._ent["fp"], self._ent["fn"])
        rel_metric = self.cal_metric(self._rel["tp"], self._rel["fp"], self._rel["fn"])

        self._global_ent_tp += self._ent["tp"]
        self._global_rel_tp += self._rel["tp"]
        self._global_ent_fp += self._ent["fp"]
        self._global_rel_fp += self._rel["fp"]
        self._global_ent_fn += self._ent["fn"]
        self._global_rel_fn += self._rel["fn"]

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
        for span, typ in ents.items():
            ent_set.add((span, typ))

        ent_span_list = [ent[0] for ent in ent_set]
        if not isinstance(rels, list):
            return ent_set, list()
        rel_set = set()
        for rel in rels:
            if not isinstance(rel, list) or len(rel) != 3:
                continue
            head_span, rel_type, tail_span = rel[0], rel[1], rel[2]
            if head_span not in ent_span_list or tail_span not in ent_span_list:
                continue
            head_type = ents.get(head_span, "UNKNOWN")
            tail_type = ents.get(tail_span, "UNKNOWN")
            rel_ = (head_span, head_type, rel_type, tail_span, tail_type)
            norm_rel_ = self._normalize_sym_rel(rel_)
            #rel_set.add(rel_)
            rel_set.add(norm_rel_)
        return ent_set, rel_set
    
    def evaluate(self, pred_results, label_results):
        for pred_result, label_result in zip(pred_results, label_results):
            pred_ents, pred_rels = self._parse_to_set(pred_result)
            label_ents, label_rels = self._parse_to_set(label_result)        
            self._ent["tp"] += len(pred_ents & label_ents)
            self._ent["fp"] += len(pred_ents - label_ents)
            self._ent["fn"] += len(label_ents - pred_ents)
            self._rel["tp"] += len(pred_rels & label_rels)
            self._rel["fp"] += len(pred_rels - label_rels)
            self._rel["fn"] += len(label_rels - pred_rels)
            result =  self._dump()
            self._metric_per_sample.append(result)
        result_global_ent  = self.cal_metric(self._global_ent_tp, self._global_ent_fp, self._global_ent_fn)
        result_global_rel  = self.cal_metric(self._global_rel_tp, self._global_rel_fp, self._global_rel_fn)
        self._metric_global = {
            "ent_f1": result_global_ent[2],
            "rel_f1": result_global_rel[2],
            "ent_p": result_global_ent[0],
            "ent_r": result_global_ent[1],
            "rel_p": result_global_rel[0],
            "rel_r": result_global_rel[1],            
        }
        return self._metric_per_sample, self._metric_global

FMT_2_PARSER = {
    "dfsjson": DfsjsonParser,
    "dfs": DfsParser,
    "sel": SelParser,
    "json": JsonNaiveParser
}
FMT_2_ID_wofmt_conll04 = {
    "json": 500, 
    "dfsjson": 2000, 
    "dfs": 2000, 
    "sel": 1500
}
FMT_2_ID_conll04 = {
    "json": 1000, 
    "dfsjson": 1000, 
    "dfs": 1500, 
    "sel": 1000
}
FMT_2_ID_scierc = {
    "json": 3000, 
    "dfsjson": 1500, 
    "dfs": 1500, 
    "sel": 2000
}
FMT_2_ID_ace2005 = {
    "json": 18000, 
    "dfsjson": 18000, 
    "dfs": 15000, 
    "sel": 18000
}

if __name__ == "__main__":
    import sys
    args = sys.argv

    dataset = "ace2005"
 
        
    #datasets = ["conll04"]
    fmts = ["dfsjson"]
    #fmts = ["json", "dfs", "sel"]
    #for dataset in datasets:
    for fmt in fmts:
        ckpt = FMT_2_ID_ace2005[fmt]
        in_path = f"/data/wengxiaolong/zhouyuanyun/LlamaFactory/saves/Qwen2.5-7B/lora/sft-{dataset}-{fmt}/output-{ckpt}-3/predict_test_predictions.jsonl"
        out_path = f"/data/wengxiaolong/zhouyuanyun/LlamaFactory/saves/Qwen2.5-7B/lora/sft-{dataset}-{fmt}/output-{ckpt}-3/parsed_predict_test_predictions.jsonl"

        outputs = read_jsonl(in_path)
        outputs_new = list()
        metric = MetricSample()

        pred_parsed_list = list()
        label_parsed_list = list()
        output_parsed_list = list()
        for i, output in enumerate(outputs):
            
            pred = output["predict"]
            label = output["label"]
            # print(label)
            pred_parsed = FMT_2_PARSER[fmt](pred).parse()
            '''if fmt == "dfsjson" or fmt == "json":
                try:
                    pred = json.loads(pred) 
                    label = json.loads(label)
                except Exception:
                    pass'''
            label_parsed = FMT_2_PARSER[fmt](label).parse()
            pred_parsed_list.append(pred_parsed)
            label_parsed_list.append(label_parsed)
            output_parsed = {
                "id": i + 1,
                #"input": output["prompt"].split("**Input**")[1],
                "input": output["prompt"], 
                "pred": pred,
                "label": label,
                "pred_parsed": pred_parsed,
                "label_parsed": label_parsed
            }
            output_parsed_list.append(output_parsed)
        metric_samplelist, metric_global = metric.evaluate(pred_parsed_list,label_parsed_list)
        print(f"\n--------Evaluation results of {dataset} {fmt}------")
        print(metric_global)

        output_merged_list = list()
        for output_parsed, scores in zip(output_parsed_list, metric_samplelist):
            output_merged = {**output_parsed, **scores}
            output_merged_list.append(output_merged)
        write_json(out_path, output_merged_list)

        
