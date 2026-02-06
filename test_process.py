import os
import json
import time  # [추가] 시간 지연을 위해 필요
import requests
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 데이터 모델 (그대로 유지) ---
class SalaryInfo(BaseModel):
    value: int = Field(description="급여 금액 (숫자만)")
    unit: str = Field(description="단위 (MONTH, YEAR, HOURLY 중 하나)")
    currency: str = Field(description="통화", default="KRW")

class JobPostingResult(BaseModel):
    activityId: str = Field(description="공고 ID")
    sourceUrl: str = Field(description="원본 링크")
    title: str = Field(description="공고 제목")
    companyName: str = Field(description="기업명")
    companyType: Optional[str] = Field(None, description="기업 형태")
    companyLogo: Optional[str] = Field(None)
    posterUrl: Optional[str] = Field(None)
    postedAt: Optional[str] = Field(None, description="게시일")
    closingAt: Optional[str] = Field(None, description="마감일")
    location: str = Field(description="근무지")
    employmentType: List[str] = Field(description="고용 형태")
    experienceLevel: List[str] = Field(description="경력 요건")
    qualifications: List[str] = Field(description="지원 자격 및 우대 사항 리스트")
    salary: Optional[SalaryInfo] = Field(None, description="급여 정보")
    description: str = Field(description="상세 내용 요약")

# --- [핵심 수정] 재시도 로직이 포함된 AI 호출 함수 ---
def call_gemini_with_retry(client, contents, retries=5):
    """429 에러 발생 시 지수 백오프(Exponential Backoff)로 재시도합니다."""
    base_delay = 5  # 시작 대기 시간 (5초)
    
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
            # 429(Rate Limit) 또는 503(Service Unavailable) 에러인 경우
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg:
                wait_time = base_delay+1 # 5초 -> 10초 -> 20초 -> 40초...
                print(f"   ⏳ 429 에러 감지 (요청 과다). {wait_time}초 대기 후 재시도합니다... ({attempt+1}/{retries})")
                time.sleep(wait_time)
            else:
                # 다른 에러면 바로 실패 처리
                raise e
    return None

