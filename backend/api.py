from fastapi import APIRouter, Body
from backend.app.services.law_search import search_law
from backend.app.services.ai_chat import ai_legal_qa_function, reset_ai_legal_memory
from backend.app.services.document_service import DocumentService
from backend.app.services.smart_contracts import save_upload_file, extract_contract_content, analyze_contract_content_with_llm
from backend.app.models.legal_doc_models import LawsuitRequest
from typing import Optional
from fastapi import UploadFile, File, HTTPException
import uuid
from pydantic import BaseModel
from typing import List
from backend.app.services.quiz_service import QuizQuestion, QuizAnswerRequest, QuizAnswerResponse, get_all_questions, check_answer as check_quiz_answer

router = APIRouter()

# 初始化文书生成服务
document_service = DocumentService()

# @router.get("/feature1")
# def feature1():
#     # 调用 langchain_service 的功能
#     return some_langchain_function()

@router.post("/reset_ai_memory")
async def reset_ai_memory():
    reset_ai_legal_memory()
    return {"msg": "memory reset"}

@router.post("/ai_legal_qa")
def ai_legal_qa(
    question: str = Body(..., embed=True),
    model: str = Body('qwen-turbo', embed=True),
):
    print(f"接收到的参数: question={question}, model={model}")
    return ai_legal_qa_function(question, model)

@router.post("/generate_lawsuit")
def generate_lawsuit(request: LawsuitRequest):
    """
    生成民事起诉状
    """
    try:
        # 构建用户输入数据
        user_input = {
            "原告信息": {
                "姓名": request.plaintiff.name,
                "证件类型": request.plaintiff.id_type,
                "证件号码": request.plaintiff.id_number,
                "住址": request.plaintiff.address,
                "联系方式": request.plaintiff.contact
            },
            "被告信息": {
                "姓名": request.defendant.name,
                "证件类型": request.defendant.id_type,
                "证件号码": request.defendant.id_number,
                "住址": request.defendant.address,
                "联系方式": request.defendant.contact
            },
            "案件信息": {
                "案件类型": request.case_info.case_type,
                "案件事实": request.case_info.facts,
                "法律依据": request.case_info.legal_basis or ""
            },
            "诉讼请求": request.claims,
            "受理法院": request.court
        }
        
        # 生成文书
        document_content = document_service.generate_legal_doc("民事起诉状", user_input)
        
        return {
            "success": True,
            "document_type": "民事起诉状",
            "content": document_content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/generate_defense")
def generate_defense(request: LawsuitRequest):
    """
    生成民事答辩状
    """
    try:
        # 构建用户输入数据
        user_input = {
            "答辩人信息": {
                "姓名": request.defendant.name,
                "证件类型": request.defendant.id_type,
                "证件号码": request.defendant.id_number,
                "住址": request.defendant.address,
                "联系方式": request.defendant.contact
            },
            "原告信息": {
                "姓名": request.plaintiff.name,
                "证件类型": request.plaintiff.id_type,
                "证件号码": request.plaintiff.id_number,
                "住址": request.plaintiff.address,
                "联系方式": request.plaintiff.contact
            },
            "案件信息": {
                "案件类型": request.case_info.case_type,
                "案件事实": request.case_info.facts,
                "法律依据": request.case_info.legal_basis or ""
            },
            "答辩请求": request.claims,
            "受理法院": request.court
        }
        
        # 生成文书
        document_content = document_service.generate_legal_doc("民事答辩状", user_input)
        
        return {
            "success": True,
            "document_type": "民事答辩状",
            "content": document_content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# @router.get("/ai_legal_history/{session_id}")
# def get_ai_legal_history(session_id: str):
#     from app.services.langchain_service import get_history
#     return get_history(session_id)

@router.post("/smart_contracts/upload/")
async def upload_contract_file(file: UploadFile = File(...)):
    try:
        file_id, file_path = save_upload_file(file)
        return {"file_id": file_id, "file_name": file.filename, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/smart_contracts/analyze_contract/")
async def analyze_contract(file: UploadFile = File(...)):
    # 保存文件
    file_id, file_path = save_upload_file(file, upload_dir="documents")
    # 提取内容
    content = extract_contract_content(file_path)
    # 调用大模型分析
    result = analyze_contract_content_with_llm(content)
    return result

@router.post("/law_search")
def law_search_api(query: str = Body(..., embed=True)):
    results = search_law(query)
    return {"results": results}



@router.get("/quiz", response_model=List[QuizQuestion])
def get_quiz():
    return get_all_questions()

@router.post("/quiz/answer", response_model=QuizAnswerResponse)
def check_answer(data: QuizAnswerRequest):
    return check_quiz_answer(data.id, data.answer)