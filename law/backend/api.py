from fastapi import APIRouter, Body, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
from backend.app.services.ai_court import CourtCoordinator, Evidence, get_court_session
from backend.app.services.law_search import search_law
from backend.app.services.ai_chat import ai_legal_qa_function_stream, reset_ai_legal_memory
from backend.app.services.document_service import DocumentService
from backend.app.services.smart_contracts import save_upload_file, extract_contract_content, analyze_contract_content_with_llm, analyze_contract_content_with_llm_stream
from backend.app.services.case_cards import get_case_cards
from backend.app.models.legal_doc_models import LawsuitRequest
from backend.app.services.quiz_service import QuizQuestion, QuizAnswerRequest, QuizAnswerResponse, get_all_questions, check_answer as check_quiz_answer, generate_explanation_stream


router = APIRouter()

# 初始化文书生成服务
document_service = DocumentService()

# @router.get("/feature1")
# def feature1():
#     # 调用 langchain_service 的功能
#     return some_langchain_function()

#AI懂法
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
    return ai_legal_qa_function_stream(question, model)

@router.post("/ai_legal_qa/stream")
def ai_legal_qa_stream(
    question: str = Body(..., embed=True),
    model: str = Body('qwen-turbo', embed=True),
):
    def event_stream():
        for chunk in ai_legal_qa_function_stream(question, model):
            yield chunk
    return StreamingResponse(event_stream(), media_type="text/plain")
    
#文书生成
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

@router.post("/generate_lawsuit/stream")
def generate_lawsuit_stream(request: LawsuitRequest):
    """
    流式生成民事起诉状
    """
    try:
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
        def event_stream():
            for chunk in document_service.generate_legal_doc_stream("民事起诉状", user_input):
                if isinstance(chunk, str):
                    yield chunk
                elif isinstance(chunk, list):
                    for item in chunk:
                        if isinstance(item, str):
                            yield item
                        elif isinstance(item, dict):
                            yield str(item)
                elif isinstance(chunk, dict):
                    yield str(chunk)
        return StreamingResponse(event_stream(), media_type="text/plain")
    except Exception as e:
        def err_stream():
            yield f"[文书生成出错: {e}]"
        return StreamingResponse(err_stream(), media_type="text/plain")

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

@router.post("/generate_defense/stream")
def generate_defense_stream(request: LawsuitRequest):
    """
    流式生成民事答辩状
    """
    try:
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
        def event_stream():
            for chunk in document_service.generate_legal_doc_stream("民事答辩状", user_input):
                if isinstance(chunk, str):
                    yield chunk
                elif isinstance(chunk, list):
                    for item in chunk:
                        if isinstance(item, str):
                            yield item
                        elif isinstance(item, dict):
                            yield str(item)
                elif isinstance(chunk, dict):
                    yield str(chunk)
        return StreamingResponse(event_stream(), media_type="text/plain")
    except Exception as e:
        def err_stream():
            yield f"[文书生成出错: {e}]"
        return StreamingResponse(err_stream(), media_type="text/plain")

# @router.get("/ai_legal_history/{session_id}")
# def get_ai_legal_history(session_id: str):
#     from app.services.langchain_service import get_history
#     return get_history(session_id)

#智能合同
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

@router.post("/smart_contracts/analyze_contract/stream")
async def analyze_contract_stream(file: UploadFile = File(...)):
    file_id, file_path = save_upload_file(file, upload_dir="documents")
    content = extract_contract_content(file_path)
    def event_stream():
        for chunk in analyze_contract_content_with_llm_stream(content):
            if isinstance(chunk, str):
                yield chunk
            elif isinstance(chunk, list):
                for item in chunk:
                    if isinstance(item, str):
                        yield item
                    elif isinstance(item, dict):
                        yield str(item)
            elif isinstance(chunk, dict):
                yield str(chunk)
    return StreamingResponse(event_stream(), media_type="text/plain")

#首页
@router.post("/law_search")
def law_search_api(query: str = Body(..., embed=True)):
    results = search_law(query)
    return {"results": results}
@router.get("/api/case_cards")
def api_case_cards(force_refresh: bool = False):
    return get_case_cards(force_refresh=force_refresh)

