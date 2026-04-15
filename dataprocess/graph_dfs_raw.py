import collections
import re
import json
import copy
import sys
from file_utils import *


def get_text_order(main_str, sub_str):
    """
    在母串中全字匹配子串（考虑空格/特殊字符），返回第一个匹配位置的起始索引
    :param main_str: 母串（被搜索的字符串）
    :param sub_str: 子串（需全字匹配，可包含空格、单引号等特殊字符）
    :return: int，第一个匹配的起始索引；无匹配返回 -1
    """
    #sub_str = sub_str.replace("_", " ")
    # 1. 转义子串中的正则特殊字符（如'、.、*等），确保按字面量匹配
    escaped_sub = re.escape(sub_str)
    
    # 2. 构建全字匹配规则：子串前后是「非单词字符/字符串边界」
    # (?<!\w)：前面不是单词字符（字母/数字/下划线）；(?!\w)：后面不是单词字符
    # \s* 兼容子串前后可能的空格（可选，根据实际需求）
    pattern = re.compile(r'(?<!\w)' + escaped_sub + r'(?!\w)')
    
    # 3. 搜索第一个匹配项
    match = pattern.search(main_str)
    
    # 4. 返回结果：有匹配返回起始索引，无匹配返回-1
    return match.start() if match else -1


# =============== GRAPH UTILS ==================

# 建立邻接表
# 格式： {v1:[(e12, v2)], v2:[(e23, v3), (e25, v5)}
def build_adj(graph):
    adj = collections.defaultdict(list)
    for s, r, t in graph["relations"]:
        adj[s].append((r, t))
    return adj

def choose_root(graph):
    # 优先选择有出边的节点，如果没有，则选字母序第一个
    sources = {s for s, _, _ in graph["relations"]}
    if sources:
        return sorted(list(sources))[0]
    return sorted(graph["entities"].keys())[0]

def build_spanning_tree(graph, text): # 增加 text 参数
    adj = build_adj(graph)
    visited = set()
    tree_edges = set()
    
    def dfs(u):
        visited.add(u)
        # 排序：邻居节点 (v) 按照在文本中出现的先后顺序排序
        neighbors = adj.get(u, [])
        # 自定义排序规则，先按get_text_order(x[1], text)排序再按x[0]排序
        sorted_neighbors = sorted(neighbors, key=lambda x: (get_text_order(text, x[1]), x[0]))
        
        for rel, v in sorted_neighbors:
            if v not in visited:
                tree_edges.add((u, rel, v))
                dfs(v)
    
    # 按照节点在文本中出现的先后顺序尝试访问，处理非连通森林
    all_nodes_sorted = sorted(graph["entities"].keys(), key=lambda n: get_text_order(text, n))
    for n in all_nodes_sorted:
        if n not in visited:
            dfs(n)
            
    return tree_edges



def serialize_graph(graph, text): # 增加 text 参数
    # 建立邻接表
    adj = build_adj(graph)
    # 建立dfs树
    tree_edges = build_spanning_tree(graph, text) 
    nodes = graph["entities"]
    # 已扩展的节点
    has_expanded = set()

    def expand(node):
        has_expanded.add(node)
        typ = nodes[node]
        parts = ["[", f"{node}:{typ}"]

        # 核心修改：分支展开的顺序也要符合文本序
        neighbors = adj.get(node, [])
        sorted_neighbors = sorted(neighbors, key=lambda x: (get_text_order(text, x[1]), x[0]))

        for rel, tgt in sorted_neighbors:
            parts.append(f"|{rel}")
            if (node, rel, tgt) in tree_edges and tgt not in has_expanded:
                parts.append(expand(tgt))
            else:
                parts.append(f"[{tgt}:REF]")
        
        parts.append("]")
        return "".join(parts)

    body_parts = []
    # 核心修改：ROOT 下的多个顶级节点按文本序排列
    all_nodes_sorted = sorted(nodes.keys(), key=lambda n: get_text_order(text, n))
    for n in all_nodes_sorted:
        if n not in has_expanded:

            body_parts.append(expand(n))

    return f"[{''.join(body_parts)}]"




# =============== DESERIALIZATION (修正版) ==================

#SPECIAL_TOKENS = {"[", "]", ":"}

# \s 代表任意空白符（空格、制表符、换行等），[^...] 是「非匹配」，+ 表示「至少一个」
TOKEN_RE = re.compile(r'\[|\]|[^\|\[\]]+')
#s = "[ROOT [Moscow:loc] [Leningrad:loc] [Armenian:other] [Yerevan:loc] [U.S.:loc] [British:other] [Bolshoi Ballet:org orgbased_in [Moscow:REF]] [Kirov_Ballet:org orgbased_in [Leningrad:REF]] [June_Anderson:peop live_in [U.S.:REF]] [Carol_Vaness:peop live_in [U.S.:REF]]]"
#print(TOKEN_RE.findall(s))

