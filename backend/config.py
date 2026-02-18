# backend/config.py
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# API 配置
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-plus"  # 可选: qwen-max, qwen-turbo

# 文件路径配置
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "output"
DATA_FOLDER = BASE_DIR / "data"
FORMATTED_TEXT_FOLDER = OUTPUT_FOLDER / "formatted_text"
JSON_FOLDER = OUTPUT_FOLDER / "json"

# 创建必要的文件夹
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, FORMATTED_TEXT_FOLDER, JSON_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# 支持的文件格式
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# 题目生成配置
DEFAULT_NUM_QUESTIONS = 15
MAX_NUM_QUESTIONS = 50
MIN_NUM_QUESTIONS = 5