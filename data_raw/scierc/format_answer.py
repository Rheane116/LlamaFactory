import json

# 读取原始文件
with open('/data1/zhouyuanyun/mywork/data_raw/scierc/post_test_llm_answer_dfsjson2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 格式化每个样本的answer字段
for sample in data:
    if 'answer' in sample:
        try:
            # 解析answer字段
            answer_json = json.loads(sample['answer'])
            # 重新格式化
            sample['answer'] = json.dumps(answer_json, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            print(f"Error parsing answer in sample {sample['sent_id']}: {e}")
            # 如果解析失败，保留原始内容
            pass

# 写入格式化后的文件
with open('/data1/zhouyuanyun/mywork/data_raw/scierc/format_post_test_llm_answer_dfsjson2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("格式化完成，已保存到 format_post_test_llm_answer_dfsjson2.json")