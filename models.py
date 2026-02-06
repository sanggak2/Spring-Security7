from pydantic import BaseModel, Field
from typing import List, Optional

# --- 이력서 데이터 구조  ---
class Education(BaseModel):
    university: str = Field(description="대학교 이름")
    major: str = Field(description="전공")
    graduation_year: str = Field(description="졸업년도")
    gpa: Optional[str] = Field(None, description="학점")

class Project(BaseModel):
    name: str = Field(description="프로젝트 명")
    description: str = Field(description="프로젝트 설명")
    tech_stack: List[str] = Field(description="사용 기술 스택")

class ResumeAnalysis(BaseModel):
    name: str = Field(description="이름")
    email: str = Field(description="이메일")
    phone: str = Field(description="전화번호")
    desired_job: str = Field(description="희망 직무")
    educations: List[Education]
    skills: List[str] = Field(description="보유 기술 스택 목록")
    experiences: List[str] = Field(description="경력 사항 요약")
    certificates: List[str] = Field(description="자격증 목록")
    projects: List[Project]
    awards: List[str] = Field(description="수상 경력")

# --- [신규] 커피챗 데이터 구조 (추가됨) ---
class CoffeeChatRequest(BaseModel):
    company_name: str = Field(description="관심 기업명")
    position: str = Field(description="희망 직무")
    tech_stack: List[str] = Field(description="본인의 주요 기술 스택")