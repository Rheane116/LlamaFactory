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
    sub_str = sub_str.replace("_", " ")
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
    #adj = sorted(adj, key = )
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
    print(text)
    # 建立邻接表
    adj = build_adj(graph)
    nodes = graph["entities"]

    body_parts = []
    # 核心修改：ROOT 下的多个顶级节点按文本序排列
    all_nodes_sorted = sorted(nodes.keys(), key=lambda n: get_text_order(text, n))
    #print(all_nodes_sorted)
    for mention in all_nodes_sorted:
        body_parts.append(f" [{mention.replace(' ', '_')}:{nodes[mention]}")
        #print(f"{mention}:{adj[mention]}")
        edges_sorted = sorted(adj[mention], key = lambda x: get_text_order(text, x[1]))
        #print(f"{mention}:{edges_sorted}")
        #print("\n")
        for edge in edges_sorted:
            body_parts.append(f" [{edge[0]}:{edge[1].replace(' ', '_')}]")
        body_parts.append("]")

    return f"[ROOT{''.join(body_parts)}]"




# =============== DESERIALIZATION（SEL 新格式） ==================

# \s 代表任意空白符（空格、制表符、换行等），[^...] 是「非匹配」，+ 表示「至少一个」
TOKEN_RE_SEL = re.compile(r'\[|\]|[^\s\[\]]+')


class Parser_sel:
    """
    解析 SEL 新格式：
      [ROOT [A:TYPEA [E1:B] [E2:C]] [B:TYPEB [E3:C]] [C:TYPEC]]
    """

    def __init__(self, s):
        self.tokens = TOKEN_RE_SEL.findall(s or "")
        self.i = 0
        self.nodes = {}
        self.edges = []

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def next(self):
        t = self.peek()
        self.i += 1
        return t

    def _expect(self, tok):
        t = self.next()
        if t != tok:
            raise ValueError(f"Parse error: expect {tok}, got {t}")

    def _parse_entity(self):
        """
        已经消耗了实体块起始的 '['，当前 token 形如 'mention:TYPE'，
        之后是若干个关系块，每个为 '[REL:TAIL]'，最后以 ']' 结束。
        """
        mt = self.next()
        if not mt or ":" not in mt:
            raise ValueError(f"Parse error: bad entity header token: {mt}")
            #print(f"Parse error: bad entity header token: {mt}")
            
        mention, typ = mt.split(":", 1)
        self.nodes[mention.replace('_', ' ')] = typ

        while True:
            t = self.peek()
            if t is None:
                raise ValueError("Parse error: unexpected EOF in entity block")
            if t == "]":
                self.next()  # 结束当前实体块
                return
            if t == "[":
                # 关系块：[REL:TAIL]
                self.next()           # 消耗 '['
                rt = self.next()
                if not rt or ":" not in rt:
                    raise ValueError(f"Parse error: bad relation token: {rt}")
                rel, tail = rt.split(":", 1)
                self._expect("]")
                edge = [mention.replace('_', ' '), rel, tail.replace('_', ' ')]
                if edge not in self.edges:
                    self.edges.append(edge)
                continue

            # 容错：跳过意外 token
            self.next()

    def parse(self):
        # 寻找 ROOT 起点
        while self.peek() is not None:
            if self.peek() == "[":
                self.next()
                if self.peek() == "ROOT":
                    self.next()  # 消耗 ROOT
                    break
            else:
                self.next()

        # 未找到 ROOT，则认为是空图
        if self.peek() is None:
            return {"entities": {}, "relations": []}

        # 解析 ROOT 内部的若干实体块，直到遇到对应的 ']'
        while True:
            t = self.peek()
            if t is None:
                raise ValueError("Parse error: unexpected EOF in ROOT block")
            if t == "]":
                self.next()  # 结束 ROOT
                break
            if t == "[":
                self.next()          # 消耗实体块起始 '['
                try:
                    self._parse_entity() # 解析实体及其所有关系
                except Exception as e:
                    while t != "]":
                        self.next()
                continue
            # 其他 token（例如多余空白）直接跳过
            self.next()

        return {"entities": self.nodes, "relations": list(self.edges)}


