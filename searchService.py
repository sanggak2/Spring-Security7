from serpapi import GoogleSearch
from fastapi import HTTPException
from models import CoffeeChatRequest

# --- 커피챗 대상 찾기 로직 (SerpApi) ---
def find_coffee_chat_targets(request: CoffeeChatRequest, api_key: str):
    try:
        # 1. 검색 쿼리 생성
        skills = " ".join(request.tech_stack[:2]) # 상위 2개 스택만 사용
        search_query = f"site:linkedin.com/in/ {request.company_name} {request.position} {skills}"

        # 2. SerpApi 파라미터 설정
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": api_key,
            "num": 3,       # 상위 3명만
            "gl": "kr",     # 한국 지역
            "hl": "ko"      # 한국어
        }

        # 3. 검색 실행
        search = GoogleSearch(params)
        results = search.get_dict()

        # 4. 결과 정제
        real_contacts = []
        if "organic_results" in results:
            for item in results["organic_results"]:
                real_contacts.append({
                    "name_and_title": item.get("title"),
                    "profile_url": item.get("link"),
                    "snippet": item.get("snippet")
                })

        if not real_contacts:
            return {
                "status": "empty",
                "query": search_query,
                "message": "검색 결과가 없습니다."
            }

        return {
            "status": "success",
            "query": search_query,
            "results": real_contacts
        }

    except Exception as e:
        print(f"Search API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"커피챗 검색 중 오류: {str(e)}")