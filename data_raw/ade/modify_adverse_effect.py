import json

# 读取原始文件
with open('data_raw/ade/test_graph.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 处理每一行
modified_lines = []
for line in lines:
    try:
        data = json.loads(line)
        
        # 修改句子文本中的adverse_effect为adverse effect
        if 'sentences' in data:
            data['sentences'] = data['sentences'].replace('adverse_effect', 'adverse effect')
        
        # 修改实体中的adverse_effect为adverse effect
        if 'entities' in data:
            new_entities = {}
            for entity_name, entity_info in data['entities'].items():
                # 替换实体名称中的adverse_effect
                new_entity_name = entity_name.replace('adverse_effect', 'adverse effect')
                # 如果实体类型不是adverse_effect，替换类型中的adverse_effect
                if entity_info.get('type') != 'adverse_effect':
                    entity_info['type'] = entity_info['type'].replace('adverse_effect', 'adverse effect')
                new_entities[new_entity_name] = entity_info
            data['entities'] = new_entities
        
        # 修改关系中的adverse_effect为adverse effect（仅修改实体名称，不修改关系类型）
        if 'relations' in data:
            new_relations = []
            for relation in data['relations']:
                if len(relation) >= 3:
                    head, rel_type, tail = relation[0], relation[1], relation[2]
                    # 替换头尾实体名称中的adverse_effect
                    new_head = head.replace('adverse_effect', 'adverse effect')
                    new_tail = tail.replace('adverse_effect', 'adverse effect')
                    # 关系类型保持adverse_effect不变
                    new_relations.append([new_head, rel_type, new_tail])
                else:
                    new_relations.append(relation)
            data['relations'] = new_relations
        
        # 转换回JSON字符串
        modified_line = json.dumps(data, ensure_ascii=False)
        modified_lines.append(modified_line)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing line: {e}")
        modified_lines.append(line)

# 写入修改后的文件
with open('data_raw/ade/test_graph.jsonl', 'w', encoding='utf-8') as f:
    f.write('\n'.join(modified_lines))

print("修改完成，已保存到 train_graph.jsonl")