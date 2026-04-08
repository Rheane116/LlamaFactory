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
  确保输出的标签在给出的7种实体标签与6种关系标签之中！
  ## 1.1 实体标签（7种）
（1）PER : 指个人，包括全名、名字、姓氏、昵称等。注意，人称代词也需标注为PER。例如："Jessica Lynch", "George W. Bush", "Osama bin Laden","we"。
（2）ORG : 指有组织的团体，如公司、政府机构、军队单位、政党、体育团队、学校等。例如："CNN", "Pentagon", "Republican Guard", "Microsoft", "Al Qaeda"。
（3）GPE : 指地理政治实体，即具有明确边界和政府的国家、城市、省份、州等。例如："Iraq", "Baghdad", "United States", "California", "West Bank"。
（4）LOC : 指地理位置，通常是非政治性的地点，如山、河、海、沙漠、地区等。例如："Persian Gulf", "Tigris River", "Mount Everest"。
（5）FAC : 指人造的设施或建筑，如机场、桥梁、医院、学校、博物馆、军事基地等。例如："Saddam International Airport", "White House", "Brooklyn Bridge", "Gracie Mansion"。
（6）VEH : 指交通工具，包括汽车、飞机、轮船、火箭、直升机等。例如："Blackhawk helicopter", "USS Abraham Lincoln", "taxicab", "M1 Abrams tank"。
（7）WEA : 指武器，包括枪、导弹、炸弹、坦克等军事装备。例如："AK-47", "Tomahawk missiles", "grenades", "nuclear weapons"。
 ## 1.2 关系标签（6种）
（1）ORG-AFF : 组织-从属关系。表示一个实体（通常是PER）属于或服务于某个组织。例如(Ariel Sharon, Israel)，即沙龙是以色列的官员。
（2）PER-SOC: 个人-社交关系。表示两个人之间存在家庭、朋友或其他社会关系。例如(George W. Bush, Putin)，他们是朋友或同行。
（3）PHYS : 物理关系。表示一个实体位于另一个实体的位置（如住在某城市、死在某地）或有物理上的交互。例如(Hamid Karzai, Afghanistan)，即卡尔扎伊在阿富汗。
（4）ART: 人造物关系。表示一个人拥有、使用或控制一个人造物（如武器、车辆）。例如(Qusay, rocket)，即库赛使用火箭。
（5）GEN-AFF: 一般从属关系。表示一个实体属于某个更大的、通常是地理或民族的群体。例如(Saddam Hussein, Baath Party)，即萨达姆属于复兴党。
（6）PART-WHOLE : 部分-整体关系。表示一个实体是另一个实体的组成部分。例如(Israel, Middle East)，即以色列是中东的一部分。也常用于地点之间的包含关系，如城市属于国家。
  # 2.输入：待抽取的样本（字符串）。
  # 3.输出：实体和关系抽取结果（字符串），采用专门设计的序列化格式。
  ## 3.1 序列化输出说明：（1）采用dfs图遍历方法，实体对应图中的节点（节点的命名为实体提及）、关系对应图中的有向边（从头实体到尾实体，有向边的命名为关系类型）。
  （2）形式上采用括号嵌套（中括号[]）的方法，用冒号:说明类型，不同节点或边之间用一个空格进行分隔。如果一个实体包含多个token，每两个token之间用下划线_相连。
  （3）扩展节点时，优先级更高的节点为在文本中更靠前的实体提及。
  （4）采用反向边来表示从尾实体到头实体的边（反向边的命名为在关系类型后加-rev），正向边和反向边只读取其中之一。
  （5）若在扩展节点的过程中访问到已扩展的节点，用REF来表示、不再继续展开。
  （6）若实体抽取结果为空，只输出根节点[ROOT]。
  ## 3.2 序列化输出示例：
  （1）输入文本为text = "Holding a framed picture of her son , serving with the Army 's 3rd Infantry Division in Iraq , she said she did n't know whether he was dead or alive . "
  （2）实体关系标注为G = {
        "nodes": {"her": {"type": "PER"}, "son": {"type": "PER"}, "Army": {"type": "ORG"}, "3rd_Infantry_Division": {"type": "ORG"}, "Iraq": {"type": "GPE"}, "she": {"type": "PER"}, "he": {"type": "PER"}}, 
        "edges": [["her", "PER-SOC", "son"], ["son", "ORG-AFF", "3rd_Infantry_Division"], ["son", "PHYS", "Iraq"], ["3rd_Infantry_Division", "GEN-AFF", "Iraq"], ["3rd_Infantry_Division", "PART-WHOLE", "Army"]]
    }
    （3）序列化之后的输出为：[ROOT [her:PER PER-SOC [son:PER PHYS [Iraq:GPE GEN-AFF-rev [3rd_Infantry_Division:ORG ORG-AFF-rev [son:REF] PART-WHOLE [Army:ORG]]]]] [he:PER] [she:PER]]
    # 4.输入输出示例
    （1）示例1：输入为"there is also intelligence , officials say , suggesting republican guard units have been issued artillery shells containing chemical agents .",
    输出为"[ROOT [officials:PER] [republican_guard:ORG ORG-AFF-rev [units:PER ART [shells:WEA]]] [artillery:WEA] [agents:WEA]]"
    （2）示例2：输入为"a source tell us enron is considering suing its own investment bankers for giving it bad financial advice .",
    输出为"[ROOT [source:PER] [us:ORG] [enron:ORG] [its:ORG ORG-AFF-rev [bankers:ORG]] [it:ORG] [own:ORG]]",
    # 以下为测试样本，请输出序列化后的测试结果（字符串），不要输出多余的内容。确保输出的标签在给出的7种实体标签与6种关系标签之中！
