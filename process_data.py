import os
import json
import time
import requests
from google import genai
from google.genai import types

# 모델 임포트
from models import JobPostingResult

# --- AI 호출 함수 (재시도 로직 포함) ---
def call_gemini_with_retry(client, contents, retries=5):
    """429 Resource Exhausted 에러 발생 시 지수 백오프로 재시도"""
    base_delay = 5  # 기본 대기 20초 (Gemini Flash 기준)
    
    for attempt in range(retries):
        try:
            return client.models.generate_content(
                model="gemini-2.5-flash",  
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=JobPostingResult
                )
            )
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg:
                wait_time = base_delay * (2 ** attempt) 
                print(f"   ⏳ [Rate Limit] 할당량 초과. {wait_time}초 대기... ({attempt+1}/{retries})")
                time.sleep(wait_time)
            else:
                raise e
    return None

def process_single_posting(raw_data: dict, client: genai.Client) -> JobPostingResult | None:
    if "error" in raw_data or "jobPosting" not in raw_data:
        print(f"⚠️ [Skip] 유효하지 않은 데이터: ID {raw_data.get('activityId')}")
        return None

    try:
        print(f"🔄 처리 중... ID {raw_data.get('activityId')} ({raw_data['jobPosting'].get('title')})")

        # 1. 이미지 다운로드
        image_bytes = None
        img_url = raw_data.get("detailImageUrl") or raw_data.get("jobPosting", {}).get("image", {}).get("contentUrl")
        
        if img_url:
            try:
                img_res = requests.get(img_url, timeout=5)
                if img_res.status_code == 200:
                    image_bytes = img_res.content
            except:
                pass

        # 2. 프롬프트 구성 (담당업무 추가됨)
        prompt = f"""
        당신은 채용 공고 데이터 분석 AI입니다.
        [JSON 데이터]와 [이미지]를 분석하여 최종 데이터를 추출하세요.
        
        [규칙]
        1. JSON 데이터를 우선하되, 텍스트와 이미지 정보를 모두 종합하세요.
        2. 'responsibilities' (담당업무): "주요업무", "담당업무", "Role", "What you'll do" 등의 섹션을 찾아 리스트로 정리하세요.
        3. 'qualifications' (자격요건): "지원자격", "필수요건", "우대사항" 등을 찾아 리스트로 정리하세요.
        4. 'companyType': JSON에 없으면 기업명으로 추론하세요.
        
        [JSON 데이터]
        {json.dumps(raw_data, ensure_ascii=False)}
        """

        contents = [prompt]
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        # 3. 안전하게 호출
        response = call_gemini_with_retry(client, contents)
        
        if response:
            return response.parsed
        return None

    except Exception as e:
        print(f"❌ 처리 실패: {str(e)}")
        return None