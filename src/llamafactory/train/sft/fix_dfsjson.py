import re
import json


def fix_json_string(raw_output: str) -> str:
    """
    修复LLM输出的JSON字符串，使其符合dfsjson格式要求。
    
    格式要求：
    - 最外层是JSON列表 [...]
    - 每个元素是对象 {span, type, targets?, relation?, ref?}
    - targets中包含{relation, span, type}或{relation, ref}
    - 末尾应为 }] 组合
    """
    
    # 1. 提取JSON部分（去除markdown代码块等）
    json_str = extract_json_part(raw_output)
    
    # 2. 修复常见问题
    json_str = remove_trailing_comma(json_str)          # 移除多余逗号
    json_str = fix_single_quotes(json_str)               # 单引号转双引号
    json_str = fix_unquoted_keys(json_str)               # 修复未加引号的key
    json_str = fix_bracket_mismatch(json_str)            # 修复括号不匹配
    json_str = fix_ending_brackets(json_str)              # 修复末尾括号
    
    return json_str


def extract_json_part(text: str) -> str:
    """从LLM输出中提取JSON部分"""
    # 去除markdown代码块标记
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    
    # 尝试找到JSON数组的起始和结束位置
    json_match = re.search(r'\[[\s\S]*', text)
    if json_match:
        start_pos = json_match.start()
        text = text[start_pos:]
    
    return text.strip()


def remove_trailing_comma(json_str: str) -> str:
    """移除JSON中结尾的多余逗号，如 [1,2,3,] -> [1,2,3]"""
    # 移除 } 或 ] 前的多余逗号
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    return json_str


def fix_single_quotes(json_str: str) -> str:
    """将单引号替换为双引号（处理LLM常用单引号的问题）"""
    result = []
    i = 0
    in_string = False
    
    while i < len(json_str):
        char = json_str[i]
        
        if char == '"' and (i == 0 or json_str[i-1] != '\\'):
            in_string = not in_string
            result.append(char)
        elif char == "'" and not in_string:
            result.append('"')
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def fix_unquoted_keys(json_str: str) -> str:
    """修复未加引号的JSON key"""
    # 匹配 key: value 模式，key未加引号的情况
    # 但要排除已经加引号的和冒号在引号内的情况
    def replace_key(match):
        key = match.group(1)
        # 再次检查是否在字符串内
        prefix = match.group(0)[:match.start() - len(match.group(0))]
        if prefix.count('"') % 2 == 0:  # 引号数量为偶数，当前不在字符串内
            return f'"{key}":'
        return match.group(0)
    
    # 匹配 {key: 或 ,key: 模式（key是字母开头）
    json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', replace_key, json_str)
    return json_str


def fix_bracket_mismatch(json_str: str) -> str:
    """修复括号不匹配问题"""
    # 使用栈来跟踪括号
    stack = []
    result = []
    i = 0
    
    while i < len(json_str):
        char = json_str[i]
        
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


def fix_ending_brackets(json_str: str) -> str:
    """
    修复末尾括号问题
    dfsjson格式要求以 }] 结尾
    """
    json_str = json_str.rstrip()
    
    if not json_str:
        return "[]"
    
    # 如果已经是合法的JSON，直接返回
    try:
        json.loads(json_str)
        return json_str
    except:
        pass
    
    # 暴力尝试修复：从后往前尝试不同的括号组合
    # dfsjson合法的末尾只能是 ] 或 }] 或 }]]
    for suffix_len in range(1, min(len(json_str) + 1, 10)):
        suffix = json_str[-suffix_len:]
        main = json_str[:-suffix_len]
        
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
            candidate = json_str.rstrip() + '}' * num_close + ']' * num_end
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return candidate
            except:
                pass
    
    # 尝试从后往前删除多余的字符直到能解析
    for i in range(len(json_str)):
        truncated = json_str[:-i] if i > 0 else json_str
        truncated = truncated.rstrip()
        if not truncated.endswith(']') and not truncated.endswith('}'):
            truncated += ']'
        try:
            parsed = json.loads(truncated)
            if isinstance(parsed, list):
                return truncated
        except:
            pass
    
    return json_str


def validate_and_parse(json_str: str) -> tuple[bool, any, str]:
    """
    验证并解析JSON字符串
    
    Returns:
        (是否成功, 解析结果, 错误信息)
    """
    try:
        parsed = json.loads(json_str)
        return True, parsed, ""
    except json.JSONDecodeError as e:
        return False, None, str(e)


# 使用示例
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        # 缺少末尾括号
        '[{"span": "test", "type": "Generic"}',
        # 括号不完整
        '[{"span": "test", "type": "Generic", "targets": [{"relation": "UsedFor"',
        # 多余逗号
        '[{"span": "test", "type": "Generic",}, {"span": "test2", "type": "Method"}]',
        # 单引号
        "[{'span': 'test', 'type': 'Generic'}]",

         '[{\"span\": \"algorithm\", \"type\": \"Generic\", \"targets\": [{\"relation\": \"UsedFor\", \"span\": \"computing optical flow , shape , motion , lighting , and albedo\", \"type\": \"Task\"}]}, {\"span\": \"image sequence\", \"type\": \"Material\", \"targets\": [{\"relation\": \"UsedFor\", \"ref\": \"algorithm\"}]}, {\"span\": \"rigidly-moving Lambertian object\", \"type\": \"Material\", \"targets\": [{\"relation\": \"FeatureOf\", \"ref\": \"image sequence\"}]}, {\"span\": \"distant illumination\", \"type\": \"OtherScientificTerm\", \"targets\": [{\"relation\": \"FeatureOf\", \"ref\": \"rigidly-moving Lambertian object\"}]]}]',

         '[{\"span\": \"problem\", \"type\": \"Generic\"}, {\"span\": \"motion\", \"type\": \"Material\", \"targets\": [{\"relation\": \"Conjunction\", \"span\": \"multi-view stereo\", \"type\": \"Material\", \"targets\": [{\"relation\": \"Conjunction\", \"span\": \"photo-metric stereo\", \"type\": \"Material\"}]}}]',

         '[{\"span\": \"algorithm\", \"type\": \"Generic\"}, {\"span\": \"estimating affine camera parameters , illumination , shape , and albedo\", \"type\": \"Method\", \"targets\": [{\"relation\": \"UsedFor\", \"ref\": \"algorithm\"}]',

         '[{\"span\": \"videos of hand-held objects\", \"type\": \"Material\"}]]'
    ]
    
    for i, test in enumerate(test_cases):
        print(f"测试用例 {i+1}:")
        print(f"  输入: {test[:60]}...")
        fixed = fix_json_string(test)
        print(f"  修复: {fixed[:60]}...")
        success, parsed, error = validate_and_parse(fixed)
        print(f"  解析: {'成功' if success else '失败'} - {error if not success else ''}")
        print()