def process_single_posting(raw_data: dict, client: genai.Client) -> Optional[JobPostingResult]:
    if "error" in raw_data or "jobPosting" not in raw_data:
        print(f"⚠️ [Skip] 유효하지 않은 데이터: ID {raw_data.get('activityId')}")
        return None

    try:
        print(f"🔄 처리 중... ID {raw_data.get('activityId')} ({raw_data['jobPosting'].get('title')})")

        image_bytes = None
        img_url = raw_data.get("detailImageUrl") or raw_data.get("jobPosting", {}).get("image", {}).get("contentUrl")
        
        if img_url:
            try:
                img_res = requests.get(img_url, timeout=5)
                if img_res.status_code == 200:
                    image_bytes = img_res.content
            except:
                pass

        prompt = f"""
        당신은 채용 공고 데이터 분석 AI입니다.
        [JSON 데이터]와 [이미지]를 분석하여 최종 데이터를 추출하세요.
        
        [규칙]
        1. JSON 데이터를 우선하되, 'qualifications'와 'salary'는 이미지 텍스트까지 분석해서 채우세요.
        2. 'companyType'은 JSON에 없으면 기업명으로 추론하세요 (예: (주)대학내일 -> 중견기업/중소기업).
        
        [JSON 데이터]
        {json.dumps(raw_data, ensure_ascii=False)}
        """

        contents = [prompt]
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        # [수정] 재시도 함수 사용
        response = call_gemini_with_retry(client, contents)
        
        if response:
            return response.parsed
        return None

    except Exception as e:
        print(f"❌ 최종 실패: {str(e)}")
        return None

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Error: .env 파일에 GEMINI_API_KEY를 설정해주세요.")
        exit()

    client = genai.Client(api_key=API_KEY)

    # (이전과 동일한 입력 데이터 test_input_data 사용)
    # ... 여기에 test_input_data 리스트를 넣어주세요 ...
    # 편의상 생략했습니다. 위에서 쓰신 리스트 그대로 두시면 됩니다.
    test_input_data = [

    {

      "activityId": "299032",

      "sourceUrl": "https://linkareer.com/activity/299032",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[대한FSS] 충북 청주지역 인턴영양사 채용",

        "datePosted": "2026-01-30T03:22:51.000Z",

        "validThrough": "2026-03-01T14:59:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "05510",

              "streetAddress": "서울 송파구 올림픽로 299",

              "addressLocality": "송파구",

              "addressRegion": "서울",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "대한FSS",

          "sameAs": "http://www.dhfss.co.kr/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753705"

        },

        "description": "[대한FSS] 충북 청주지역 인턴영양사 채용\n[지원자격]\n모집직무: 서비스\n근무지: 서울 송파구\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "초대졸",

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "215-87-47646"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753705",

          "caption": "[대한FSS] 충북 청주지역 인턴영양사 채용"

        }

      },

      "fetchedAt": "2026-02-06T15:18:08.818Z",

      "recruitCategory": ": 서비스\\n근무지: 서울 송파구\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"초대졸\",\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"215-87-47646\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753705\",\"caption\":\"[대한FSS] 충북 청주지역 인턴영양사 채용\"}}"

    },

    {

      "activityId": "298990",

      "sourceUrl": "https://linkareer.com/activity/298990",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[한국청소년정책연구원] 체험형청년인턴(중증장애인) 채용 공고",

        "datePosted": "2026-01-30T02:01:05.000Z",

        "validThrough": "2026-02-13T08:00:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "30147",

              "streetAddress": "세종특별자치시 시청대로 370",

              "addressLocality": "",

              "addressRegion": "세종특별자치시",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "한국청소년정책연구원",

          "sameAs": "https://www.nypi.re.kr/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753574"

        },

        "description": "[한국청소년정책연구원] 체험형청년인턴(중증장애인) 채용 공고\n[지원자격]\n모집직무: 경영/사무\n근무지: 세종\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "학력무관",

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "229-82-00591"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753574",

          "caption": "[한국청소년정책연구원] 체험형청년인턴(중증장애인) 채용 공고"

        }

      },

      "fetchedAt": "2026-02-06T15:18:10.024Z",

      "detailImageUrl": "https://media-cdn.linkareer.com//se2editor/image/753572",

      "companyType": "공공기관/공기업",

      "recruitCategory": ": 경영/사무\\n근무지: 세종\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"학력무관\",\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"229-82-00591\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753574\",\"caption\":\"[한국청소년정책연구원] 체험형청년인턴(중증장애인) 채용 공고\"}}"

    },

    {

      "activityId": "298979",

      "sourceUrl": "https://linkareer.com/activity/298979",

      "error": "No JobPosting JSON-LD found",

      "fetchedAt": "2026-02-06T15:18:10.944Z"

    },

    {

      "activityId": "298977",

      "sourceUrl": "https://linkareer.com/activity/298977",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[웹케시] 사업기획, 상품기획 신입/경력직 채용",

        "datePosted": "2026-01-30T01:39:33.000Z",

        "validThrough": "2026-02-08T14:59:59.999Z",

        "employmentType": [

          "INTERN",

          "FULL_TIME"

        ],

        "experienceRequirements": [

          "신입",

          "경력"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "07228",

              "streetAddress": "서울 영등포구 영신로 220",

              "addressLocality": "영등포구",

              "addressRegion": "서울",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "웹케시",

          "sameAs": "https://www.webcash.co.kr/2025/MAIN.html",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753531"

        },

        "description": "[웹케시] 사업기획, 상품기획 신입/경력직 채용\n[지원자격]\n모집직무: 경영/사무,무역/유통\n근무지: 서울 영등포구\n고용형태: 신입,경력\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "대졸",

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "214-86-35102"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753531",

          "caption": "[웹케시] 사업기획, 상품기획 신입/경력직 채용"

        }

      },

      "fetchedAt": "2026-02-06T15:18:12.215Z",

      "detailImageUrl": "https://media-cdn.linkareer.com//se2editor/image/753530",

      "companyType": "중소기업",

      "recruitCategory": ": 경영/사무,무역/유통\\n근무지: 서울 영등포구\\n고용형태: 신입,경력\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"대졸\",\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"214-86-35102\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753531\",\"caption\":\"[웹케시] 사업기획, 상품기획 신입/경력직 채용\"}}"

    },

    {

      "activityId": "298963",

      "sourceUrl": "https://linkareer.com/activity/298963",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "지식교양 콘텐츠 조연출(인턴) 구인합니다.",

        "datePosted": "2026-01-30T01:23:15.000Z",

        "validThrough": "2026-02-09T14:59:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "03708",

              "streetAddress": "서울 서대문구 연희맛로 18",

              "addressLocality": "서대문구",

              "addressRegion": "서울",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "큰그림 연구소",

          "sameAs": "http://bigpicturelab.net/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753494"

        },

        "description": "지식교양 콘텐츠 조연출(인턴) 구인합니다.\n[지원자격]\n모집직무: 미디어\n근무지: 서울 서대문구\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "학력무관",

        "baseSalary": {

          "@type": "MonetaryAmount",

          "currency": "KRW",

          "value": {

            "@type": "QuantitativeValue",

            "minValue": 2300000,

            "maxValue": 2300000,

            "unitText": "MONTH"

          }

        },

        "workHours": [

          "오전",

          "오후"

        ],

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "150-03-00553"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753494",

          "caption": "지식교양 콘텐츠 조연출(인턴) 구인합니다."

        }

      },

      "fetchedAt": "2026-02-06T15:18:15.562Z",

      "companyType": "중소기업",

      "recruitCategory": ": 미디어\\n근무지: 서울 서대문구\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"학력무관\",\"baseSalary\":{\"@type\":\"MonetaryAmount\",\"currency\":\"KRW\",\"value\":{\"@type\":\"QuantitativeValue\",\"minValue\":2300000,\"maxValue\":2300000,\"unitText\":\"MONTH\"}},\"workHours\":[\"오전\",\"오후\"],\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"150-03-00553\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753494\",\"caption\":\"지식교양 콘텐츠 조연출(인턴) 구인합니다.\"}}"

    },

    {

      "activityId": "298957",

      "sourceUrl": "https://linkareer.com/activity/298957",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[SK플라즈마] 안동공장 혈액제제 정제 및 공정관리 신입(전환형 인턴)",

        "datePosted": "2026-01-30T01:11:17.000Z",

        "validThrough": "2026-02-11T14:59:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "36618",

              "streetAddress": "경북 안동시 풍산읍 산업단지길 157",

              "addressLocality": "안동시",

              "addressRegion": "경북",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "SK플라즈마",

          "sameAs": "https://www.skplasma.com/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753488"

        },

        "description": "[SK플라즈마] 안동공장 혈액제제 정제 및 공정관리 신입(전환형 인턴)\n[지원자격]\n모집직무: 생산/제조,연구개발/설계\n근무지: 경상 안동시\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "대졸",

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "778-86-00034"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753488",

          "caption": "[SK플라즈마] 안동공장 혈액제제 정제 및 공정관리 신입(전환형 인턴)"

        }

      },

      "fetchedAt": "2026-02-06T15:18:17.043Z",

      "detailImageUrl": "https://media-cdn.linkareer.com//se2editor/image/753486",

      "companyType": "대기업",

      "recruitCategory": ": 생산/제조,연구개발/설계\\n근무지: 경상 안동시\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"대졸\",\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"778-86-00034\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753488\",\"caption\":\"[SK플라즈마] 안동공장 혈액제제 정제 및 공정관리 신입(전환형 인턴)\"}}"

    },

    {

      "activityId": "298956",

      "sourceUrl": "https://linkareer.com/activity/298956",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[대학내일] 마케팅(AE)_20대연구소_인턴(체험형)",

        "datePosted": "2026-01-30T01:11:00.000Z",

        "validThrough": "2026-02-09T06:00:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "04156",

              "streetAddress": "서울 마포구 독막로 331",

              "addressLocality": "마포구",

              "addressRegion": "서울",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "(주)대학내일",

          "sameAs": "https://corp.univ.me/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753484"

        },

        "description": "[대학내일] 마케팅(AE)_20대연구소_인턴(체험형)\n[지원자격]\n모집직무: 마케팅/광고/홍보\n근무지: 서울 마포구\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "학력무관",

        "workHours": [

          "오전",

          "오후"

        ],

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "101-86-28789"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753484",

          "caption": "[대학내일] 마케팅(AE)_20대연구소_인턴(체험형)"

        }

      },

      "fetchedAt": "2026-02-06T15:18:18.385Z",

      "recruitCategory": ": 마케팅/광고/홍보\\n근무지: 서울 마포구\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"학력무관\",\"workHours\":[\"오전\",\"오후\"],\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"101-86-28789\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753484\",\"caption\":\"[대학내일] 마케팅(AE)_20대연구소_인턴(체험형)\"}}"

    },

    {

      "activityId": "298954",

      "sourceUrl": "https://linkareer.com/activity/298954",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[대학내일] 마케팅(AE)_익스피리언스플래닝4팀_인턴(체험형)",

        "datePosted": "2026-01-30T01:02:35.000Z",

        "validThrough": "2026-02-09T06:00:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "04156",

              "streetAddress": "서울 마포구 독막로 331",

              "addressLocality": "마포구",

              "addressRegion": "서울",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "(주)대학내일",

          "sameAs": "https://corp.univ.me/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753481"

        },

        "description": "[대학내일] 마케팅(AE)_익스피리언스플래닝4팀_인턴(체험형)\n[지원자격]\n모집직무: 마케팅/광고/홍보\n근무지: 서울 마포구\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "학력무관",

        "workHours": [

          "오전",

          "오후"

        ],

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "101-86-28789"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753481",

          "caption": "[대학내일] 마케팅(AE)_익스피리언스플래닝4팀_인턴(체험형)"

        }

      },

      "fetchedAt": "2026-02-06T15:18:20.506Z",

      "recruitCategory": ": 마케팅/광고/홍보\\n근무지: 서울 마포구\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"학력무관\",\"workHours\":[\"오전\",\"오후\"],\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"101-86-28789\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753481\",\"caption\":\"[대학내일] 마케팅(AE)_익스피리언스플래닝4팀_인턴(체험형)\"}}"

    },

    {

      "activityId": "298951",

      "sourceUrl": "https://linkareer.com/activity/298951",

      "jobPosting": {

        "@context": "https://schema.org",

        "@type": "JobPosting",

        "title": "[대학내일ES] 디자이너(Design)_크리에이티브팀_인턴(체험형)",

        "datePosted": "2026-01-30T00:59:19.000Z",

        "validThrough": "2026-02-09T06:00:59.999Z",

        "employmentType": [

          "INTERN"

        ],

        "experienceRequirements": [

          "신입"

        ],

        "jobLocation": [

          {

            "@type": "Place",

            "address": {

              "@type": "PostalAddress",

              "postalCode": "04156",

              "streetAddress": "서울 마포구 독막로 331",

              "addressLocality": "마포구",

              "addressRegion": "서울",

              "addressCountry": "KR"

            }

          }

        ],

        "hiringOrganization": {

          "@type": "Organization",

          "name": "(주)대학내일",

          "sameAs": "https://corp.univ.me/",

          "logo": "https://media-cdn.linkareer.com/activity_manager/logos/753477"

        },

        "description": "[대학내일ES] 디자이너(Design)_크리에이티브팀_인턴(체험형)\n[지원자격]\n모집직무: 디자인\n근무지: 서울 마포구\n고용형태: 신입\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다",

        "educationRequirements": "학력무관",

        "workHours": [

          "오전",

          "오후"

        ],

        "identifier": {

          "@type": "PropertyValue",

          "propertyID": "사업자등록번호",

          "value": "101-86-28789"

        },

        "image": {

          "@type": "ImageObject",

          "contentUrl": "https://media-cdn.linkareer.com/activity_manager/logos/753477",

          "caption": "[대학내일ES] 디자이너(Design)_크리에이티브팀_인턴(체험형)"

        }

      },

      "fetchedAt": "2026-02-06T15:18:23.175Z",

      "recruitCategory": ": 디자인\\n근무지: 서울 마포구\\n고용형태: 신입\\n채용정보 상세 내용 및 즉시지원은 링커리어에서 가능합니다\",\"educationRequirements\":\"학력무관\",\"workHours\":[\"오전\",\"오후\"],\"identifier\":{\"@type\":\"PropertyValue\",\"propertyID\":\"사업자등록번호\",\"value\":\"101-86-28789\"},\"image\":{\"@type\":\"ImageObject\",\"contentUrl\":\"https://media-cdn.linkareer.com/activity_manager/logos/753477\",\"caption\":\"[대학내일ES] 디자이너(Design)_크리에이티브팀_인턴(체험형)\"}}"

    }

    ]
    print("--- 🚀 데이터 가공 테스트 (Rate Limit 대응 버전) 시작 ---")
    
    final_results = []
    
    for raw_item in test_input_data:
        result = process_single_posting(raw_item, client)
        if result:
            final_results.append(result.model_dump())
            print(f"   ✅ 성공! ({result.companyName})")
        
        # [중요] 한 건 처리 후 강제로 2초 휴식 (Rate Limit 예방)
        time.sleep(2)

    print("\n--- ✅ 최종 결과 (JSON Output) ---")
    print(json.dumps(final_results, indent=2, ensure_ascii=False))