import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from models import ResumeAnalysis, JobPostingResult, JobMatchResult

class JobMatcher:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobMatcher, cls).__new__(cls)
            print("⚙️ Embedding Model Loading... (all-MiniLM-L6-v2)")
            # 모델을 싱글톤으로 로드하여 메모리 절약
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Model Loaded!")
        return cls._instance

    def _create_user_text(self, user: ResumeAnalysis) -> str:
        """이력서 객체를 하나의 텍스트로 변환"""
        text = f"희망 직무: {user.desired_job}. "
        text += f"보유 기술: {', '.join(user.skills)}. "
        
        for proj in user.projects:
            techs = ", ".join(proj.tech_stack)
            text += f"프로젝트 {proj.name}: {techs} 활용, {proj.description}. "
            
        for exp in user.experiences:
            text += f"{exp} "
            
        return text

    def _create_job_text(self, job: JobPostingResult) -> str:
        """채용공고 객체를 하나의 텍스트로 변환"""
        text = f"{job.title}. "
        text += f"담당 업무: {' '.join(job.responsibilities)}. "
        text += f"자격 요건: {' '.join(job.qualifications)}. "
        return text

    def calculate_scores(self, user: ResumeAnalysis, jobs: List[JobPostingResult]) -> List[JobMatchResult]:
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