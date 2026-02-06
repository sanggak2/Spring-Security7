from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# 1. 이력서 분석용 모델 (Resume Analysis)
# ==========================================
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

# ==========================================
# 2. 커피챗 추천용 모델 (Coffee Chat)
# ==========================================
class CoffeeChatRequest(BaseModel):
    company_name: str = Field(description="관심 기업명")
    position: str = Field(description="희망 직무")
    tech_stack: List[str] = Field(description="본인의 주요 기술 스택")

# ==========================================
# 3. 채용 공고 가공용 모델 (Job Posting ETL)
# ==========================================
class SalaryInfo(BaseModel):
    value: int = Field(description="급여 금액 (숫자만)")
    unit: str = Field(description="단위 (MONTH, YEAR, HOURLY 중 하나)")
    currency: str = Field(description="통화", default="KRW")

class JobPostingResult(BaseModel):
    activityId: str = Field(description="공고 ID (원본 유지)")
    sourceUrl: str = Field(description="원본 링크 (원본 유지)")
    title: str = Field(description="공고 제목")
    companyName: str = Field(description="기업명")
    companyType: Optional[str] = Field(None, description="기업 형태")
    
    companyLogo: Optional[str] = Field(None)
    posterUrl: Optional[str] = Field(None)
    
    postedAt: Optional[str] = Field(None, description="게시일 (ISO 8601)")
    closingAt: Optional[str] = Field(None, description="마감일 (ISO 8601)")
    
    location: str = Field(description="근무지 전체 주소")
    employmentType: List[str] = Field(description="고용 형태")
    experienceLevel: List[str] = Field(description="경력 요건")
    
    responsibilities: List[str] = Field(description="담당 업무, 주요 업무, Role 리스트")
    qualifications: List[str] = Field(description="지원 자격, 필수 요건, 우대 사항 리스트")
    
    salary: Optional[SalaryInfo] = Field(None, description="급여 정보")
    description: str = Field(description="상세 내용 요약")