import logging
from sentence_transformers import SentenceTransformer

# 로깅 설정
logger = logging.getLogger("uvicorn")

class JobMatcher:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobMatcher, cls).__new__(cls)
        return cls._instance

    def load_model(self):
        """모델이 없을 때만 로딩 (Lazy Loading)"""
        if self._model is None:
            logger.info("⚙️ [Cold Start] 모델을 메모리에 올리는 중... (약 3~5초 소요)")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ 모델 로딩 완료!")
    
    def calculate_scores(self, user, jobs):
        # 계산 직전에 모델 로딩 확인
        self.load_model()
        if not jobs:
            return []

        # 1. 텍스트 변환
        user_text = self._create_user_text(user)
        job_texts = [self._create_job_text(job) for job in jobs]

        # 2. 임베딩 (Vectorization)
        # 사용자 벡터 (1, 384)
        user_vector = self._model.encode([user_text])
        # 공고 벡터들 (N, 384)
        job_vectors = self._model.encode(job_texts)

        # 3. 코사인 유사도 계산
        similarities = cosine_similarity(user_vector, job_vectors)[0]

        # 4. 결과 매핑
        results = []
        for i, score in enumerate(similarities):
            match_score = round(float(score) * 100, 1)
            
            # AI 분석 코멘트 생성
            if match_score >= 70:
                analysis = "🌟 AI 강력 추천 (직무/스택 일치도 매우 높음)"
            elif match_score >= 50:
                analysis = "✅ 적합 (핵심 역량 부합)"
            elif match_score >= 30:
                analysis = "🤔 검토 필요 (일부 연관성 있음)"
            else:
                analysis = "⚠️ 관련성 낮음"

            # 원본 데이터에 점수와 분석 추가
            job_data = jobs[i].model_dump()
            results.append(JobMatchResult(
                **job_data,
                match_score=match_score,
                ai_analysis=analysis
            ))

        # 5. 점수 높은 순 정렬
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

# 외부에서 쉽게 쓰도록 인스턴스 생성 함수 제공
def get_matcher():
    return JobMatcher()