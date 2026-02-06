import os
import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from google.genai import types
import pypdf
from docx import Document

app = FastAPI()

# --- [기존] 이력서 데이터 구조 (변경 없음) ---
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

# --- [신규] 파일에서 텍스트 추출하는 함수들 ---

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 읽기 실패: {str(e)}")

def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX 읽기 실패: {str(e)}")


# --- [수정] 파일 업로드 엔드포인트 ---
@app.post("/analyze_file")
async def analyze_resume_file(file: UploadFile = File(...)):
    # 1. 파일 확장자 확인 및 텍스트 추출
    content = await file.read() # 파일 내용 읽기 (바이트 상태)
    resume_text = ""

    if file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(content)
    elif file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(content)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (.pdf, .docx 만 가능)")

    # 텍스트가 너무 짧으면 에러 처리 (선택사항)
    if len(resume_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출할 수 없습니다.")

    # 2. Gemini API 호출 (기존 로직과 동일)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key not set")

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
        다음 이력서 텍스트를 분석하여 정보를 추출해주세요.
        명시되지 않은 정보는 null 또는 빈 리스트로 처리하세요.
        
        [이력서 텍스트]
        {resume_text}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResumeAnalysis
            )
        )

        return response.parsed

    except Exception as e:
        print(f"AI Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI 분석 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)