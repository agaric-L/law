import json
from pathlib import Path


class TemplateService:
    def __init__(self):
<<<<<<< HEAD
        # 兼容 Render 云部署，使用绝对路径
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_path = os.path.join(base_dir, 'template', 'official_templates.json')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在：{template_path}")
=======
        # 加载官方模板（确保路径正确）
        template_path = Path(__file__).parent.parent.parent / "template" / "official_templates.json"
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在：{template_path}")

>>>>>>> e5db59705d7ac3e53137f9b5db64196b88c254fa
        with open(template_path, "r", encoding="utf-8") as f:
            self.templates = json.load(f)

    def get_template(self, doc_type: str) -> dict:
        """获取指定文书类型的官方模板"""
        return self.templates.get(doc_type)

    def build_prompt(self, doc_type: str, user_input: dict) -> str:
        """构建纯文本提示词（无Markdown标记）"""
        template = self.get_template(doc_type)
        if not template:
            raise ValueError(f"未找到{doc_type}模板")

        # 处理模板结构：移除原始模板中的Markdown标记（如**）
        cleaned_structure = []
        for section in template["structure"]:
            # 去除内容中的**（如"**民事起诉状**" → "民事起诉状"）
            clean_content = section["content"].replace("**", "")
            cleaned_structure.append(clean_content)
        structure = "\n".join(cleaned_structure)

        # 处理必填项：纯文本描述
        required_fields = ", ".join(template["required_fields"])

        # 生成纯文本提示词（无任何Markdown符号）
        return f"""
请严格按照以下官方格式生成{doc_type}，内容为纯文本（不要任何特殊标记），不得遗漏必填项：

官方模板格式：
{structure}

必填项：
{required_fields}

用户提供的信息：
{json.dumps(user_input, ensure_ascii=False, indent=2)}

生成要求：
1. 逐段匹配模板格式，替换[占位符]后删除括号及占位符标记；
2. 法律术语准确，引用法条需用全称（如《中华人民共和国民法典》）；
3. 输出内容只能是纯文本，不能包含**、#、[]、`等任何Markdown标记；
4. 语言正式、简洁，符合法律文书规范。
5. 分清原告和被告，原告是起诉方，被告是被起诉方。
6. 对于用户信息中的"XXX"占位符，请在文书中直接使用"XXX"表示，不要替换为其他内容。
7. 如果用户没有提供具体信息（如出生日期、案发时间等），在文书中使用"XXX"表示。
"""