# =============== VALIDATION ==================
def verify(original, recovered):
    orig_edges = sorted(original["relations"])
    reco_edges = sorted(recovered["relations"])
    '''for i in range(len(orig_edges)):
        orig_edges[i][0] = orig_edges[i][0].replace("_", " ")
        orig_edges[i][-1] = orig_edges[i][-1].replace("_", " ")
    for i in range(len(reco_edges)):
        reco_edges[i][0] = reco_edges[i][0].replace("_", " ")
        reco_edges[i][-1] = reco_edges[i][-1].replace("_", " ")
    for k, v in original["entities"].items():
        original["entities"][k.replace("_", " ")] = v
        del original["entities"][k]
    for k, v in recovered["entities"].items():
        recovered["entities"][k.replace("_", " ")] = v
        del recovered["entities"][k]
    print(orig_edges)
    print(reco_edges)
    print(original["entities"])
    print(recovered["entities"])'''
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
        print("Usage: python build_graph.py <dataset> <split>")
        sys.exit(1)

    dataset = args[1]
    split = args[2]'''

    from tqdm import tqdm
    datasets = ["conll04", "scierc", "ace2005"]
    splits = ["train", "dev", "test"]

    for dataset in datasets:
        for split in splits:
            datalist = read_jsonl(f"data_raw/{dataset}/{split}_graph_mapped.jsonl")
            datalist_new = list()
            for i, data in tqdm(enumerate(datalist)):
                print(f"Processing {i}th data...")
                if len(data['sentences']) < 1 or len(data['entities']) < 1:
                    seq = "[ROOT]"
                else:
                    text = data['sentences']
                    G = {"entities": data['entities'], "relations": data['relations']}
                    print(f"text:{text}")
                    print(f"nodes:{data['entities']}")
                    print(f"edges:{data['relations']}")
                    seq = serialize_graph(G, text)
                    print("Serialized:\n", seq)
                    #print("Token count:", count_tokens(seq))
                    G2 = Parser_sel(seq).parse()
                    print(f"G2:{G2}")
                    if_match = verify(G, G2)
                    if not if_match:
                        print("Not match!!!!")
                        break
                    print("--------------------------------")
                data_new = copy.deepcopy(data)
                data_new["serialized"] = seq
                datalist_new.append(data_new)
            write_jsonl_w(f"data_raw/{dataset}/{split}_graph_serialized_sel.jsonl", datalist_new)

    '''text = "A 49-year - old man with Crohn 's disease treated with prednisone and mesalamine ( 5-ASA ) developed worsening respiratory distress and fever ."

    G = {
            "entities": {"5-ASA": {"type": "Drug"}, "fever": {"type": "Adverse-Effect"}, "mesalamine": {"type": "Drug"}, "prednisone": {"type": "Drug"}, "worsening respiratory distress": {"type": "Adverse-Effect"}}, "relations": [["fever", "adverse_effect", "5-ASA"], ["fever", "adverse_effect", "mesalamine"], ["fever", "adverse_effect", "prednisone"], ["worsening respiratory distress", "adverse_effect", "5-ASA"], ["worsening respiratory distress", "adverse_effect", "mesalamine"], ["worsening respiratory distress", "adverse_effect", "prednisone"]]}

    seq = serialize_graph(G, text)
    print("Serialized:\n", seq)

    G2 = Parser_sel(seq).parse()
    print("Recovered graph:", G2)

    # 执行验证
    is_perfect = verify(G, G2)
    if is_perfect:
        print("SUCCESS: The graph was recovered perfectly!")
    else:
        print("FAILURE: There are discrepancies between the graphs.") '''