import os
import json
import glob
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 통합 모델에서 가져오기
from models import JobPostingResult

# 환경 변수 로드 (.env 파일이 같은 폴더에 있어야 함)
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

def process_single_posting(raw_data: dict, client: genai.Client) -> JobPostingResult:
    """단일 공고 데이터를 AI로 분석하여 정제된 데이터를 반환합니다."""
    try:
        # 1. 이미지 다운로드
        image_bytes = None
        img_url = raw_data.get("detailImageUrl") or raw_data.get("jobPosting", {}).get("image", {}).get("contentUrl")
        
        if img_url:
            try:
                # 타임아웃 설정으로 무한 대기 방지
                img_res = requests.get(img_url, timeout=10)
                if img_res.status_code == 200:
                    image_bytes = img_res.content
            except Exception as e:
                print(f"⚠️ 이미지 다운로드 실패 ({img_url}): {e}")

        # 2. 프롬프트 구성
        prompt = f"""
        당신은 채용 공고 데이터 분석 전문가입니다.
        제공된 [JSON 데이터]와 [이미지(포스터)]를 종합하여 최종 데이터를 추출하세요.

        [지침]
        1. 'activityId', 'sourceUrl', 'postedAt', 'closingAt', 'companyName' 등 명확한 정보는 [JSON 데이터]를 우선하세요.
        2. 'qualifications' (지원자격/우대사항)은 [JSON 데이터]의 'description'과 [이미지]의 텍스트를 모두 분석하여 상세한 리스트로 만드세요.
        3. 'salary' (급여) 정보가 텍스트나 이미지에 있다면 반드시 추출하세요. (없으면 null)
        4. 'companyType'은 JSON에 있으면 쓰고, 없으면 null.
        5. 'employmentType'은 ["INTERN"], ["FULL_TIME"] 형태로 정확히 매핑하세요.

        [JSON 데이터]
        {json.dumps(raw_data, ensure_ascii=False)}
        """

        # 3. Gemini 요청 구성
        contents = [prompt]
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        # 4. AI 호출
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # 이미지 분석 가성비 모델
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobPostingResult
            )
        )
        
        return response.parsed

    except Exception as e:
        print(f"❌ Error processing ID {raw_data.get('activityId')}: {str(e)}")
        return None

def main():
    if not API_KEY:
        print("Error: GEMINI_API_KEY가 설정되지 않았습니다.")
        return

    client = genai.Client(api_key=API_KEY)
    
    # 예: ./raw_data 폴더에 있는 모든 json 파일을 읽음
    # (실제 환경에 맞춰 경로 수정 필요)
    # raw_files = glob.glob("./raw_data/*.json") 
    
    # 테스트용: 작성해주신 데이터 하나로 테스트
    sample_data = {
      "activityId": "298963",
      "sourceUrl": "https://linkareer.com/activity/298963",
      "detailImageUrl": "https://media-cdn.linkareer.com//se2editor/image/753494",
      "jobPosting": {
        "title": "지식교양 콘텐츠 조연출(인턴) 구인합니다.",
        "description": "지식교양 콘텐츠 조연출...",
        "employmentType": ["INTERN"],
        # ... 추가 데이터 ...
      }
    }
    
    # 리스트로 만들어서 일괄 처리 시뮬레이션
    raw_files_data = [sample_data] 
    processed_results = []

    print(f"🚀 총 {len(raw_files_data)}개의 공고 처리를 시작합니다...")

    for data in raw_files_data:
        result = process_single_posting(data, client)
        if result:
            processed_results.append(result.model_dump()) # dict로 변환
            print(f"✅ 처리 완료: {result.title}")
    
    # 결과 저장
    with open("processed_jobs.json", "w", encoding="utf-8") as f:
        json.dump(processed_results, f, ensure_ascii=False, indent=2)
    
    print(f"✨ 전체 완료! processed_jobs.json에 저장되었습니다.")

if __name__ == "__main__":
    main()