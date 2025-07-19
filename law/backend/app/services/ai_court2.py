import json
from typing import List, Dict, Optional, Any
import logging
logger = logging.getLogger(__name__)
from .ai_chat import ai_legal_qa_function
from .document_service import DocumentService

# ================== 固定法官台词（严格参照用户给定流程） ==================
JUDGE_LINES = [
    "全体人员请遵守法庭纪律，不得喧哗、录音录像，手机调至静音。智法云人民法院民事审判庭，现依法公开审理原告××诉被告××（案由）一案，现在开庭。",
    "请原告宣读起诉状。",
    "请被告进行答辩。",
    "请原告出示证据，说明证据名称、来源及证明目的。",
    "请被告对证据发表质证意见（真实性、合法性、关联性）。",
    None,  # 法官询问阶段，由LLM生成问题
    "双方围绕争议焦点（如合同效力、损害赔偿等）发表辩论意见。",
    "法庭辩论结束，请原告作最后陈述。",
    "法庭辩论结束，请被告作最后陈述。",
    None   # 法官判决阶段，由LLM生成判决结果
]

PROMPTS = {
    "plaintiff_statement": "你是原告，请宣读起诉状。",
    "defendant_defense": "你是被告，请进行答辩。",
    "plaintiff_evidence": "你是原告，请出示证据。",
    "defendant_cross": "你是被告，请对原告证据进行质证。",
    "judge_question_plaintiff": "你是法官，请向原告提出1-2个关键问题。",
    "judge_question_defendant": "你是法官，请向被告提出1-2个关键问题。",
    "plaintiff_answer": "你是原告，请回答法官的问题。",
    "defendant_answer": "你是被告，请回答法官的问题。",
    "plaintiff_final": "你是原告，请作最后陈述。",
    "defendant_final": "你是被告，请作最后陈述。",
    "judge_judgment": "你是法官，请根据案件事实和证据做出判决。可以当庭宣判，也可以择日宣判。"
}

class Evidence:
    def __init__(self, name, source, purpose, content):
        self.name = name
        self.source = source
        self.purpose = purpose
        self.content = content
    def to_dict(self):
        return {
            "name": self.name,
            "source": self.source,
            "purpose": self.purpose,
            "content": self.content
        }

