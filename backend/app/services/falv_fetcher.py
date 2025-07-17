import requests
import time
from datetime import datetime

class CourtCaseDataFetcher:
    def __init__(self):
        self.base_url = "https://eastlawlibrary.court.gov.cn/court-digital-library-search/sword/search/ChineseHistoricalMajorCaseService/getCaseListByCountryTypeAndCaseType"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://eastlawlibrary.court.gov.cn",
            "Referer": "https://eastlawlibrary.court.gov.cn/court-digital-library-search/page/caseFilesDatabase/historicMajorCases.html"
        }
        # 案例类型映射
        self.case_types = {
            "刑事案件": "31",
            "民事案件": "32",
            "行政案件": "33",
            "环资案件": "34",
            "商事案件": "35"
        }
        self.country_type = "3"  # 根据请求文件，countryType固定为3

    def fetch_cases(self, case_type_name, start=0, end=5):
        """获取指定类型的案例数据"""
        if case_type_name not in self.case_types:
            raise ValueError(f"不支持的案例类型: {case_type_name}")
        
        case_type = self.case_types[case_type_name]
        pd_t = self.generate_pd_t()
        
        params = {
            "PD_T":  pd_t # 这个参数在每个请求中都有，但具体含义不明
        }
        
        data = {
            "countryType": self.country_type,
            "caseType": case_type,
            "start": start,
            "end": end
        }
        
        try:
            response = requests.post(self.base_url, params=params, data=data, headers=self.headers)
            response.raise_for_status()  # 检查请求是否成功
            
            # 解析JSON响应
            result = response.json()
            
            if result.get("status") == "200":
                model = result["model"]
                # 为每个案例添加URL
                if "caseList" in model and isinstance(model["caseList"], list):
                    # 使用正确的URL格式: imageCaseDetail.html?countryType=3&caseId=xxx
                    base_url = "https://eastlawlibrary.court.gov.cn/court-digital-library-search/page/caseFilesDatabase/imageCaseDetail.html"
                    for case in model["caseList"]:
                        if "caseId" in case:
                            case["caseUrl"] = f"{base_url}?countryType={self.country_type}&caseId={case['caseId']}"
                return model
            else:
                print(f"请求失败: {result.get('msg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"获取案例数据时出错: {e}")
            return None
    
    def get_all_case_types(self):
        """获取所有案例类型的案例数据"""
        all_cases = {}
        for case_type_name in self.case_types:
            print(f"正在获取{case_type_name}案例...")
            cases = self.fetch_cases(case_type_name)
            if cases:
                all_cases[case_type_name] = cases
            else:
                all_cases[case_type_name] = {"caseList": [], "countAll": 0}
        
        return all_cases

    def generate_pd_t(self):
        """生成基于当前时间的 PD_T 参数（格式：yyyyMMddHHmmssSSS）"""
        now = datetime.now()
        pd_t = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}"
        return pd_t

# 使用示例
if __name__ == "__main__":
    fetcher = CourtCaseDataFetcher()
    
    # 获取所有类型的案例数据
    all_cases = fetcher.get_all_case_types()
    print(all_cases)
