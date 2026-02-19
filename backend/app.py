# backend/app.py
import dashscope
from dashscope import Generation  # 明确导入需要的类
from http import HTTPStatus

from question_generator import DashScopeQuestionGenerator
from chapters_manager import ChaptersManager
import os
import config
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from pathlib import Path

from question_generator import DashScopeQuestionGenerator
from chapters_manager import ChaptersManager
import config


app = Flask(__name__)
CORS(app)

# 初始化
if not config.QWEN_API_KEY:
    print("⚠️ 警告: 未设置 QWEN_API_KEY 环境变量")
    print("请在 backend/.env 文件中设置: QWEN_API_KEY=your-key")

generator = DashScopeQuestionGenerator(api_key=config.QWEN_API_KEY)
chapters_manager = ChaptersManager(config.BASE_DIR / 'chapters.json')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """返回 agent.html"""
    return send_from_directory(config.BASE_DIR, 'agent.html')

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "api_key_configured": bool(config.QWEN_API_KEY)
    })

@app.route('/api/generate', methods=['POST'])
def generate_questions():
    """生成题目的 API 端点"""
    
    # 检查文件
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "error": "没有上传文件"
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "文件名为空"
        }), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": f"不支持的文件格式，仅支持: {', '.join(config.ALLOWED_EXTENSIONS)}"
        }), 400
    
    # 获取参数
    chapter_name = request.form.get('chapter_name', 'chapter')
    chapter_name = secure_filename(chapter_name)
    
    chapter_title = request.form.get('chapter_title', '')
    chapter_description = request.form.get('chapter_description', '')
    week = request.form.get('week', '')
    instructor = request.form.get('instructor', 'BAEG Gyeong Hun')
    date = request.form.get('date', '')
    
    try:
        num_questions = int(request.form.get('num_questions', config.DEFAULT_NUM_QUESTIONS))
        num_questions = max(config.MIN_NUM_QUESTIONS, 
                           min(num_questions, config.MAX_NUM_QUESTIONS))
    except ValueError:
        num_questions = config.DEFAULT_NUM_QUESTIONS
    
    # 保存上传的文件
    filename = secure_filename(file.filename)
    upload_path = config.UPLOAD_FOLDER / filename
    file.save(str(upload_path))
    
    try:
        # 处理文件
        results = generator.process_file(
            file_path=str(upload_path),
            chapter_name=chapter_name,
            num_questions=num_questions
        )
        
        # 清理上传的文件
        os.remove(upload_path)
        
        if results["success"]:
            json_file_path = results["json_path"]
            
            # 生成章节配置
            chapter_config = chapters_manager.generate_chapter_config(
                chapter_id=chapter_name,
                title=chapter_title or f"Chapter: {chapter_name}",
                description=chapter_description,
                week=week or chapters_manager.get_next_week_number(),
                instructor=instructor,
                date=date,
                json_file_path=json_file_path
            )
            
            return jsonify({
                "success": True,
                "message": results["message"],
                "question_count": results["question_count"],
                "download_json_url": f"/api/download/json/{chapter_name}.json",
                "download_text_url": f"/api/download/text/{chapter_name}_formatted.txt",
                "json_filename": f"{chapter_name}.json",
                "chapter_config": chapter_config,
                "chapter_exists": chapters_manager.chapter_exists(chapter_name)
            })
        else:
            return jsonify({
                "success": False,
                "error": results["message"]
            }), 500
    
    except Exception as e:
        if upload_path.exists():
            os.remove(upload_path)
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/download/json/<filename>')
def download_json(filename):
    """下载生成的 JSON 文件"""
    return send_from_directory(config.JSON_FOLDER, filename, as_attachment=True)

@app.route('/api/download/text/<filename>')
def download_text(filename):
    """下载格式化的文本文件"""
    return send_from_directory(config.FORMATTED_TEXT_FOLDER, filename, as_attachment=True)

@app.route('/api/copy-to-data/<filename>', methods=['POST'])
def copy_to_data(filename):
    """将生成的 JSON 文件复制到 data 文件夹"""
    try:
        import shutil
        src = config.JSON_FOLDER / filename
        dst = config.DATA_FOLDER / filename
        
        if not src.exists():
            return jsonify({
                "success": False,
                "error": "源文件不存在"
            }), 404
        
        shutil.copy2(src, dst)
        
        return jsonify({
            "success": True,
            "message": f"文件已复制到 data/{filename}"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chapters/add', methods=['POST'])
def add_chapter_to_config():
    """添加章节到 chapters.json"""
    try:
        data = request.json
        chapter_config = data.get('chapter_config')
        
        if not chapter_config:
            return jsonify({
                "success": False,
                "error": "缺少章节配置数据"
            }), 400
        
        # 添加或更新章节
        action = chapters_manager.add_or_update_chapter(chapter_config)
        
        return jsonify({
            "success": True,
            "action": action,
            "message": f"章节已{'更新' if action == 'updated' else '添加'}到 chapters.json"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    """获取所有 DashScope 模型"""
    try:
        response = Model.list()
        
        if response.status_code == HTTPStatus.OK:
            models = [model.model_id for model in response.data]
            return jsonify({
                "success": True,
                "data": models
            }), 200
        else:
            raise Exception(f"API 调用失败: {response.code} - {response.message}")
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 启动题目生成 Agent 服务器...")
    print(f"📁 上传文件夹: {config.UPLOAD_FOLDER}")
    print(f"📁 输出文件夹: {config.OUTPUT_FOLDER}")
    print(f"🤖 API Key 已配置: {bool(config.QWEN_API_KEY)}")
    app.run(debug=True, host='0.0.0.0', port=5000)