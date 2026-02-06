import os
import json
import re
import asyncio
from google import genai
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# 요청 모델 정의
class OptimizationRequest(BaseModel):
    raw_cv: Dict[str, Any]
    job_description: str

# 로직 함수 (main.py에서 호출)
async def process_cv_optimization(request: OptimizationRequest, api_key: str):
    client = genai.Client(api_key=api_key)
    max_retries = 1
    
    for attempt in range(max_retries + 1):
        try:
            prompt = f"""
            당신은 IT 전문 커리어 코치입니다. 제공된 'raw_cv'를 'job_description'에 맞춰 최적화하세요.
            반드시 {{ 로 시작해서 }} 로 끝나는 순수한 JSON 데이터만 출력하세요. 부연 설명은 하지 마세요.

            기업 공고(JD):
            {request.job_description}

            원본 데이터(raw_cv):
            {json.dumps(request.raw_cv, ensure_ascii=False)}
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            res_text = response.text.strip()
            # JSON 추출 (마크다운 코드 블록 제거 등)
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()

            # 정규식으로 JSON 부분만 확실히 추출
            json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
            
            if not json_match:
                raise ValueError("AI가 유효한 JSON을 생성하지 못했습니다.")
                
            optimized_cv = json.loads(json_match.group())

            return {
                "status": "success",
                "optimized_cv": optimized_cv
            }

        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries:
                print(f"⚠️ Quota Exceeded. Retrying in 1 second... (Attempt {attempt + 1})")
                await asyncio.sleep(1)
                continue
            
            print(f"❌ Optimization Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"최적화 오류: {error_msg}")