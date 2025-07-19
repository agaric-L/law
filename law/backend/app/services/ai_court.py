from typing import List, Dict, Optional, Generator
import json
from enum import Enum
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from pydantic import SecretStr

load_dotenv()

class TrialPhase(Enum):
    COURT_OPENING = "开庭"
    PLAINTIFF_STATEMENT = "原告陈述"
    DEFENDANT_DEFENSE = "被告答辩"
    EVIDENCE_PRESENTATION = "举证"
    EVIDENCE_CROSS_EXAMINATION = "质证"
    COURT_INQUIRY = "法庭询问"
    COURT_DEBATE = "法庭辩论"
    FINAL_STATEMENT = "最后陈述"
    JUDGMENT = "判决"

class Evidence:
    def __init__(self, name: str, source: str, purpose: str, content: str):
        self.name = name
        self.source = source
        self.purpose = purpose
        self.content = content

class ContextManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.json_file = f"court_context_{session_id}.json"
        self.context = {
            "session_id": session_id,
            "case_info": {},
            "evidence_list": [],
            "trial_records": [],
            "current_phase": TrialPhase.COURT_OPENING.value,
            "user_role": "plaintiff",
            "created_at": datetime.now().isoformat()
        }

    def save_case_info(self, case_info: Dict) -> None:
        self.context["case_info"] = case_info
        self._save_to_json()

    def set_user_role(self, user_role: str) -> None:
        self.context["user_role"] = user_role
        self._save_to_json()

    def add_evidence(self, evidence: Evidence) -> None:
        self.context["evidence_list"].append({
            "name": evidence.name,
            "source": evidence.source,
            "purpose": evidence.purpose,
            "content": evidence.content
        })
        self._save_to_json()

    def add_trial_record(self, speaker: str, content: str) -> None:
        self.context["trial_records"].append({
            "speaker": speaker,
            "content": content,
            "phase": self.context["current_phase"],
            "timestamp": datetime.now().isoformat()
        })
        self._save_to_json()

    def update_phase(self, phase: TrialPhase) -> None:
        self.context["current_phase"] = phase.value
        self._save_to_json()

    def get_case_info(self) -> Dict:
        return self.context.get("case_info", {})

    def get_evidence_list(self) -> List[Dict]:
        return self.context.get("evidence_list", [])

    def get_trial_records(self) -> List[Dict]:
        return self.context.get("trial_records", [])

    def get_current_phase(self) -> str:
        return self.context.get("current_phase", TrialPhase.COURT_OPENING.value)

    def get_user_role(self) -> str:
        return self.context.get("user_role", "plaintiff")

    def _save_to_json(self) -> None:
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)

    def load_from_json(self) -> None:
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                self.context = json.load(f)
        except FileNotFoundError:
            pass  # 使用默认值