# =============== DESERIALIZATION (修正版) ==================
class Parser_dfs:
    def __init__(self, s):
        self.tokens = TOKEN_RE.findall(s)
        self.i = 0
        self.nodes = {}
        self.edges = [] # 改用 set 自动去重

    def next(self):
        t = self.tokens[self.i] if self.i < len(self.tokens) else None
        self.i += 1
        return t

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def parse_node(self):
        #if self.peek() == "[":
        #    self.next()
        tok = self.next()
      
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
        while self.peek() and self.peek() != "]":
            rel = self.next().strip()
            if self.peek() == "[":
                self.next() # 消耗 '('
                child = self.parse_node()
                '''if not child:
                    # 核心修复：更新指针跳过当前出错的实体块，直到遇到右括号
                    while self.peek() is not None and self.peek() != "]":
                        self.next()
                    if self.peek() == "]":
                        self.next() # 消耗掉该错误实体的右括号
                    return False'''
                if [mention, rel, child] not in self.edges and mention in self.nodes.keys() and child in self.nodes.keys():
                    self.edges.append([mention, rel, child]) # 存入 set
        
        # 消耗自己的 ']'
        if self.peek() == "]":
            self.next()
        return mention

    def parse(self):
        if self.peek() == "[":
            self.next()
        while self.peek() and self.peek() != "]":
            if self.peek() == "[":
                self.next() # 消耗顶级节点的 '('
                self.parse_node()
                '''if not self.parse_node():
                    # 核心修复：更新指针跳过当前出错的实体块，直到遇到右括号
                    while self.peek() is not None and self.peek() != "]":
                        self.next()
                    if self.peek() == "]":
                        self.next() # 消耗掉该错误实体的右括号'''
            else: self.next() # 跳过
        return {"entities": self.nodes, "relations": list(self.edges)}

# =============== VALIDATION ==================
def verify(original, recovered):
    orig_edges = sorted(original["relations"])
    reco_edges = sorted(recovered["relations"])
    nodes_match = original["entities"] == recovered["entities"]
    edges_match = orig_edges == reco_edges
    
    print(f"\nNodes Match: {nodes_match}")
    print(f"Edges Match: {edges_match}")
    if not edges_match:
        print("Original edges count:", len(orig_edges))
        print("Recovered edges count:", len(reco_edges))
    return nodes_match and edges_match


# =============== DEMO ==================
if __name__ == "__main__":

    args = sys.argv
    '''if len(args) != 3:
        print("Usage: python graph_dfs.py <dataset> <split>")
        sys.exit(1)
    dataset = args[1]
    split = args[2]'''
    from tqdm import tqdm

    datasets = ["ace2005"]
    splits = ["train", "dev", "test"]

    for dataset in datasets:
        for split in splits:
            datalist = read_jsonl(f"data_raw/{dataset}/{split}_graph_mapped.jsonl")
            datalist_new = list()
            for i, data in tqdm(enumerate(datalist)):
                print(f"Processing {i}th data...")
                if len(data['sentences']) < 1 or len(data['entities']) < 1:
                    seq = "[]"
                else:
                    text = data['sentences']
                    G = {"entities": data['entities'], "relations": data['relations']}
                    print(f"text:{text}")
                    print(f"entities:{data['entities']}")
                    print(f"relations:{data['relations']}")
                    seq = serialize_graph(G, text)
                    print("Serialized:\n", seq)
                    #print("Token count:", count_tokens(seq))
                    G2 = Parser_dfs(seq).parse()
                    print(f"G2:{G2}")
                    if_match = verify(G, G2)
                    if not if_match:
                        print("Not match!!!!")
                        sys.exit(0)
                    print("--------------------------------")
                data_new = copy.deepcopy(data)
                data_new["serialized"] = seq
                datalist_new.append(data_new)
            write_jsonl_w(f"data_raw/{dataset}/{split}_graph_serialized_dfs.jsonl", datalist_new)

    '''text = "<entity_span_1> <entity_span_2> <entity_span_3> <entity_span_4> <entity_span_5> ."

    G = {
    "entities": {
        "<entity_span_1>": "<Entity_Type_1>",
        "<entity_span_2>": "<Entity_Type_2>",
        "<entity_span_3>": "<Entity_Type_3>",
        "<entity_span_4>": "<Entity_Type_4>",
        "<entity_span_5>": "<Entity_Type_5>",
    },
    "relations": [
        ["<entity_span_2>", "<Relation_Type_1>", "<entity_span_3>"],
        ["<entity_span_2>", "<Relation_Type_2>", "<entity_span_5>"],
        ["<entity_span_4>", "<Relation_Type_2>", "<entity_span_3>"],
    ]
    }
    seq = serialize_graph(G, text)
    print("Serialized:\n", seq)

    G2 = Parser_dfs(seq).parse()
    print("Recovered graph:", G2)

    # 执行验证
    is_perfect = verify(G, G2)
    if is_perfect:
        print("SUCCESS: The graph was recovered perfectly!")
    else:
        print("FAILURE: There are discrepancies between the graphs.") '''