from .template_service import TemplateService
from openai import OpenAI
import os
from typing import Dict

class DocumentService:
    def __init__(self):
        self.template_service = TemplateService()
        # 从环境变量读取API密钥，避免硬编码
        self.api_key = "sk-5aa7547800eb424599bce554bd52c3d9"  # 请替换为真实密钥
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model_name = "qwen-plus"

    def generate_legal_doc(self, doc_type: str, user_input: Dict) -> str:
        """生成法律文书的主方法（纯文本格式，无Markdown）"""
        try:
            # 1. 调用模板服务生成纯文本提示词
            prompt = self.template_service.build_prompt(doc_type, user_input)

            # 2. 调用模型，明确要求纯文本输出
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业法律文书生成助手，生成的文书必须是纯文本格式，绝对不能包含任何Markdown标记（如**、#、[]、`等），严格遵循中国法律规范和官方模板的文本格式。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            # 3. 清理可能残留的Markdown标记（双重保险）
            raw_content = response.choices[0].message.content.strip()
            clean_content = raw_content.replace("**", "").replace("__", "").replace("`", "").replace("[", "").replace("]", "")

            return clean_content

        except Exception as e:
            raise ValueError(f"Qwen模型调用失败：{str(e)}") from e