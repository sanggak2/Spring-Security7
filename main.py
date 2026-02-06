import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from google import genai

# 데이터 모델 임포트
from models import CoffeeChatRequest, JobPostingResult

# 비즈니스 로직 모듈 임포트
from aiScreening import extract_text_from_pdf, extract_text_from_docx, analyze_resume_with_ai
from searchService import find_coffee_chat_targets
from process_data import process_single_posting

app = FastAPI()

# --- 1. 이력서 분석 API ---
@app.post("/analyze_file")
async def analyze_resume_file(file: UploadFile = File(...)):
    content = await file.read()
    resume_text = ""

    if file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(content)
    elif file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(content)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    if len(resume_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="파일 내용 부족")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set")

    result = analyze_resume_with_ai(resume_text, api_key)
    return result

# --- 2. 커피챗 추천 API ---
@app.post("/coffee-chat/generate")
async def generate_coffee_chat_info(request: CoffeeChatRequest):
    serpapi_key = os.environ.get("SERPAPI_KEY")
    
    if not serpapi_key:
        raise HTTPException(status_code=500, detail="SERPAPI_KEY not set")

    # [변경] cx 없이 키만 전달
    result = find_coffee_chat_targets(request, serpapi_key)
    
    return result

@app.post("/job-posting/analyze", response_model=JobPostingResult)
async def analyze_job_posting(raw_data: Dict[str, Any] = Body(...)):
    """
    [Internal/Admin] Raw JSON 데이터를 받아 AI로 정제된 공고 데이터를 반환합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server Error: GEMINI_API_KEY not configured")

    client = genai.Client(api_key=api_key)

    # process_data.py의 로직 재사용
    result = process_single_posting(raw_data, client)

    if not result:
        raise HTTPException(status_code=500, detail="AI 분석에 실패했습니다. (데이터 확인 필요)")

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)