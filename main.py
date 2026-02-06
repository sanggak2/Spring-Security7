import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from google import genai

# 데이터 모델 임포트
from models import CoffeeChatRequest, JobPostingResult, ResumeAnalysis, JobMatchingRequest, JobMatchResult

# 비즈니스 로직 모듈 임포트
from aiScreening import extract_text_from_pdf, extract_text_from_docx, analyze_resume_with_ai
from searchService import find_coffee_chat_targets
from process_data import process_single_posting
from matchingService import get_matcher
from resume_optimization import process_cv_optimization, OptimizationRequest


app = FastAPI()

# =================================================================
# 1. 이력서 분석 API
# =================================================================
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

# =================================================================
# 2. 커피챗 추천 API
# =================================================================
@app.post("/coffee-chat/generate")
async def generate_coffee_chat_info(request: CoffeeChatRequest):
    serpapi_key = os.environ.get("SERPAPI_KEY")
    
    if not serpapi_key:
        raise HTTPException(status_code=500, detail="SERPAPI_KEY not set")

    result = find_coffee_chat_targets(request, serpapi_key)
    return result

# =================================================================
# 3. 채용 공고 AI 가공 API (DB 저장 X, 분석 결과 반환 O)
# =================================================================
@app.post("/job-posting/analyze", response_model=JobPostingResult)
async def analyze_job_posting(raw_data: Dict[str, Any] = Body(...)):
    """
    [Internal] Raw JSON 데이터를 받아 AI로 정제된 결과를 반환합니다.
    (DB 저장은 하지 않습니다.)
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server Error: GEMINI_API_KEY not configured")

    client = genai.Client(api_key=api_key)

    # 로직 실행
    result = process_single_posting(raw_data, client)

    if not result:
        raise HTTPException(status_code=500, detail="AI 분석에 실패했습니다. (데이터 확인 필요)")

    # [변경] DB 저장 로직(save_job_posting) 삭제됨.
    # 바로 결과만 반환합니다.
    return result

# =================================================================
# 4. 직무 적합도 추천 API
# =================================================================
@app.post("/jobs/recommend", response_model=List[JobMatchResult])
async def recommend_jobs(request: JobMatchingRequest):
    """
    내 이력서(User Profile)와 공고 리스트(Job Postings)를 주면,
    AI가 적합도를 계산하여 점수가 높은 순으로 정렬해 줍니다.
    """
    try:
        matcher = get_matcher()
        results = matcher.calculate_scores(request.user_profile, request.job_postings)
        return results
    except Exception as e:
        print(f"매칭 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"매칭 분석 실패: {str(e)}")

@app.post("/cv/optimize")
async def optimize_cv_endpoint(request: OptimizationRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set")
    
    return await process_cv_optimization(request, api_key)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)