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
  确保输出的标签在给出的4种实体标签与5种关系标签之中！
  ## 1.1 实体标签（4种）
    （1）peop：指人名或具体的人物，如政客、科学家、普通个人等。
    例：Reagan、Michael_D._Papagiannis、Bill_Gordon。
    （2）org：指组织机构，包括公司、大学、政府机构、协会、军队等。
    例：AP、Boston_University、United_Federation_of_Teachers、Navy。
    （3）loc：指地理位置：国家、城市、地区、建筑物、公园等实体。
    例：Italy、Jerusalem、Hot_Springs_National_Park、White_House。
    （4）other：其他类型的实体，不是人、组织或地点，但在语义上仍然是“名词性实体”，如时间、事件、数量表达等。
    例：Palestinians（作为群体）、Cuban_missile_crisis、100_million_years、Dec._16_,。
  ## 1.2 关系标签（5种）
    （1）work_for
    含义：人物为某组织工作（从属/雇佣关系）。
    例子：Wright work_for University_of_Texas，Michael_Coats work_for Navy。
    典型语义：X 是 Y 的员工、成员、职员等。
    （2）orgbased_in
    含义：组织的“总部/所在位置”在某地。
    例子：AP orgbased_in Italy，Congress orgbased_in Washington，University_of_Virginia orgbased_in Charlottesville。
    典型语义：公司总部位于某城、机构位于某地。
    （3）located_in
    含义：地点或实体位于另一地点内部。
    例子：PERUGIA located_in Italy，Aguadilla located_in Puerto_Rico，Ontario located_in California。
    典型语义：城市在州/国家里，公园在州内，小地名从属于大地名。
    （4）live_in
    含义：人物居住在某地。
    例子：Reagan live_in America，Yves_Fortier live_in Canada，Bill_Gordon live_in Bingham_County。
    典型语义：X 住在/来自 Y，长期居住关系而非短期访问。
    （5）kill
    含义：杀害关系，通常是 Person/Organization → Person（施事者杀害受事者），或事件相关。
    典型语义：X 杀害了 Y（如“the rebels killed 10 soldiers” 中，rebels kill soldiers）
  # 2.输入：待抽取的样本（字符串）。
  # 3.输出：实体和关系抽取结果（字符串），采用专门设计的序列化格式。
  ## 3.1 序列化输出说明：（1）采用dfs图遍历方法，实体对应图中的节点（节点的命名为实体提及）、关系对应图中的有向边（从头实体到尾实体，有向边的命名为关系类型）。
  （2）形式上采用括号嵌套（中括号[]）的方法，用冒号:说明类型，不同节点或边之间用一个空格进行分隔。如果一个实体包含多个token，每两个token之间用下划线_相连。
  （3）扩展节点时，优先级更高的节点为在文本中更靠前的实体提及。
  （4）采用反向边来表示从尾实体到头实体的边（反向边的命名为在关系类型后加-rev），正向边和反向边只读取其中之一。
  （5）若在扩展节点的过程中访问到已扩展的节点，用REF来表示、不再继续展开。
  （6）若实体抽取结果为空，只输出根节点[ROOT]。
  ## 3.2 序列化输出示例：
  （1）输入文本为text = "Locations containing suitable federally owned land were listed as : Fort Wainwright annex , Fairbanks , Alaska ;"
  （2）实体关系标注为G = {
        "nodes": {"Fort_Wainwright_annex": {"type": "loc"}, "Fairbanks": {"type": "loc"}, "Alaska": {"type": "loc"}}, 
        "edges": [["Fort_Wainwright_annex", "located_in", "Fairbanks"], ["Fort_Wainwright_annex", "located_in", "Alaska"], ["Fairbanks", "located_in", "Alaska"]]
    }
    （3）序列化之后的输出为: [ROOT [Fairbanks:loc located_in [Alaska:loc located_in-rev [Fort_Wainwright_annex:loc located_in [Fairbanks:REF]]]]]
    # 4.输入输出示例
    （1）示例1：输入为"Dancers of Moscow 's Bolshoi Ballet in Moscow and Leningrad 's Kirov Ballet , together with opera singers from the Armenian capital of Yerevan , joined U.S. sopranos June Anderson and Carol Vaness and British dancers and singers .",
    输出为"[ROOT [Moscow:loc orgbased_in-rev [Bolshoi_Ballet:org]] [Leningrad:loc orgbased_in-rev [Kirov_Ballet:org]] [Armenian:other] [Yerevan:loc] [U.S.:loc live_in-rev [June_Anderson:peop] live_in-rev [Carol_Vaness:peop]] [British:other]]"
    （2）示例2：输入为"Iowa Republican Terry Branstad was installed as new chairman of the bipartisan National Governors ' Association , and Democrat Booth Gardner of Washington was selected to serve as vice to follow Branstad as chairman in a year.",
    输出为"[ROOT [Iowa:loc live_in-rev [Branstad:peop work_for [National_Governors_'_Association:org work_for-rev [Terry_Branstad:peop live_in [Iowa:REF]] work_for-rev [Booth_Gardner:peop live_in [Washington:loc]]]]]]",
    # 以下为测试样本，请输出序列化后的测试结果（字符串），不要输出多余的内容。确保输出的标签在给出的4种实体标签与5种关系标签之中！
'''


in_path = "data/conll04/test_graph_serialized.jsonl"
out_path = "data/CoNLL04/test_llm_answer.jsonl"
samplelist = read_jsonl(in_path)

# API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-vfsnrgklnukgzyegbldlymrdmaegtlqmreqmiqctltexxrkt"  # 请替换为您的实际API密钥

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

for i, sample in enumerate(samplelist):
    if i + 1 < 270:
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

        
    except requests.exceptions.RequestException as e:
        print(f"请求出错：{e}")
    except KeyError as e:
        print(f"响应解析出错：{e}")
        print(f"完整响应：{response.text}")
    except Exception as e:
        print(f"其他错误：{e}")