#法律答题
@router.get("/quiz", response_model=List[QuizQuestion])
def get_quiz():
    return get_all_questions()

@router.post("/quiz/answer", response_model=QuizAnswerResponse)
def check_answer(data: QuizAnswerRequest):
    return check_quiz_answer(data.id, data.answer)

@router.post("/quiz/answer/stream")
def check_answer_stream(data: QuizAnswerRequest):
    # 查找题目
    for q in get_all_questions():
        if q.id == data.id:
            # 直接流式输出解析
            def event_stream():
                # 先判断正误
                correct = False
                correct_answer = 0
                for qq in get_all_questions():
                    if qq.id == data.id:
                        correct_answer = qq.options.index(qq.options[0]) if hasattr(qq, 'answer') else 0
                        break
                # 直接用data.answer
                for chunk in generate_explanation_stream(q.question, q.options, data.answer):
                    if isinstance(chunk, str):
                        yield chunk
                    elif isinstance(chunk, list):
                        for item in chunk:
                            if isinstance(item, str):
                                yield item
                            elif isinstance(item, dict):
                                yield str(item)
                    elif isinstance(chunk, dict):
                        yield str(chunk)
            return StreamingResponse(event_stream(), media_type="text/plain")
    def err_stream():
        yield "题目不存在"
    return StreamingResponse(err_stream(), media_type="text/plain")

#AI法庭
class CourtCaseInfo(BaseModel):
    case_title: str
    plaintiff_name: str
    defendant_name: str
    case_type: str
    plaintiff_claim: str
    plaintiff_reason: str
    defendant_response: str
    defendant_reason: str = ""
    user_role: str = "plaintiff"  # 用户选择的角色

class CourtEvidence(BaseModel):
    name: str
    source: str
    purpose: str
    content: str

class CourtUserInput(BaseModel):
    session_id: str
    user_input: str

@router.post("/court/start_trial")
def start_trial(case_info: CourtCaseInfo):
    """
    初始化法庭会话并提交案件信息
    """
    # 创建会话ID
    session_id = str(uuid.uuid4())
    court = get_court_session(session_id)
    
    # 设置案件信息和用户角色
    case_data = {
        "case_title": case_info.case_title,
        "plaintiff_name": case_info.plaintiff_name,
        "defendant_name": case_info.defendant_name,
        "case_type": case_info.case_type,
        "plaintiff_claim": case_info.plaintiff_claim,
        "plaintiff_reason": case_info.plaintiff_reason,
        "defendant_response": case_info.defendant_response,
        "defendant_reason": case_info.defendant_reason
    }
    court.setup_case(case_data, case_info.user_role)
    
    return {
        "session_id": session_id,
        "message": "法庭会话已初始化，案件信息已提交"
    }

@router.post("/court/submit_evidence")
def submit_evidence(evidence: CourtEvidence, role: str = "plaintiff", session_id: Optional[str] = None):
    """
    提交证据
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少session_id参数")
    
    court = get_court_session(session_id)
    evidence_obj = Evidence(
        name=evidence.name,
        source=evidence.source,
        purpose=evidence.purpose,
        content=evidence.content
    )
    court.context_manager.add_evidence(evidence_obj)
    return {"message": "证据已提交"}

@router.post("/court/advance_trial")
def advance_trial(request: Optional[CourtUserInput] = None):
    """
    推进庭审到下一阶段
    """
    session_id = request.session_id if request else None
    user_input = request.user_input if request else None
    
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少session_id参数")
    
    court = get_court_session(session_id)
    response = court.advance_trial(user_input or "")
    
    return {
        "session_id": session_id,
        "phase": response["phase"],
        "content": response["content"],
        "need_user_input": response.get("need_user_input", False),
        "current_role": response.get("current_role"),
        "trial_completed": response.get("trial_completed", False)
    }

@router.get("/court/session/{session_id}")
def get_session_info(session_id: str):
    """
    获取会话信息
    """
    court = get_court_session(session_id)
    context = court.context_manager.context
    
    return {
        "session_id": session_id,
        "case_info": context.get("case_info", {}),
        "current_phase": context.get("current_phase"),
        "user_role": context.get("user_role"),
        "trial_records": context.get("trial_records", [])
    }