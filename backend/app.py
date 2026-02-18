# backend/app.py
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os

# 选择你想用的生成器
# from question_generator import QuestionGenerator  # 原始文本版
from question_generator_multimodal import MultimodalQuestionGenerator  # 多模态版本
# from question_generator_dashscope import DashScopeQuestionGenerator  # DashScope版本

import config

app = Flask(__name__, static_folder='../static')
CORS(app)

# 初始化生成器（多模态版本）
generator = MultimodalQuestionGenerator(
    api_key=config.QWEN_API_KEY,
    base_url=config.QWEN_BASE_URL
)

@app.route('/api/generate', methods=['POST'])
def generate_questions():
    """生成题目 API"""
    
    # ... (前面的验证代码相同) ...
    
    try:
        # 使用多模态处理
        formatted_text = generator.process_file(
            file_path=str(upload_path),
            chapter_name=chapter_name,
            num_questions=num_questions,
            use_vision=True  # 启用视觉分析
        )
        
        # 转换为 JSON 并保存
        # ... (后续代码相同) ...
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500