'''

prompt = '''
  你的任务是做实体关系联合抽取。
  # 1.任务schema
  确保输出的标签在给出的7种实体标签与6种关系标签之中！
  ## 1.1 实体标签（7种）
（1）PER : 指个人，包括全名、名字、姓氏、昵称等。注意，人称代词也需标注为PER。例如："Jessica Lynch", "George W. Bush", "Osama bin Laden","we"。
（2）ORG : 指有组织的团体，如公司、政府机构、军队单位、政党、体育团队、学校等。例如："CNN", "Pentagon", "Republican Guard", "Microsoft", "Al Qaeda"。
（3）GPE : 指地理政治实体，即具有明确边界和政府的国家、城市、省份、州等。例如："Iraq", "Baghdad", "United States", "California", "West Bank"。
（4）LOC : 指地理位置，通常是非政治性的地点，如山、河、海、沙漠、地区等。例如："Persian Gulf", "Tigris River", "Mount Everest"。
（5）FAC : 指人造的设施或建筑，如机场、桥梁、医院、学校、博物馆、军事基地等。例如："Saddam International Airport", "White House", "Brooklyn Bridge", "Gracie Mansion"。
（6）VEH : 指交通工具，包括汽车、飞机、轮船、火箭、直升机等。例如："Blackhawk helicopter", "USS Abraham Lincoln", "taxicab", "M1 Abrams tank"。
（7）WEA : 指武器，包括枪、导弹、炸弹、坦克等军事装备。例如："AK-47", "Tomahawk missiles", "grenades", "nuclear weapons"。
 ## 1.2 关系标签（6种）
