import os
import json
from uuid import uuid4
from typing import Dict, List
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

UPLOAD_DIR = "uploads"
DOC_DIR = "documents"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)

import os
from langchain_openai import ChatOpenAI
#智能合同只用通义千问就行
MODEL_CONFIG = {
    '通义千问': {
        'api_key': os.environ.get('QWEN_API_KEY', ''),
        'model': os.environ.get('QWEN_MODEL', 'qwen-turbo'),
        'url': os.environ.get('QWEN_URL',
                              'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'),
    }
}

def save_upload_file(file, upload_dir=UPLOAD_DIR):
    """保存上传文件到指定目录，保留原始后缀，返回文件路径和文件ID"""
    file_id = str(uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join(upload_dir, f"{file_id}{file_extension}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_id, file_path

def extract_contract_content(file_path: str) -> str:
    """根据文件类型提取合同文本内容，txt自动检测编码"""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith(".txt"):
        # 尝试自动检测编码
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
        except Exception:
            try:
                loader = TextLoader(file_path, encoding="gbk")
                docs = loader.load()
            except Exception:
                loader = TextLoader(file_path, encoding="gb2312")
                docs = loader.load()
        content = "\n".join([doc.page_content for doc in docs])
        return content
    else:
        raise ValueError("仅支持 .txt/.docx/.pdf 文件")
    docs = loader.load()
    content = "\n".join([doc.page_content for doc in docs])
    return content

def analyze_contract_content_with_llm(content: str, model: str = "通义千问") -> Dict:
    """调用大模型分析合同内容，返回结构化结果，调用方式与ai_chat.py一致"""
    prompt = f"请分析以下合同内容，并以如下标准JSON格式返回：\n\n{content}\n\n返回格式示例：\n{{\n  \"合同摘要\": \n  \"潜在风险条款\": \n}}\n字段全部用中文，且不要返回markdown、代码块或字符串化JSON。注意：不要照搬示例，必须基于实际合同内容分析，请勿直接返回示例内容"

    model_key = model.lower()
    if model_key not in MODEL_CONFIG:
        raise ValueError(f"暂不支持的模型: {model}")
    conf = MODEL_CONFIG[model_key]
    llm = ChatOpenAI(
        model=conf['model'],
        base_url=conf['url'],
        api_key=conf['api_key'],
        temperature=0.2,
        max_tokens=1024
    )

    response = llm([HumanMessage(content=prompt)])
    result = response.content.strip() if hasattr(response, 'content') else str(response)

    # 兼容原有的key映射和清洗逻辑
    def try_json_loads(s):
        try:
            return json.loads(s)
        except Exception:
            return None
    import re
    def extract_json_str(s):
        s = s.strip()
        match = re.search(r'```json([\s\S]*?)```', s)
        if match:
            return match.group(1).strip()
        match = re.search(r'```([\s\S]*?)```', s)
        if match:
            return match.group(1).strip()
        match = re.search(r'({[\s\S]*})', s)
        if match:
            return match.group(1).strip()
        return s
    key_map = {
        "summary": "合同摘要", "contract_summary": "合同摘要", "摘要": "合同摘要", "合同摘要": "合同摘要",
        "borrower": "借款人", "lender": "出借人", "amount": "借款金额", "repayment_term": "借款期限", "contract_type": "合同类型", "signed_by": "签署情况", "核心内容": "核心内容",
        "risk_clauses": "潜在风险条款", "risk_warnings": "潜在风险条款", "风险提示": "潜在风险条款", "潜在风险条款": "潜在风险条款", "risk_tips": "潜在风险条款", "potential_risks": "潜在风险条款",
        "risk_type": "风险类型", "type": "风险类型", "风险类型": "风险类型",
        "description": "描述", "desc": "描述", "描述": "描述",
    }

    def normalize_keys(data):
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                k_cn = key_map.get(k.strip(), k.strip())
                new_data[k_cn] = normalize_keys(v)
            return new_data
        elif isinstance(data, list):
            return [normalize_keys(i) for i in data]
        else:
            return data
    analysis_data = try_json_loads(result)
    if not analysis_data:
        json_str = extract_json_str(result)
        analysis_data = try_json_loads(json_str)
    if not analysis_data and isinstance(result, str):
        json_str = extract_json_str(result)
        analysis_data = try_json_loads(json_str)
    if not analysis_data:
        return {"analysis": {"原始内容": result}}
    analysis_data = normalize_keys(analysis_data)
    std = {}
    if "合同摘要" in analysis_data:
        std["合同摘要"] = analysis_data["合同摘要"]
    else:
        summary_fields = ["借款人", "出借人", "借款金额", "借款期限", "还款时间", "合同类型", "签署情况", "核心内容"]
        summary_obj = {k: v for k, v in analysis_data.items() if k in summary_fields}
        if summary_obj:
            std["合同摘要"] = summary_obj
    if "潜在风险条款" in analysis_data:
        std["潜在风险条款"] = analysis_data["潜在风险条款"]
    else:
        for k in analysis_data:
            if isinstance(analysis_data[k], list):
                std["潜在风险条款"] = analysis_data[k]
                break
    if not std:
        return {"analysis": {"原始内容": result}}
    return {"analysis": std}