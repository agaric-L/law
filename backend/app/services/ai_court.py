from typing import List, Dict, Optional
import json
from enum import Enum

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
    def __init__(self, json_file: str = "court_context.json"):
        self.json_file = json_file
        self.context = {
            "case_info": {},
            "evidence_list": [],
            "trial_records": [],
            "current_phase": TrialPhase.COURT_OPENING.value
        }

    def save_case_info(self, case_info: Dict) -> None:
        self.context["case_info"] = case_info
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
            "phase": self.context["current_phase"]
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

    def _save_to_json(self) -> None:
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)

class Agent:
    def __init__(self, role: str, context_manager: ContextManager):
        self.role = role
        self.context_manager = context_manager

    def respond(self, current_statement: str, phase: TrialPhase) -> str:
        # 基于角色、当前阶段和上下文生成回应
        raise NotImplementedError

class Judge(Agent):
    def __init__(self, context_manager: ContextManager):
        super().__init__("法官", context_manager)

    def start_trial(self) -> str:
        case_info = self.context_manager.get_case_info()
        opening_statement = (
            f"全体人员请遵守法庭纪律，不得喧哗、录音录像，手机调至静音。"
            f"本院现依法公开审理原告{case_info.get('plaintiff_name')}诉被告{case_info.get('defendant_name')}"
            f"（{case_info.get('case_type')}）一案，现在开庭。"
        )
        self.context_manager.add_trial_record(self.role, opening_statement)
        return opening_statement

    def request_statement(self, phase: TrialPhase) -> str:
        statements = {
            TrialPhase.PLAINTIFF_STATEMENT: "请原告宣读起诉状。",
            TrialPhase.DEFENDANT_DEFENSE: "请被告进行答辩。",
            TrialPhase.EVIDENCE_PRESENTATION: "请原告出示证据，说明证据名称、来源及证明目的。",
            TrialPhase.EVIDENCE_CROSS_EXAMINATION: "请被告对证据发表质证意见。",
            TrialPhase.FINAL_STATEMENT: "法庭辩论结束，请各方作最后陈述。"
        }
        statement = statements.get(phase, "")
        if statement:
            self.context_manager.add_trial_record(self.role, statement)
        return statement

    def make_judgment(self) -> str:
        case_info = self.context_manager.get_case_info()
        trial_records = self.context_manager.get_trial_records()
        evidence_list = self.context_manager.get_evidence_list()
        
        # 这里可以添加更复杂的判决逻辑，基于案件信息、庭审记录和证据
        judgment = (
            f"根据《中华人民共和国民事诉讼法》相关规定，经过审理查明：\n"
            f"1. {trial_records[1]['content']}\n"  # 原告陈述
            f"2. {trial_records[2]['content']}\n"  # 被告答辩
            f"本院认为，......\n"
            f"判决书：\n"
            f"......\n"
            f"如不服本判决，可在收到判决书之日起15日内上诉。"
        )
        self.context_manager.add_trial_record(self.role, judgment)
        return judgment

class Team(Agent):
    def __init__(self, role: str, is_ai: bool, context_manager: ContextManager):
        super().__init__(role, context_manager)
        self.is_ai = is_ai

    def present_case(self) -> str:
        case_info = self.context_manager.get_case_info()
        if self.role == "原告":
            statement = f"原告诉讼请求：{case_info.get('plaintiff_claim')}\n理由：{case_info.get('plaintiff_reason')}"
        else:
            statement = f"被告答辩意见：{case_info.get('defendant_response')}"
        self.context_manager.add_trial_record(self.role, statement)
        return statement

    def present_evidence(self, evidence: Evidence) -> str:
        statement = f"现出示证据：{evidence.name}，来源于{evidence.source}，用于证明{evidence.purpose}"
        self.context_manager.add_trial_record(self.role, statement)
        return statement

    def cross_examine_evidence(self, evidence: Evidence) -> str:
        # AI被告方可以根据证据内容生成更智能的质证意见
        statement = f"对于{evidence.name}，本方认为：\n"
        if self.is_ai:
            statement += self._generate_ai_cross_examination(evidence)
        self.context_manager.add_trial_record(self.role, statement)
        return statement

    def _generate_ai_cross_examination(self, evidence: Evidence) -> str:
        # 这里可以实现更复杂的AI质证逻辑
        return f"该证据在真实性、合法性和关联性方面存在以下问题：..."

