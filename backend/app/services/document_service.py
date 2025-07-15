import os
from typing import Dict, List
from langchain_openai import ChatOpenAI
from .template_service import TemplateService

MODEL_CONFIG = {
    '通义千问': {
        'api_key': os.environ.get('QWEN_API_KEY', ''),
        'model': os.environ.get('QWEN_MODEL', 'qwen-plus'),
        'url': os.environ.get('QWEN_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'),
    }
}

class DocumentService:
    def __init__(self):
        self.template_service = TemplateService()
        conf = MODEL_CONFIG['通义千问']
        self.llm = ChatOpenAI(
            model=conf['model'],
            api_key=conf['api_key'],
            base_url=conf['url'],
            max_tokens=2000,
            temperature=0.2,
        )
        self.model_name = conf['model']

    def generate_legal_doc(self, doc_type: str, user_input: Dict) -> str:
        """生成法律文书的主方法（纯文本格式，无Markdown）"""
        try:
            print(f"生成文书类型: {doc_type}, 用户输入: {user_input}")
            # 1. 调用模板服务生成纯文本提示词
            prompt = self.template_service.build_prompt(doc_type, user_input)
            print(f"生成的prompt: {prompt}")

            # 2. 调用模型，明确要求纯文本输出
            messages = [
                ("system", "你是专业法律文书生成助手，生成的文书必须是纯文本格式，绝对不能包含任何Markdown标记（如**、#、[]、`等），严格遵循中国法律规范和官方模板的文本格式。"),
                ("human", prompt)
            ]
            response = self.llm.invoke(messages)
            print(f"模型返回: {response}")

            # 3. 清理可能残留的Markdown标记（双重保险）
            raw_content = response.content.strip()
            clean_content = raw_content.replace("**", "").replace("__", "").replace("`", "").replace("[", "").replace("]", "")
            print(f"最终输出: {clean_content}")
            return clean_content
        except Exception as e:
            print(f"Error generating legal document: {e}")
            return ""
