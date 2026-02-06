import requests
from fastapi import HTTPException
from models import CoffeeChatRequest

def find_coffee_chat_targets(request: CoffeeChatRequest, api_key: str, cx: str):
    try:
        # 1. 검색 쿼리 생성
        skills = " ".join(request.tech_stack[:2])
        # LinkedIn 프로필 검색에 최적화된 쿼리
        search_query = f"site:linkedin.com/in/ {request.company_name} {request.position} {skills}"

        # 2. Google Custom Search API 호출
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,  # main.py에서 넘겨준 GOOGLE_API_KEY_2
            "cx": cx,        # main.py에서 넘겨준 GOOGLE_CX
            "q": search_query,
            "num": 3         # 결과 개수
        }

        response = requests.get(url, params=params)
        
        # API 호출 실패 시 예외 처리
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Google Search Error: {response.text}")

        result_data = response.json()

        # 3. 결과 정제
        real_contacts = []
        if "items" in result_data:
            for item in result_data["items"]:
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
        print(f"Search Service Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"커피챗 검색 중 오류: {str(e)}")