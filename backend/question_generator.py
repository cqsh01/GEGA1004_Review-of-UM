# backend/question_generator_dashscope.py
from http import HTTPStatus
import dashscope
from dashscope import MultiModalConversation
import os

class DashScopeQuestionGenerator:
    def __init__(self, api_key):
        dashscope.api_key = api_key
    
    def generate_questions_from_file(self, file_path, num_questions=15, chapter_info=""):
        """直接上传文件给 Qwen-VL"""
        
        # 上传文件到 DashScope
        print(f"📤 正在上传文件到 DashScope...")
        
        messages = [
            {
                "role": "system",
                "content": "你是一个医学史课程的专业题目生成专家。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "file": f"file://{os.path.abspath(file_path)}"
                    },
                    {
                        "text": f"""请基于上传的文件内容生成 {num_questions} 道医学史选择题。

章节信息：{chapter_info}

请仔细分析文件中的所有内容，包括文本、图片、图表等。如果图片中包含重要信息（如历史人物、医学工具、解剖图等），请在题目中体现。

输出格式：
题目：[题目文本]
A. [选项A] | [解析]
B. [选项B] | [解析]
C. [选项C] | [解析] ✓
D. [选项D] | [解析]
解析：[易混淆点]

---

题目之间用 --- 分隔。"""
                    }
                ]
            }
        ]
        
        response = MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"API 调用失败: {response.message}")