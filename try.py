import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from transformers import AutoTokenizer

MODEL_PATH = "/data/wengxiaolong/huggingface/Qwen2.5-7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True
)

debug_log_dir = "/data/wengxiaolong/zhouyuanyun/LlamaFactory/tmp"
os.makedirs(debug_log_dir, exist_ok=True)
debug_log_file = os.path.join(debug_log_dir, f"llamafactory_debug_rank_{os.getenv('LOCAL_RANK', '0')}.log")
with open(debug_log_file, "a") as f:
    f.write(f"[DEBUG workflow] LOCAL_RANK: {os.getenv('LOCAL_RANK')}\n")
    f.write(f"[DEBUG workflow] Tokenizer (after loading): {tokenizer.padding_side}\n\n")


    