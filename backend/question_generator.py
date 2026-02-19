# backend/question_generator.py
import dashscope
from dashscope import MultiModalConversation  # 显式导入多模态类
from dashscope import Generation  # 显式导入 Generation 类
from http import HTTPStatus
import os
import re
import json
from pathlib import Path

class DashScopeQuestionGenerator:
    def __init__(self, api_key):
        dashscope.api_key = api_key
        self.vision_model = 'qwen-vl-max'
        self.text_model = 'qwen-plus'
    
    def generate_questions_from_file(self, file_path, num_questions=15, chapter_info=""):
        """
        直接上传文件给 Qwen-VL 生成题目
        支持 PDF、图片等多模态内容
        """
        
        file_ext = Path(file_path).suffix.lower()
        
        # 如果是 PDF 或包含图片的文档，使用 VL 模型
        if file_ext in ['.pdf', '.jpg', '.jpeg', '.png']:
            return self._generate_with_vision_model(file_path, num_questions, chapter_info)
        
        # 纯文本文件，使用普通模型
        else:
            return self._generate_with_text_model(file_path, num_questions, chapter_info)
    
    def _generate_with_vision_model(self, file_path, num_questions, chapter_info):
        """使用多模态模型（支持图片分析）"""
        
        print(f"📤 正在使用多模态模型分析文件...")
        
        prompt = f"""请基于上传的文件内容生成 {num_questions} 道医学史选择题。

章节信息：{chapter_info if chapter_info else "医学史相关内容"}

请仔细分析文件中的所有内容，包括：
- 文本说明
- 图片（如历史人物画像、医学工具、解剖图、时间线等）
- 图表和示意图

如果图片中包含重要信息，请在题目中体现。例如：
- "图中展示的医学工具是？"
- "这位历史人物是谁？"
- "图示的解剖结构属于？"

输出格式（严格遵循）：
题目：[题目文本]
A. [选项A文本] | [选项A的详细解析]
B. [选项B文本] | [选项B的详细解析]
C. [选项C文本] | [选项C的详细解析，如果是正确答案在末尾加 ✓]
D. [选项D文本] | [选项D的详细解析]
解析：[易混淆点说明和答题技巧]

---

重要要求：
1. 每个选项都必须有详细解析（为什么对/为什么错）
2. 正确答案的解析末尾必须有空格+✓符号
3. 题目要有深度，考察理解而非记忆
4. 题目之间用三个短横线 --- 分隔
5. 不要添加题目编号

现在开始生成 {num_questions} 道题目："""

        messages = [
            {
                "role": "system",
                "content": [
                    {"text": "你是一个专业的医学史教育专家，擅长从文档和图片中提取信息并生成高质量的选择题。"}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"file": f"file://{os.path.abspath(file_path)}"},
                    {"text": prompt}
                ]
            }
        ]
        
        try:
            response = MultiModalConversation.call(
                model=self.vision_model,
                messages=messages
            )
            
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content[0]['text']
            else:
                raise Exception(f"API 调用失败: {response.code} - {response.message}")
        
        except Exception as e:
            raise Exception(f"多模态模型调用失败: {str(e)}")
    
    # question_generator.py
    # 示例：其他函数不变
    def _generate_with_vision_model(self, file_path, num_questions, chapter_info):
        """使用多模态模型（分析文件）"""
        print(f"📤 正在使用多模态模型分析文件: {file_path}")
        # Prompt 内容
        prompt = f"""请基于上传的文件生成 {num_questions} 道医学史选择题。

        你在这里将协助整理pdf中相应的知识点，并出成选择题
        我会发给你多个pdf，你需要针对每个pdf都出选择题
        类似于名人干了什么，什么研究成果，有什么影响，有哪些疾病，
        医学工具之类的，因为都是考的选择题，
        所以我需要范围广，而不是研究的深
        （没有论述题，考试答案可以直接从我发你的pdf上获取）

        **严格输出格式如下**：
        题目：[题目文本]
        A. [选项A] | [解析]
        B. [选项B] | [解析]
        C. [选项C] | [解析且结尾加 ✓]
        D. [选项D] | [解析]
        解析：[解析内容]
        --- """
        messages = [
            {
                "role": "user",
                "content": [
                    {"file": f"file://{os.path.abspath(file_path)}"},
                    {"text": prompt}
                ]
            }
        ]
        
        try:
            response = MultiModalConversation.call(
                model=self.vision_model,
                messages=messages
            )
            
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message['content']['text']
            else:
                raise Exception(f"API 调用失败: {response.code} - {response.message}")
        
        except Exception as e:
            raise Exception(f"多模态模型调用失败: {str(e)}")
    
    
    
    def _extract_text_from_file(self, file_path):
        """从文件提取纯文本"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext in ['.docx', '.doc']:
            try:
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except ImportError:
                raise Exception("需要安装 python-docx: pip install python-docx")
        
        else:
            raise ValueError(f"不支持的文本文件格式: {ext}")
    
    def parse_formatted_text_to_json(self, text_content):
        """将格式化文本转换为 JSON"""
        
        # 按 --- 分割题目
        question_blocks = re.split(r'^-{3,}$', text_content, flags=re.MULTILINE)
        questions = []
        
        for block in question_blocks:
            block = block.strip()
            if not block:
                continue
            
            try:
                question = self._parse_single_question(block)
                if question:
                    questions.append(question)
            except Exception as e:
                print(f"⚠️ 解析题目时出错: {e}")
                continue
        
        return {"questions": questions}
    
    def _parse_single_question(self, block):
        """解析单个题目块"""
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        
        if len(lines) < 5:
            return None
        
        # 提取题目
        question_text = lines[0]
        if question_text.startswith('题目：') or question_text.startswith('题目:'):
            question_text = re.sub(r'^题目[：:]', '', question_text).strip()
        
        # 提取选项和解析
        options = []
        explanation = ""
        
        for line in lines[1:]:
            # 检查是否是解析行
            if line.startswith('解析：') or line.startswith('解析:'):
                explanation = re.sub(r'^解析[：:]', '', line).strip()
                break
            
            # 匹配选项格式：A. 文本 | 解析 ✓
            match = re.match(r'^([A-D])[.．]\s*(.+?)\s*[|｜]\s*(.+?)(\s*✓)?$', line)
            
            if match:
                option_text = match.group(2).strip()
                option_reason = match.group(3).strip()
                is_correct = match.group(4) is not None
                
                # 清理 reason 中可能残留的 ✓
                option_reason = option_reason.rstrip('✓').strip()
                
                options.append({
                    "text": option_text,
                    "isCorrect": is_correct,
                    "reason": option_reason
                })
        
        # 验证题目有效性
        if len(options) < 2:
            return None
        
        # 确保有且只有一个正确答案
        correct_count = sum(1 for opt in options if opt["isCorrect"])
        if correct_count != 1:
            print(f"⚠️ 题目 '{question_text[:30]}...' 正确答案数量不正确({correct_count})，已跳过")
            return None
        
        return {
            "question": question_text,
            "options": options,
            "explanation": explanation
        }
    
    def process_file(self, file_path, chapter_name, num_questions=15):
        """完整处理流程"""
        
        from config import FORMATTED_TEXT_FOLDER, JSON_FOLDER
        
        results = {
            "success": False,
            "message": "",
            "formatted_text_path": None,
            "json_path": None,
            "question_count": 0
        }
        
        try:
            # 1. 生成题目
            print(f"🤖 正在生成 {num_questions} 道题目...")
            formatted_text = self.generate_questions_from_file(
                file_path, 
                num_questions, 
                chapter_name
            )
            
            # 2. 保存格式化文本
            formatted_path = FORMATTED_TEXT_FOLDER / f"{chapter_name}_formatted.txt"
            with open(formatted_path, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            results["formatted_text_path"] = str(formatted_path)
            print(f"✅ 格式化文本已保存: {formatted_path}")
            
            # 3. 转换为 JSON
            print("🔄 正在转换为 JSON 格式...")
            json_data = self.parse_formatted_text_to_json(formatted_text)
            results["question_count"] = len(json_data["questions"])
            
            # 4. 保存 JSON
            json_path = JSON_FOLDER / f"{chapter_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            results["json_path"] = str(json_path)
            print(f"✅ JSON 文件已保存: {json_path}")
            
            results["success"] = True
            results["message"] = f"成功生成 {results['question_count']} 道题目"
            print(f"🎉 {results['message']}")
            
        except Exception as e:
            results["success"] = False
            results["message"] = str(e)
            print(f"❌ 处理失败: {e}")
        
        return results