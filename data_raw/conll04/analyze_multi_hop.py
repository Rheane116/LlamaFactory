import json
from collections import defaultdict, deque

def has_multi_hop_relations(relations):
    """
    检查关系列表中是否含有多跳关系（A->B->C）
    使用BFS查找最短路径
    """
    if not relations:
        return False
    
    # 构建邻接表
    graph = defaultdict(list)
    entities = set()
    
    for head, rel_type, tail in relations:
        graph[head].append((tail, rel_type))
        #graph[tail].append((head, rel_type))
        entities.add(head)
        entities.add(tail)
    
    # 检查所有实体对之间的最短路径
    entity_list = list(entities)
    
    for i, start in enumerate(entity_list):
        for end in entity_list[i+1:]:
            # BFS查找最短路径
            if has_path(graph, start, end, min_hops=2):
                return True
    
    return False

def has_path(graph, start, end, min_hops=2):
    """
    使用BFS查找从start到end的路径，返回是否存在长度>=min_hops的路径
    """
    if start == end:
        return False
    
    visited = set()
    queue = deque([(start, 0)])
    
    while queue:
        node, hops = queue.popleft()
        
        if node == end:
            return hops >= min_hops
        
        if node in visited:
            continue
        visited.add(node)
        
        for neighbor, _ in graph[node]:
            if neighbor not in visited:
                queue.append((neighbor, hops + 1))
    
    return False

def analyze_multi_hop_ratio(file_path):
    """
    分析数据集中含有多跳关系的样本比例
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_samples = 0
    multi_hop_samples = 0
    multi_hop_details = []
    
    for line in lines:
        try:
            data = json.loads(line)
            relations = data.get('relations', [])
            
            total_samples += 1
            
            if has_multi_hop_relations(relations):
                multi_hop_samples += 1
                multi_hop_details.append({
                    'doc_id': data.get('doc_id', ''),
                    'sent_id': data.get('sent_id', -1),
                    'relations': relations
                })
        
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            continue
    
    ratio = multi_hop_samples / total_samples if total_samples > 0 else 0
    
    print(f"统计结果:")
    print(f"总样本数: {total_samples}")
    print(f"含多跳关系的样本数: {multi_hop_samples}")
    print(f"多跳关系样本比例: {ratio:.2%}")
    print(f"\n多跳关系样本详情（前10个）:")
    for i, detail in enumerate(multi_hop_details[:10]):
        print(f"\n{i+1}. doc_id={detail['doc_id']}, sent_id={detail['sent_id']}")
        print(f"   关系: {detail['relations']}")
    
    return {
        'total': total_samples,
        'multi_hop': multi_hop_samples,
        'ratio': ratio
    }

if __name__ == '__main__':
    file_path = '/data1/zhouyuanyun/mywork/data_raw/conll04/test_graph.jsonl'
    analyze_multi_hop_ratio(file_path)