class BaseAgent:
    def __init__(self, role: str, context_manager: ContextManager):
        self.role = role
        self.context_manager = context_manager
        self.llm = self._init_llm()

    def _init_llm(self) -> ChatOpenAI:
        """从环境变量初始化大模型"""
        # 默认使用通义千问
        api_key = os.environ.get('QWEN_API_KEY', '')
        model = os.environ.get('QWEN_MODEL', 'qwen-turbo')
        url = os.environ.get('QWEN_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        
        return ChatOpenAI(
            model=model,
            base_url=url,
            api_key=SecretStr(api_key) if api_key else None,
            temperature=0.3
        )

    def _get_context_summary(self) -> str:
        """获取案件上下文摘要"""
        case_info = self.context_manager.get_case_info()
        trial_records = self.context_manager.get_trial_records()
        evidence_list = self.context_manager.get_evidence_list()
        
        context = f"""
案件信息：
- 案件标题：{case_info.get('case_title', '')}
- 案件类型：{case_info.get('case_type', '')}
- 原告诉讼请求：{case_info.get('plaintiff_claim', '')}
- 原告理由：{case_info.get('plaintiff_reason', '')}
- 被告答辩：{case_info.get('defendant_response', '')}
- 被告理由：{case_info.get('defendant_reason', '')}

庭审记录：{len(trial_records)}条
证据列表：{len(evidence_list)}项
当前阶段：{self.context_manager.get_current_phase()}
"""
        return context

    def generate_response(self, prompt: str) -> str:
        """使用大模型生成回复"""
        try:
            context = self._get_context_summary()
            system_prompt = f"""
你是一个专业的{self.role}，正在参与一场法庭审理。
请根据以下案件信息和庭审记录，按照{self.role}的身份和当前庭审阶段的要求进行回应。

案件背景：
{context}

请严格按照{self.role}的身份和当前庭审阶段的要求进行回应，语言要专业、准确、符合法律程序。
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return str(response.content)
        except Exception as e:
            print(f"大模型调用失败: {e}")
            return f"作为{self.role}，我需要根据案件情况进行分析和回应。"

class JudgeAgent(BaseAgent):
    def __init__(self, context_manager: ContextManager):
        super().__init__("法官", context_manager)

    def start_trial(self) -> str:
        case_info = self.context_manager.get_case_info()
        prompt = f"""
作为法官，请主持开庭仪式。案件信息如下：
- 原告：{case_info.get('plaintiff_name', '原告')}
- 被告：{case_info.get('defendant_name', '被告')}
- 案件类型：{case_info.get('case_type', '民事纠纷')}

请按照标准法庭程序进行开庭仪式。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def request_statement(self, phase: TrialPhase) -> str:
        phase_prompts = {
            TrialPhase.PLAINTIFF_STATEMENT: "请原告宣读起诉状，陈述诉讼请求和事实理由。",
            TrialPhase.DEFENDANT_DEFENSE: "请被告进行答辩，对原告的诉讼请求发表意见。",
            TrialPhase.EVIDENCE_PRESENTATION: "请原告出示证据，说明证据名称、来源及证明目的。",
            TrialPhase.EVIDENCE_CROSS_EXAMINATION: "请被告对原告出示的证据发表质证意见。",
            TrialPhase.COURT_DEBATE: "现在进入法庭辩论阶段，双方围绕争议焦点发表辩论意见。",
            TrialPhase.FINAL_STATEMENT: "法庭辩论结束，请各方作最后陈述。"
        }
        
        prompt = f"作为法官，当前庭审阶段是{phase.value}，请按照标准程序引导庭审进行。"
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def make_judgment(self) -> str:
        prompt = """
作为法官，请根据整个庭审过程和双方提交的证据，依法作出判决。
判决书应当包括：
1. 案件基本情况
2. 双方诉辩意见
3. 证据认定
4. 事实认定
5. 法律适用
6. 判决结果
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

class PlaintiffAgent(BaseAgent):
    def __init__(self, context_manager: ContextManager):
        super().__init__("原告", context_manager)

    def present_case(self) -> str:
        case_info = self.context_manager.get_case_info()
        prompt = f"""
作为原告，请根据以下信息宣读起诉状：
- 诉讼请求：{case_info.get('plaintiff_claim', '')}
- 事实和理由：{case_info.get('plaintiff_reason', '')}

请按照标准格式宣读起诉状。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def present_evidence(self, evidence: Evidence) -> str:
        prompt = f"""
作为原告，请出示证据：{evidence.name}
证据来源：{evidence.source}
证明目的：{evidence.purpose}
证据内容：{evidence.content}

请按照标准格式出示证据。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def debate(self, opponent_statement: str = "") -> str:
        prompt = f"""
作为原告，请进行法庭辩论。
{('对方观点：' + opponent_statement) if opponent_statement else ''}

请围绕案件争议焦点进行辩论。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def final_statement(self) -> str:
        prompt = "作为原告，请作最后陈述，总结本方观点和请求。"
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

class DefendantAgent(BaseAgent):
    def __init__(self, context_manager: ContextManager):
        super().__init__("被告", context_manager)

    def present_defense(self) -> str:
        case_info = self.context_manager.get_case_info()
        prompt = f"""
作为被告，请进行答辩：
- 原告诉讼请求：{case_info.get('plaintiff_claim', '')}
- 被告答辩意见：{case_info.get('defendant_response', '')}
- 被告理由：{case_info.get('defendant_reason', '')}

请按照标准格式进行答辩。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def cross_examine_evidence(self, evidence: Evidence) -> str:
        prompt = f"""
作为被告，请对原告出示的证据进行质证：
证据名称：{evidence.name}
证据来源：{evidence.source}
证明目的：{evidence.purpose}
证据内容：{evidence.content}

请从证据的真实性、合法性、关联性等方面进行质证。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def debate(self, opponent_statement: str = "") -> str:
        prompt = f"""
作为被告，请进行法庭辩论。
{('对方观点：' + opponent_statement) if opponent_statement else ''}

请围绕案件争议焦点进行辩论。
"""
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

    def final_statement(self) -> str:
        prompt = "作为被告，请作最后陈述，总结本方观点和请求。"
        response = self.generate_response(prompt)
        self.context_manager.add_trial_record(self.role, response)
        return response

class CourtCoordinator:
    """法庭协调器，负责协调整个庭审流程"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context_manager = ContextManager(session_id)
        self.context_manager.load_from_json()
        
        # 初始化所有agent
        self.judge = JudgeAgent(self.context_manager)
        self.plaintiff = PlaintiffAgent(self.context_manager)
        self.defendant = DefendantAgent(self.context_manager)
        
        self.current_phase = TrialPhase.COURT_OPENING
        self.user_role = "plaintiff"  # 默认用户为原告

    def setup_case(self, case_info: Dict, user_role: str) -> None:
        """设置案件信息和用户角色"""
        self.context_manager.save_case_info(case_info)
        self.context_manager.set_user_role(user_role)
        self.user_role = user_role

    def advance_trial(self, user_input: Optional[str] = None) -> Dict:
        """推进庭审流程"""
        response = {
            "phase": self.current_phase.value,
            "content": [],
            "need_user_input": False,
            "current_role": None,
            "session_id": self.session_id
        }

        # 如果有用户输入，先记录
        if user_input:
            user_role_name = "原告" if self.user_role == "plaintiff" else "被告"
            self.context_manager.add_trial_record(user_role_name, user_input)

        # 根据当前阶段推进庭审
        if self.current_phase == TrialPhase.COURT_OPENING:
            # 开庭仪式
            response["content"].append({"role": "法官", "content": self.judge.start_trial()})
            response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.PLAINTIFF_STATEMENT)})
            self.current_phase = TrialPhase.PLAINTIFF_STATEMENT
            self.context_manager.update_phase(self.current_phase)
            
            # 检查是否需要用户输入
            if self.user_role == "plaintiff":
                response["need_user_input"] = True
                response["current_role"] = "原告"
            else:
                # AI原告自动陈述
                response["content"].append({"role": "原告", "content": self.plaintiff.present_case()})
                self._advance_to_defendant_defense(response)

        elif self.current_phase == TrialPhase.PLAINTIFF_STATEMENT:
            if user_input:
                # 用户已输入，继续到被告答辩
                response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.DEFENDANT_DEFENSE)})
                self.current_phase = TrialPhase.DEFENDANT_DEFENSE
                self.context_manager.update_phase(self.current_phase)
                
                if self.user_role == "defendant":
                    response["need_user_input"] = True
                    response["current_role"] = "被告"
                else:
                    # AI被告自动答辩
                    response["content"].append({"role": "被告", "content": self.defendant.present_defense()})
                    self._advance_to_evidence_presentation(response)

        elif self.current_phase == TrialPhase.DEFENDANT_DEFENSE:
            if user_input:
                # 用户已输入，继续到举证阶段
                response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.EVIDENCE_PRESENTATION)})
                self.current_phase = TrialPhase.EVIDENCE_PRESENTATION
                self.context_manager.update_phase(self.current_phase)
                
                if self.user_role == "plaintiff":
                    response["need_user_input"] = True
                    response["current_role"] = "原告"
                else:
                    # AI原告自动举证
                    self._handle_evidence_presentation(response)

        elif self.current_phase == TrialPhase.EVIDENCE_PRESENTATION:
            if user_input:
                # 用户已举证，继续到质证阶段
                response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.EVIDENCE_CROSS_EXAMINATION)})
                self.current_phase = TrialPhase.EVIDENCE_CROSS_EXAMINATION
                self.context_manager.update_phase(self.current_phase)
                
                if self.user_role == "defendant":
                    response["need_user_input"] = True
                    response["current_role"] = "被告"
                else:
                    # AI被告自动质证
                    self._handle_evidence_cross_examination(response)

        elif self.current_phase == TrialPhase.EVIDENCE_CROSS_EXAMINATION:
            if user_input:
                # 用户已质证，继续到法庭辩论
                response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.COURT_DEBATE)})
                self.current_phase = TrialPhase.COURT_DEBATE
                self.context_manager.update_phase(self.current_phase)
                
                if self.user_role == "plaintiff":
                    response["need_user_input"] = True
                    response["current_role"] = "原告"
                else:
                    # AI原告自动辩论
                    response["content"].append({"role": "原告", "content": self.plaintiff.debate()})
                    self._advance_to_defendant_debate(response)

        elif self.current_phase == TrialPhase.COURT_DEBATE:
            if user_input:
                # 用户已辩论，检查是否需要对方回应
                if self.user_role == "plaintiff":
                    # 原告已发言，被告回应
                    response["content"].append({"role": "被告", "content": self.defendant.debate(user_input)})
                    self._advance_to_final_statement(response)
                elif self.user_role == "defendant":
                    # 被告已发言，原告回应
                    response["content"].append({"role": "原告", "content": self.plaintiff.debate(user_input)})
                    self._advance_to_final_statement(response)

        elif self.current_phase == TrialPhase.FINAL_STATEMENT:
            if user_input:
                # 用户已作最后陈述，检查是否需要对方最后陈述
                if self.user_role == "plaintiff":
                    # 原告已最后陈述，被告最后陈述
                    response["content"].append({"role": "被告", "content": self.defendant.final_statement()})
                    self._advance_to_judgment(response)
                elif self.user_role == "defendant":
                    # 被告已最后陈述，原告最后陈述
                    response["content"].append({"role": "原告", "content": self.plaintiff.final_statement()})
                    self._advance_to_judgment(response)

        elif self.current_phase == TrialPhase.JUDGMENT:
            # 法官判决
            response["content"].append({"role": "法官", "content": self.judge.make_judgment()})
            response["trial_completed"] = True

        return response

    def _advance_to_defendant_defense(self, response: Dict) -> None:
        """推进到被告答辩阶段"""
        response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.DEFENDANT_DEFENSE)})
        self.current_phase = TrialPhase.DEFENDANT_DEFENSE
        self.context_manager.update_phase(self.current_phase)
        
        if self.user_role == "defendant":
            response["need_user_input"] = True
            response["current_role"] = "被告"
        else:
            response["content"].append({"role": "被告", "content": self.defendant.present_defense()})
            self._advance_to_evidence_presentation(response)

    def _advance_to_evidence_presentation(self, response: Dict) -> None:
        """推进到举证阶段"""
        response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.EVIDENCE_PRESENTATION)})
        self.current_phase = TrialPhase.EVIDENCE_PRESENTATION
        self.context_manager.update_phase(self.current_phase)
        
        if self.user_role == "plaintiff":
            response["need_user_input"] = True
            response["current_role"] = "原告"
        else:
            self._handle_evidence_presentation(response)

    def _handle_evidence_presentation(self, response: Dict) -> None:
        """处理举证阶段"""
        evidence_list = self.context_manager.get_evidence_list()
        if evidence_list:
            for evidence_data in evidence_list:
                evidence = Evidence(
                    evidence_data["name"],
                    evidence_data["source"],
                    evidence_data["purpose"],
                    evidence_data["content"]
                )
                response["content"].append({"role": "原告", "content": self.plaintiff.present_evidence(evidence)})
        
        # 推进到质证阶段
        response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.EVIDENCE_CROSS_EXAMINATION)})
        self.current_phase = TrialPhase.EVIDENCE_CROSS_EXAMINATION
        self.context_manager.update_phase(self.current_phase)
        
        if self.user_role == "defendant":
            response["need_user_input"] = True
            response["current_role"] = "被告"
        else:
            self._handle_evidence_cross_examination(response)

    def _handle_evidence_cross_examination(self, response: Dict) -> None:
        """处理质证阶段"""
        evidence_list = self.context_manager.get_evidence_list()
        if evidence_list:
            for evidence_data in evidence_list:
                evidence = Evidence(
                    evidence_data["name"],
                    evidence_data["source"],
                    evidence_data["purpose"],
                    evidence_data["content"]
                )
                response["content"].append({"role": "被告", "content": self.defendant.cross_examine_evidence(evidence)})
        
        # 推进到法庭辩论
        response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.COURT_DEBATE)})
        self.current_phase = TrialPhase.COURT_DEBATE
        self.context_manager.update_phase(self.current_phase)
        
        if self.user_role == "plaintiff":
            response["need_user_input"] = True
            response["current_role"] = "原告"
        else:
            response["content"].append({"role": "原告", "content": self.plaintiff.debate()})
            self._advance_to_defendant_debate(response)

    def _advance_to_defendant_debate(self, response: Dict) -> None:
        """推进到被告辩论阶段"""
        if self.user_role == "defendant":
            response["need_user_input"] = True
            response["current_role"] = "被告"
        else:
            response["content"].append({"role": "被告", "content": self.defendant.debate()})
            self._advance_to_final_statement(response)

    def _advance_to_final_statement(self, response: Dict) -> None:
        """推进到最后陈述阶段"""
        response["content"].append({"role": "法官", "content": self.judge.request_statement(TrialPhase.FINAL_STATEMENT)})
        self.current_phase = TrialPhase.FINAL_STATEMENT
        self.context_manager.update_phase(self.current_phase)
        
        if self.user_role == "plaintiff":
            response["need_user_input"] = True
            response["current_role"] = "原告"
        else:
            response["content"].append({"role": "原告", "content": self.plaintiff.final_statement()})
            self._advance_to_defendant_final_statement(response)

    def _advance_to_defendant_final_statement(self, response: Dict) -> None:
        """推进到被告最后陈述阶段"""
        if self.user_role == "defendant":
            response["need_user_input"] = True
            response["current_role"] = "被告"
        else:
            response["content"].append({"role": "被告", "content": self.defendant.final_statement()})
            self._advance_to_judgment(response)

    def _advance_to_judgment(self, response: Dict) -> None:
        """推进到判决阶段"""
        self.current_phase = TrialPhase.JUDGMENT
        self.context_manager.update_phase(self.current_phase)
        response["content"].append({"role": "法官", "content": self.judge.make_judgment()})
        response["trial_completed"] = True

# 全局会话管理器
court_sessions: Dict[str, CourtCoordinator] = {}

def get_court_session(session_id: str) -> CourtCoordinator:
    """获取或创建法庭会话"""
    if session_id not in court_sessions:
        court_sessions[session_id] = CourtCoordinator(session_id)
    return court_sessions[session_id]

def main():
    # 测试代码
    session_id = str(uuid.uuid4())
    coordinator = CourtCoordinator(session_id)
    
    case_info = {
        "case_title": "借款纠纷案",
        "plaintiff_name": "张三",
        "defendant_name": "李四",
        "case_type": "借贷纠纷",
        "plaintiff_claim": "请求判令被告归还借款10万元",
        "plaintiff_reason": "被告借款未还",
        "defendant_response": "不同意原告诉讼请求",
        "defendant_reason": "原告所述事实不属实"
    }
    
    coordinator.setup_case(case_info, "plaintiff")
    result = coordinator.advance_trial()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()