class CourtSession:
    def __init__(self):
        self.context_manager = ContextManager()
        self.judge = Judge(self.context_manager)
        self.plaintiff_team = None
        self.defendant_team = None
        self.current_phase = TrialPhase.COURT_OPENING

    def setup_teams(self, player_role: str):
        if player_role == "plaintiff":
            self.plaintiff_team = Team("原告", False, self.context_manager)
            self.defendant_team = Team("被告", True, self.context_manager)
        else:
            self.plaintiff_team = Team("原告", True, self.context_manager)
            self.defendant_team = Team("被告", False, self.context_manager)

    def submit_case(self, case_info: Dict) -> None:
        self.context_manager.save_case_info(case_info)

    def submit_evidence(self, role: str, evidence: Evidence) -> str:
        self.context_manager.add_evidence(evidence)
        team = self.plaintiff_team if role == "plaintiff" else self.defendant_team
        return team.present_evidence(evidence)

    def process_evidence_cross_examination(self, evidence: Evidence) -> str:
        return self.defendant_team.cross_examine_evidence(evidence)

    def advance_trial(self) -> Dict:
        current_phase = self.current_phase
        response = {
            "phase": current_phase.value,
            "content": []
        }

        if current_phase == TrialPhase.COURT_OPENING:
            response["content"].append(self.judge.start_trial())
            self.current_phase = TrialPhase.PLAINTIFF_STATEMENT

        elif current_phase == TrialPhase.PLAINTIFF_STATEMENT:
            response["content"].append(self.judge.request_statement(current_phase))
            response["content"].append(self.plaintiff_team.present_case())
            self.current_phase = TrialPhase.DEFENDANT_DEFENSE

        elif current_phase == TrialPhase.DEFENDANT_DEFENSE:
            response["content"].append(self.judge.request_statement(current_phase))
            response["content"].append(self.defendant_team.present_case())
            self.current_phase = TrialPhase.EVIDENCE_PRESENTATION

        elif current_phase == TrialPhase.EVIDENCE_PRESENTATION:
            response["content"].append(self.judge.request_statement(current_phase))
            # 实际应用中，这里需要一个机制来获取原告提交的证据
            # 此处为简化示例，我们假设证据已在上下文中
            evidence_list = self.context_manager.get_evidence_list()
            for ev in evidence_list:
                evidence_obj = Evidence(ev['name'], ev['source'], ev['purpose'], ev['content'])
                response["content"].append(self.plaintiff_team.present_evidence(evidence_obj))
            self.current_phase = TrialPhase.EVIDENCE_CROSS_EXAMINATION

        elif current_phase == TrialPhase.EVIDENCE_CROSS_EXAMINATION:
            response["content"].append(self.judge.request_statement(current_phase))
            evidence_list = self.context_manager.get_evidence_list()
            for ev in evidence_list:
                evidence_obj = Evidence(ev['name'], ev['source'], ev['purpose'], ev['content'])
                response["content"].append(self.defendant_team.cross_examine_evidence(evidence_obj))
            self.current_phase = TrialPhase.COURT_INQUIRY

        elif current_phase == TrialPhase.COURT_INQUIRY:
            # 法庭询问阶段，法官可以向双方提问
            question_to_plaintiff = "法官：原告，请说明被告是如何归还借款的？"
            self.context_manager.add_trial_record(self.judge.role, question_to_plaintiff)
            response["content"].append(question_to_plaintiff)
            # 假设原告回答
            plaintiff_answer = "原告：被告声称已通过银行转账归还，但我并未收到相关款项。"
            self.context_manager.add_trial_record(self.plaintiff_team.role, plaintiff_answer)
            response["content"].append(plaintiff_answer)
            self.current_phase = TrialPhase.COURT_DEBATE

        elif current_phase == TrialPhase.COURT_DEBATE:
            response["content"].append("法官：双方围绕争议焦点发表辩论意见。")
            plaintiff_debate = "原告律师：请求法官支持原告诉讼请求。"
            self.context_manager.add_trial_record(self.plaintiff_team.role, plaintiff_debate)
            response["content"].append(plaintiff_debate)
            defendant_debate = "被告律师：请求驳回原告的诉讼请求。"
            self.context_manager.add_trial_record(self.defendant_team.role, defendant_debate)
            response["content"].append(defendant_debate)
            self.current_phase = TrialPhase.FINAL_STATEMENT

        elif current_phase == TrialPhase.FINAL_STATEMENT:
            response["content"].append(self.judge.request_statement(current_phase))
            plaintiff_final_statement = "原告：请求法官支持原告的诉讼请求。"
            self.context_manager.add_trial_record(self.plaintiff_team.role, plaintiff_final_statement)
            response["content"].append(plaintiff_final_statement)
            defendant_final_statement = "被告：请求驳回原告诉讼请求。"
            self.context_manager.add_trial_record(self.defendant_team.role, defendant_final_statement)
            response["content"].append(defendant_final_statement)
            self.current_phase = TrialPhase.JUDGMENT

        elif current_phase == TrialPhase.JUDGMENT:
            response["content"].append(self.judge.make_judgment())
            # 庭审结束，可以将阶段设置为一个终态，或保持在JUDGMENT

        self.context_manager.update_phase(self.current_phase)
        return response

def main():
    # 创建法庭会话
    court = CourtSession()
    
    # 示例：玩家选择作为原告
    court.setup_teams("plaintiff")
    
    # 提交案件信息
    case_info = {
        "case_title": "借款合同纠纷案",
        "plaintiff_name": "张三",
        "defendant_name": "李四",
        "case_type": "民事借款合同纠纷",
        "plaintiff_claim": "请求 WARRANTY 被告偿还借款10万元及利息",
        "plaintiff_reason": "2023年1月1日，原告借给被告10万元，约定年利率4%，至今未还",
        "defendant_response": "不同意偿还，借款已经归还"
    }
    court.submit_case(case_info)
    
    # 提交证据
    evidence = Evidence(
        name="借条",
        source="原告提供",
        purpose="证明借款事实",
        content="兹借到张三现金10万元，约定年利率4%，借款日期：2023年1月1日，借款人：李四"
    )
    court.submit_evidence("plaintiff", evidence)
    
    # 进行庭审
    while True:
        response = court.advance_trial()
        print(f"\n当前阶段：{response['phase']}")
        for content in response['content']:
            print(content)
        
        if response['phase'] == TrialPhase.JUDGMENT.value:
            break

if __name__ == "__main__":
    main()