from pydantic import BaseModel, Field
from typing import Literal, Dict

class UserInfo(BaseModel):
    name: str = Field(..., description="姓名/单位名称")
    id_type: str = Field(..., description="证件类型")
    id_number: str = Field(..., description="证件号码")
    address: str = Field(..., description="住址/地址")
    contact: str = Field(..., description="联系方式")

class CaseInfo(BaseModel):
    case_type: str = Field(..., description="案件类型")
    facts: str = Field(..., description="案件事实描述")
    legal_basis: str = Field(None, description="法律依据")

class LawsuitRequest(BaseModel):
    """起诉状生成请求"""
    plaintiff: UserInfo = Field(..., description="原告信息")
    defendant: UserInfo = Field(..., description="被告信息")
    case_info: CaseInfo = Field(..., description="案件信息")
    claims: list[str] = Field(..., description="诉讼请求")
    court: str = Field(..., description="受理法院")