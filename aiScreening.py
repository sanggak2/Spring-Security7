import io
import os
import pypdf
from docx import Document
from google import genai
from google.genai import types
from fastapi import HTTPException
from models import ResumeAnalysis  # models.py에서 가져옴

# --- 1. 파일 텍스트 추출 로직 ---
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

# --- 2. Gemini AI 호출 로직 ---
def analyze_resume_with_ai(resume_text: str, api_key: str) -> ResumeAnalysis:
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