class CourtSession:
    def __init__(self, user_role="plaintiff"):
        self.case_info: Optional[Dict] = None
        self.evidence_list: List[Dict] = []
        self.history: List[Dict] = []
        self.stage = 0
        self.user_role = user_role  # 'plaintiff' or 'defendant'
        self.document_service = DocumentService()  # 初始化文书生成服务
        self.stage_order = [
            "judge_opening",           # 0 法官说第一句：开庭
            "judge_plaintiff",         # 1 法官说第二句：请原告宣读起诉状
            "plaintiff_statement",     # 2 原告宣读起诉状
            "judge_defendant",        # 3 法官说第三句：请被告进行答辩
            "defendant_defense",      # 4 被告答辩
            "judge_evidence",         # 5 法官说第四句：请原告出示证据
            "plaintiff_evidence",     # 6 原告举证
            "judge_cross",            # 7 法官说第五句：请被告对证据发表质证意见
            "defendant_cross",        # 8 被告质证
            "judge_question_plaintiff", # 9 法官向原告提问
            "plaintiff_answer",       # 10 原告回答
            "judge_question_defendant", # 11 法官向被告提问
            "defendant_answer",       # 12 被告回答
            "plaintiff_final",        # 13 原告最后陈述
            "defendant_final",        # 14 被告最后陈述
            "judge_judgment"          # 15 法官宣判
        ]
        self.context: Dict[str, Any] = {
            "complaint": "",
            "defense": "",
            "evidence": [],
            "court_context": "",
            "history": []
        }
        self.teams = {"plaintiff": None, "defendant": None}

    def setup_teams(self, role: str):
        if role == "plaintiff":
            self.teams["plaintiff"] = {"role": "plaintiff", "members": []}
        elif role == "defendant":
            self.teams["defendant"] = {"role": "defendant", "members": []}
        return {"status": "success", "message": f"{role}团队已初始化"}

    def submit_case(self, case_data: Dict):
        self.case_info = case_data
        self.context["complaint"] = str(case_data.get("plaintiff_claim", ""))
        self.context["defense"] = str(case_data.get("defendant_response", ""))
        self.context["evidence"] = []
        self.context["history"] = []
        self.context["court_context"] = ""
        return {"status": "success", "message": "案件已提交"}

    def submit_evidence(self, role: str, evidence: Evidence):
        ev_dict = evidence.to_dict()
        self.evidence_list.append({"role": role, "evidence": ev_dict})
        self.context["evidence"].append(ev_dict)
        return {"status": "success", "message": f"证据'{evidence.name}'已由{role}提交"}

    def advance_trial(self, user_input=None):
        # 流程结束判断
        if self.stage >= len(self.stage_order):
            return self._stage_result(None, "系统", "end")

        role = self.get_current_role()
        stage_key = self.stage_order[self.stage]
        
        logger.info(f"当前阶段: {stage_key}, 角色: {role}, 用户角色: {self.user_role}, 用户输入: {user_input}")

        # 用户角色
        if ((role == "原告" and self.user_role == "plaintiff") or (role == "被告" and self.user_role == "defendant")):
            if user_input is None:
                logger.info(f"用户回合，等待输入: {role}")
                return self._stage_result(None, role, stage_key)
            
            logger.info(f"用户输入: {user_input}")
            # 记录用户输入
            if stage_key == "plaintiff_statement":
                self.context["complaint"] = str(user_input)
            elif stage_key == "defendant_defense":
                self.context["defense"] = str(user_input)
            elif stage_key == "plaintiff_evidence":
                ev = Evidence(name="证据", source="原告", purpose="证明案件事实", content=str(user_input))
                self.submit_evidence("plaintiff", ev)
            elif stage_key == "defendant_cross":
                self.context["defendant_cross"] = str(user_input)
            elif stage_key == "plaintiff_answer":
                self.context["plaintiff_answer"] = str(user_input)
            elif stage_key == "defendant_answer":
                self.context["defendant_answer"] = str(user_input)
            elif stage_key == "plaintiff_final":
                self.context["plaintiff_final"] = str(user_input)
            elif stage_key == "defendant_final":
                self.context["defendant_final"] = str(user_input)
            self.append_history({"role": role, "content": str(user_input)})
            self.stage += 1
            # 用户输入后，推进到下一个阶段
            return self.advance_trial(None)

        # AI角色
        logger.info(f"检查AI角色条件: role={role}, user_role={self.user_role}")
        
        # 修复条件判断：当用户扮演原告时，AI扮演被告；当用户扮演被告时，AI扮演原告
        if ((role == "原告" and self.user_role == "defendant") or (role == "被告" and self.user_role == "plaintiff")):
            logger.info(f"进入AI角色处理: {role}")
            output = ""
            
            # 特殊处理：原告宣读起诉状时，调用文书生成功能
            if stage_key == "plaintiff_statement" and role == "原告":
                try:
                    # 确保case_info不为None
                    case_info = self.case_info or {}
                    # 构建文书生成所需的用户输入
                    user_input = {
                        "原告信息": {
                            "姓名": case_info.get("plaintiff_name", "原告"),
                            "证件类型": "身份证",
                            "证件号码": "***",
                            "住址": "***",
                            "联系方式": "***"
                        },
                        "被告信息": {
                            "姓名": case_info.get("defendant_name", "被告"),
                            "证件类型": "身份证",
                            "证件号码": "***",
                            "住址": "***",
                            "联系方式": "***"
                        },
                        "案件信息": {
                            "案件类型": case_info.get("case_type", ""),
                            "案件事实": case_info.get("plaintiff_reason", ""),
                            "法律依据": ""
                        },
                        "诉讼请求": case_info.get("plaintiff_claim", ""),
                        "受理法院": "智法云人民法院"
                    }
                    
                    # 生成起诉状
                    complaint_content = self.document_service.generate_legal_doc("民事起诉状", user_input)
                    if complaint_content:
                        output = f"现在宣读起诉状：\n\n{complaint_content}"
                    else:
                        # 如果文书生成失败，使用备用方案
                        prompt = PROMPTS.get(stage_key, "")
                        context_text = self._build_context_text(stage_key)
                        full_prompt = f"""
{context_text}

{prompt}

重要：你现在就是{role}，直接说话，不要解释，不要分析，不要总结。
"""
                        result = ai_legal_qa_function(full_prompt, model="智谱")
                        output = result['summary'] if isinstance(result, dict) and 'summary' in result else str(result)
                except Exception as e:
                    logger.error(f"生成起诉状失败: {e}")
                    # 使用备用方案
                    prompt = PROMPTS.get(stage_key, "")
                    context_text = self._build_context_text(stage_key)
                    full_prompt = f"""
{context_text}

{prompt}

重要：你现在就是{role}，直接说话，不要解释，不要分析，不要总结。
"""
                    result = ai_legal_qa_function(full_prompt, model="智谱")
                    output = result['summary'] if isinstance(result, dict) and 'summary' in result else str(result)
            else:
                # 其他AI角色使用原有逻辑
                prompt = PROMPTS.get(stage_key, "")
                if prompt:
                    context_text = self._build_context_text(stage_key)
                    full_prompt = f"""
{context_text}

{prompt}

重要：你现在就是{role}，直接说话，不要解释，不要分析，不要总结。
"""
                    result = ai_legal_qa_function(full_prompt, model="智谱")
                    output = result['summary'] if isinstance(result, dict) and 'summary' in result else str(result)
                else:
                    # 如果没有找到对应的prompt，使用默认回复
                    output = f"我是{role}，正在等待指示。"
            
            logger.info(f"AI角色{role}生成回复: {output}")
            self.append_history({"role": role, "content": output})
            self.stage += 1
            # 只返回本阶段AI发言，前端收到后自动推进
            return self._stage_result(output, role, stage_key)

        # 法官阶段
        if role == "法官":
            if stage_key == "judge_opening":
                # 法官说第一句：开庭
                output = JUDGE_LINES[0]
            elif stage_key == "judge_plaintiff":
                # 法官说第二句：请原告宣读起诉状
                output = JUDGE_LINES[1]
            elif stage_key == "judge_defendant":
                # 法官说第三句：请被告进行答辩
                output = JUDGE_LINES[2]
            elif stage_key == "judge_evidence":
                # 法官说第四句：请原告出示证据
                output = JUDGE_LINES[3]
            elif stage_key == "judge_cross":
                # 法官说第五句：请被告对证据发表质证意见
                output = JUDGE_LINES[4]
            elif stage_key == "judge_question_plaintiff" or stage_key == "judge_question_defendant":
                # 法官提问阶段，由LLM生成问题
                prompt = PROMPTS.get(stage_key, "")
                context_text = self._build_context_text(stage_key)
                full_prompt = f"""
{context_text}

{prompt}

重要：你现在就是法官，直接说话，不要解释，不要分析，不要总结。
"""
                result = ai_legal_qa_function(full_prompt, model="智谱")
                output = result['summary'] if isinstance(result, dict) and 'summary' in result else str(result)
                
                # 保存法官问题到context中
                if stage_key == "judge_question_plaintiff":
                    self.context["judge_question_plaintiff"] = output
                elif stage_key == "judge_question_defendant":
                    self.context["judge_question_defendant"] = output
                    
            elif stage_key == "judge_judgment":
                # 法官判决阶段，由LLM生成判决结果
                prompt = PROMPTS.get(stage_key, "")
                context_text = self._build_context_text(stage_key)
                full_prompt = f"""
{context_text}

{prompt}

重要：你现在就是法官，直接说话，不要解释，不要分析，不要总结。
"""
                result = ai_legal_qa_function(full_prompt, model="智谱")
                output = result['summary'] if isinstance(result, dict) and 'summary' in result else str(result)
            else:
                # 其他法官阶段使用固定台词
                output = JUDGE_LINES[self.stage] if self.stage < len(JUDGE_LINES) else ""
            
            self.append_history({"role": role, "content": output})
            self.stage += 1
            # 只返回本阶段法官台词，前端收到后自动推进
            return self._stage_result(output, role, stage_key)

        # 兜底
        return self._stage_result(None, role, stage_key)

    def _build_context_text(self, stage_key):
        case_info = self.case_info or {}
        
        if stage_key == "plaintiff_statement":
            return f"""
你的诉讼请求：{case_info.get('plaintiff_claim', '')}
你的理由：{case_info.get('plaintiff_reason', '')}
"""
        elif stage_key == "defendant_defense":
            return f"""
原告说：{case_info.get('plaintiff_claim', '')}，因为{case_info.get('plaintiff_reason', '')}
你的答辩意见：{case_info.get('defendant_response', '')}
"""
        elif stage_key == "plaintiff_evidence":
            return f"""
你的诉讼请求：{case_info.get('plaintiff_claim', '')}
"""
        elif stage_key == "defendant_cross":
            return f"""
原告证据：{json.dumps(self.context['evidence'], ensure_ascii=False)}
"""
        elif stage_key == "judge_question_plaintiff":
            return f"""
案件争议：
原告主张：{case_info.get('plaintiff_claim', '')}，理由：{case_info.get('plaintiff_reason', '')}
被告答辩：{case_info.get('defendant_response', '')}
庭审记录：{self.context['court_context']}

请向原告提出关键问题。
"""
        elif stage_key == "judge_question_defendant":
            return f"""
案件争议：
原告主张：{case_info.get('plaintiff_claim', '')}，理由：{case_info.get('plaintiff_reason', '')}
被告答辩：{case_info.get('defendant_response', '')}
庭审记录：{self.context['court_context']}

请向被告提出关键问题。
"""
        elif stage_key == "plaintiff_answer":
            return f"""
法官问题：{self.context.get('judge_question_plaintiff', '')}
你的诉讼请求：{case_info.get('plaintiff_claim', '')}
请回答法官的问题。
"""
        elif stage_key == "defendant_answer":
            return f"""
法官问题：{self.context.get('judge_question_defendant', '')}
你的答辩意见：{case_info.get('defendant_response', '')}
请回答法官的问题。
"""
        elif stage_key == "judge_inquiry":
            return f"""
案件争议：
原告主张：{case_info.get('plaintiff_claim', '')}，理由：{case_info.get('plaintiff_reason', '')}
被告答辩：{case_info.get('defendant_response', '')}
庭审记录：{self.context['court_context']}

请根据争议焦点和庭审情况提问。
"""
        elif stage_key == "debate":
            return f"""
原告主张：{case_info.get('plaintiff_claim', '')}，理由：{case_info.get('plaintiff_reason', '')}
被告答辩：{case_info.get('defendant_response', '')}
证据情况：{json.dumps(self.context['evidence'], ensure_ascii=False)}

请主持法庭辩论。
"""
        elif stage_key == "plaintiff_final":
            return f"""
你的诉讼请求：{case_info.get('plaintiff_claim', '')}
"""
        elif stage_key == "defendant_final":
            return f"""
你的答辩意见：{case_info.get('defendant_response', '')}
"""
        elif stage_key == "judge_judgment":
            return f"""
案件事实：
原告主张：{case_info.get('plaintiff_claim', '')}，理由：{case_info.get('plaintiff_reason', '')}
被告答辩：{case_info.get('defendant_response', '')}
证据情况：{json.dumps(self.context['evidence'], ensure_ascii=False)}
庭审记录：{self.context['court_context']}

请根据以上事实和证据做出判决。
"""
        return ""

    def append_history(self, record):
        self.history.append(record)
        self.context["history"].append(record)
        self.context["court_context"] = "\n".join([f"{item['role']}：{item['content']}" for item in self.context["history"]])

    def get_current_role(self):
        mapping = {
            0: "法官", 1: "法官", 2: "原告", 3: "法官", 4: "被告", 
            5: "法官", 6: "原告", 7: "法官", 8: "被告", 9: "法官",
            10: "原告", 11: "法官", 12: "被告", 13: "原告", 14: "被告", 15: "法官"
        }
        return mapping.get(self.stage, "系统")

    def _stage_result(self, output, role, stage_key):
        return {
            "output": output,
            "context": self.context,
            "current_role": role,  # 这里的 role 必须是当前应发言的人
            "current_stage": stage_key,
            "stage_progress": (self.stage / len(self.stage_order)) * 100
        }