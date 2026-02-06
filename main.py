import os
from fastapi import FastAPI, HTTPException, UploadFile, File

# 모델 임포트
from models import CoffeeChatRequest

# [변경] 로직 파일 분리 임포트
from aiScreening import extract_text_from_pdf, extract_text_from_docx, analyze_resume_with_ai
from searchService import find_coffee_chat_targets  # <-- 새로 만든 파일에서 가져옴!

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
    google_api_key = os.environ.get("GOOGLE_API_KEY_2")
    google_cx = os.environ.get("GOOGLE_CX")
    
    # 키가 하나라도 없으면 에러
    if not google_api_key or not google_cx:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY_2 or GOOGLE_CX not set")

    # searchService에 키 2개를 전달
    result = find_coffee_chat_targets(request, google_api_key, google_cx)
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)