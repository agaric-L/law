import os
import json
import re
from uuid import uuid4
from typing import Dict, List
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.messages import HumanMessage
from pydantic import SecretStr
from dotenv import load_dotenv
load_dotenv()

UPLOAD_DIR = "uploads"
DOC_DIR = "documents"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)

import os
from langchain_openai import ChatOpenAI

# 全局工具函数
def try_json_loads(s):
    try:
        return json.loads(s)
    except Exception:
        return None

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

def identify_contract_type(content: str) -> str:
    """识别合同类型，为分析提供上下文"""
    contract_keywords = {
        "借贷合同": ["借款", "贷款", "利息", "还款", "本金"],
        "租赁合同": ["租赁", "租金", "租期", "押金", "房屋"],
        "买卖合同": ["买卖", "销售", "购买", "价款", "交付"],
        "劳动合同": ["工作", "工资", "社保", "试用期", "解除"],
        "服务合同": ["服务", "费用", "期限", "质量", "标准"]
    }
    
    content_lower = content.lower()
    for contract_type, keywords in contract_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            return contract_type
    
    return "其他合同"

def assess_risk_level(analysis_data: Dict) -> str:
    """基于分析结果评估风险等级"""
    risk_score = 0
    
    # 高风险因素
    if "高风险条款" in analysis_data and len(analysis_data["高风险条款"]) > 0:
        risk_score += len(analysis_data["高风险条款"]) * 3
    
    # 中风险因素
    if "中风险条款" in analysis_data and len(analysis_data["中风险条款"]) > 0:
        risk_score += len(analysis_data["中风险条款"]) * 2
    
    # 低风险因素
    if "低风险条款" in analysis_data and len(analysis_data["低风险条款"]) > 0:
        risk_score += len(analysis_data["低风险条款"]) * 1
    
    if risk_score >= 6:
        return "高风险"
    elif risk_score >= 3:
        return "中风险"
    else:
        return "低风险"

def analyze_contract_content_with_llm(content: str, model: str = "通义千问") -> Dict:
    """增强版合同分析"""
    
    # 1. 识别合同类型
    contract_type = identify_contract_type(content)
    
    # 2. 构建专业提示词
    prompt = f"""作为专业法律顾问，请分析这份{contract_type}：

{content}

请从以下维度进行专业分析：

**合同基本信息**
- 合同类型：{contract_type}
- 主要当事人
- 核心条款

**风险识别**
- 霸王条款（如：单方面加重责任、排除主要权利）
- 不公平条款（如：权利义务不对等）
- 法律漏洞（如：缺少必要条款）

**权利义务分析**
- 各方权利义务是否对等
- 是否存在明显不公平的条款

**违约责任评估**
- 违约条款是否合理
- 赔偿标准是否公平

**法律依据**
- 相关法律法规

**专业建议**
- 针对发现问题的具体建议

请以JSON格式返回，确保分析客观专业，避免误导用户。"""

    # 兼容原有的key映射和清洗逻辑
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
    
    # 3. 调用大模型分析
    model_key = model.lower()
    if model_key not in MODEL_CONFIG:
        raise ValueError(f"暂不支持的模型: {model}")
    
    conf = MODEL_CONFIG[model_key]
    llm = ChatOpenAI(
        model=conf['model'],
        base_url=conf['url'],
        api_key=SecretStr(conf['api_key']),
        temperature=0.1  # 降低随机性，提高一致性
    )

    response = llm([HumanMessage(content=prompt)])
    
    # 修复response.content的类型处理
    if hasattr(response, 'content'):
        result = response.content
        if isinstance(result, list):
            result = '\n'.join([str(item) for item in result])
        result = str(result).strip()
    else:
        result = str(response).strip()

    # 4. 解析结果
    analysis_data = try_json_loads(result)
    if not analysis_data:
        json_str = extract_json_str(result)
        analysis_data = try_json_loads(json_str)
    
    if not analysis_data:
        return {
            "error": "分析失败",
            "raw_result": result,
            "disclaimer": "本分析仅供参考，具体问题请咨询专业律师"
        }
    
    # 5. 评估风险等级
    risk_level = assess_risk_level(analysis_data)
    analysis_data["风险等级"] = risk_level
    
    # 6. 添加免责声明
    analysis_data["免责声明"] = "本分析仅供参考，具体问题请咨询专业律师"
    
    return {"analysis": analysis_data}