（1）ORG-AFF : 组织-从属关系。表示一个实体（通常是PER）属于或服务于某个组织。例如(Ariel Sharon, Israel)，即沙龙是以色列的官员。
（2）PER-SOC: 个人-社交关系。表示两个人之间存在家庭、朋友或其他社会关系。例如(George W. Bush, Putin)，他们是朋友或同行。
（3）PHYS : 物理关系。表示一个实体位于另一个实体的位置（如住在某城市、死在某地）或有物理上的交互。例如(Hamid Karzai, Afghanistan)，即卡尔扎伊在阿富汗。
（4）ART: 人造物关系。表示一个人拥有、使用或控制一个人造物（如武器、车辆）。例如(Qusay, rocket)，即库赛使用火箭。
（5）GEN-AFF: 一般从属关系。表示一个实体属于某个更大的、通常是地理或民族的群体。例如(Saddam Hussein, Baath Party)，即萨达姆属于复兴党。
（6）PART-WHOLE : 部分-整体关系。表示一个实体是另一个实体的组成部分。例如(Israel, Middle East)，即以色列是中东的一部分。也常用于地点之间的包含关系，如城市属于国家。
  # 2.输入：待抽取的样本（字符串）。
  # 3.输出：实体和关系抽取结果（字符串），采用专门设计的序列化格式。
  ## 3.1 序列化输出说明：（1）采用dfs图遍历方法，实体对应图中的节点（节点的命名为实体提及）、关系对应图中的有向边（从头实体到尾实体，有向边的命名为关系类型）。
  （2）形式上采用括号嵌套（中括号[]）的方法，用冒号:说明类型，不同节点或边之间用一个空格进行分隔。如果一个实体包含多个token，每两个token之间用下划线_相连。
  （3）扩展节点时，优先级更高的节点为在文本中更靠前的实体提及。
  （4）采用反向边来表示从尾实体到头实体的边（反向边的命名为在关系类型后加-rev），正向边和反向边只读取其中之一。
  （5）若在扩展节点的过程中访问到已扩展的节点，用REF来表示、不再继续展开。
  （6）若实体抽取结果为空，只输出根节点[ROOT]。
  ## 3.2 序列化输出示例：
  （1）输入文本为text = "Holding a framed picture of her son , serving with the Army 's 3rd Infantry Division in Iraq , she said she did n't know whether he was dead or alive . "
  （2）实体关系标注为G = {
        "nodes": {"her": {"type": "PER"}, "son": {"type": "PER"}, "Army": {"type": "ORG"}, "3rd_Infantry_Division": {"type": "ORG"}, "Iraq": {"type": "GPE"}, "she": {"type": "PER"}, "he": {"type": "PER"}}, 
        "edges": [["her", "PER-SOC", "son"], ["son", "ORG-AFF", "3rd_Infantry_Division"], ["son", "PHYS", "Iraq"], ["3rd_Infantry_Division", "GEN-AFF", "Iraq"], ["3rd_Infantry_Division", "PART-WHOLE", "Army"]]
    }
    （3）序列化之后的输出为：[ROOT [her:PER PER-SOC [son:PER PHYS [Iraq:GPE GEN-AFF-rev [3rd_Infantry_Division:ORG ORG-AFF-rev [son:REF] PART-WHOLE [Army:ORG]]]]] [he:PER] [she:PER]]
    # 4.输入输出示例
    （1）示例1：输入为"there is also intelligence , officials say , suggesting republican guard units have been issued artillery shells containing chemical agents .",
    输出为"[ROOT [officials:PER] [republican_guard:ORG ORG-AFF-rev [units:PER ART [shells:WEA]]] [artillery:WEA] [agents:WEA]]"
    （2）示例2：输入为"a source tell us enron is considering suing its own investment bankers for giving it bad financial advice .",
    输出为"[ROOT [source:PER] [us:ORG] [enron:ORG] [its:ORG ORG-AFF-rev [bankers:ORG]] [it:ORG] [own:ORG]]",
    # 以下为测试样本，请输出序列化后的测试结果（字符串），不要输出多余的内容。确保输出的标签在给出的7种实体标签与6种关系标签之中！
'''

in_path = "data/ACE2005/test_graph_serialized.jsonl"
out_path = "data/ACE2005/test_llm_answer.jsonl"
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
    if i + 1 < 11:
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