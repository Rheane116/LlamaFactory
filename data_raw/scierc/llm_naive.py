import requests
import json
from copy import deepcopy

def read_jsonl(path):
    datalist = list()
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        datalist.append(json.loads(line))
    return datalist
def write_jsonl(data, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


prompt = '''
  你的任务是做实体关系联合抽取。
  # 1.任务schema
  确保输出的标签在给出的6种实体标签与7种关系标签之中！
  ## 1.1 实体标签（6种）
    （1）Task
    含义：科学研究中的任务或问题设置，通常对应论文标题/研究方向/实验任务。
    例子：Recognition_of_proper_nouns、morphological_analysis、Japanese_information_extraction、reconstruction。
    （2）Method
    含义：完成某个任务所用的方法、算法、模型、系统或具体技术方案。
    例子：morphological_analyzer、Amorph、dictionary_lookup、Bayesian_inference、spoken_language_understanding_system。
    （3）Material
    含义：实验或研究中使用的数据、语料、语言文本、硬件/软件资源等“材料”。
    例子：Japanese_text、annotated_training_corpus、English_and_Czech_newspaper_texts、new_domains。
    （4）OtherScientificTerm
    含义：其他科学术语，包括概念、变量、特征、结构、约束、知识等，不直接当作任务/方法/材料。
    例子：proper_nouns、Named_Entity_-LRB-_NE_-RRB-_items、syntactic_knowledge、complex_tree_structures。
    （5）Generic
    含义：语境中的泛指名词或指代项，本身不是具体科学术语，但在关系中当作一个节点引用，如“它/该方法/该模型”。
    例子：It、approach、analyzer、task、They、model、system、posterior。
    （6）Metric 
    含义：表示评价指标 / 度量标准，用来衡量模型、方法或结果好坏的量化值或属性。
    例子：pixel-wise_differences_in_image_intensity、repeatability、labelled_bracket_F-score、accuracy等。
 ## 1.2 关系标签（7种）
    （1）USED-FOR
    含义：X 被用来完成/实现 Y（X 用于 Y）。
    典型模式：Method/Material/Term USED-FOR Task/Term。
    （2）PART-OF
    含义：X 是 Y 的组成部分或步骤（整体-部分关系）。
    典型模式：Subtask/Component PART-OF Task/Method/Material。
    （3）HYPONYM-OF
    含义：X 是 Y 的下位类别（X 是 Y 的一种，“is-a” 关系）。
    典型模式：Term HYPONYM-OF MoreGeneralTerm。
    （4）CONJUNCTION
    含义：X 与 Y 并列出现（协同使用、联合方法/特征），通常由 “and / or” 等连接。
    典型模式：两个方法或两个术语之间的“and”关系。
    （5）FEATURE-OF
    含义：X 是 Y 的一个属性/特征（Y 拥有特征 X）。
    典型模式：Property FEATURE-OF Concept。
    （6）EVALUATE-FOR
    含义：X 被用来评估 Y 的效果/性能（评测关系）。
    典型模式：Dataset/Benchmark EVALUATE-FOR Method/Model。
    （7）COMPARE 
    含义：表示对比关系，两个方法/系统/模型之间被显式地拿来比较性能或性质。
  # 2.输入：待抽取的样本（字符串）。
  # 3.输出：实体和关系抽取结果，采用json格式，包含nodes字段和edges字段，分别对应实体和关系抽取结果。nodes字段是一个字典，键为实体提及，值为一个字典，有一个键type、其值为实体类型。edges字段是一个列表，每一个元素是一个三元组（列表），分别对应头实体提及、关系类型和尾实体提及。
    # 4.输入输出示例
    （1）示例1：输入为"Human action recognition from well-segmented 3D skeleton data has been intensively studied and attracting an increasing attention ."
    输出为{"nodes": {"Human_action_recognition": {"type": "Task"}, "well-segmented_3D_skeleton_data": {"type": "Material"}}, "edges": [["well-segmented_3D_skeleton_data", "USED-FOR", "Human_action_recognition"]]}
    （2）示例2：输入为"Many of the resources used are derived from data created by human beings out of an NLP context , especially regarding MT and reference translations ."
    输出为{"nodes": {"NLP": {"type": "Task"}, "MT": {"type": "Task"}, "reference_translations": {"type": "Task"}}, "edges": [["MT", "HYPONYM-OF", "NLP"], ["MT", "CONJUNCTION", "reference_translations"], ["reference_translations", "HYPONYM-OF", "NLP"]]}
    # 以下为测试样本，请输出json（字符串），不要输出多余的内容。确保输出的标签在给出的7种实体标签与6种关系标签之中！
'''


in_path = "data/scierc/test_graph_serialized.jsonl"
out_path = "data/scierc/naive_test_llm_answer.jsonl"
samplelist = read_jsonl(in_path)

# API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-mojjssgddpnutthpptliaoxqwquddecefskykervlyhzpjdd"  # 请替换为您的实际API密钥

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

for i, sample in enumerate(samplelist):
    if i + 1 < 0:
        continue
    print(f"样本{i +1}:{sample["sentences"]}")
    # 请求数据 - 修改为使用Qwen3-8B模型
    data = {
        "model": "Qwen/Qwen3-8B",  # 根据实际模型名称调整
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": sample["sentences"]}
        ]
    }
    try:
        # 发送POST请求
        response = requests.post(API_URL, headers=headers, json=data)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 提取并打印助手的回复
        answer = result['choices'][0]['message']['content']
        sample_new = deepcopy(sample)
        sample_new["answer"] = answer
        print(answer)
        write_jsonl(sample_new, out_path)
        
    except requests.exceptions.RequestException as e:
        print(f"请求出错：{e}")
    except KeyError as e:
        print(f"响应解析出错：{e}")
        print(f"完整响应：{response.text}")
    except Exception as e:
        print(f"其他错误：{e}")