import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from services import extract_text_from_pdf, extract_text_from_docx, analyze_resume_with_ai

app = FastAPI()

@app.post("/analyze_file")
async def analyze_resume_file(file: UploadFile = File(...)):
    # 1. 파일 읽기
    content = await file.read()
    resume_text = ""

    # 2. 확장자에 따라 텍스트 추출 (Service 호출)
    if file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(content)
    elif file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(content)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (.pdf, .docx 만 가능)")

    if len(resume_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출할 수 없습니다.")

    # 3. API Key 확인
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key not set")

    # 4. AI 분석 요청 (Service 호출)
    result = analyze_resume_with_ai(resume_text, api_key)
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)