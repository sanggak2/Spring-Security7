import logging
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# models.py에서 정의한 클래스들 임포트
from models import ResumeAnalysis, JobPostingResult, JobMatchResult

logger = logging.getLogger("uvicorn")

class JobMatcher:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobMatcher, cls).__new__(cls)
        return cls._instance

    def load_model(self):
        if self._model is None:
            print("\n⚙️ [System] AI 모델 로딩 시작...")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ [System] 모델 로딩 완료!\n")

    def _create_user_text(self, user: ResumeAnalysis) -> str:
        text = f"희망 직무: {user.desired_job}. "
        text += f"보유 기술: {', '.join(user.skills)}. "
        for proj in user.projects:
            techs = ", ".join(proj.tech_stack)
            text += f"프로젝트 {proj.name}: {techs} 활용, {proj.description}. "
        for exp in user.experiences:
            text += f"{exp} "
        return text

    def _create_job_text(self, job: JobPostingResult) -> str:
        text = f"{job.title}. "
        res = job.responsibilities if job.responsibilities else []
        qual = job.qualifications if job.qualifications else []
        text += f"담당 업무: {' '.join(res)}. "
        text += f"자격 요건: {' '.join(qual)}. "
        return text

    def calculate_scores(self, user: ResumeAnalysis, jobs: List[JobPostingResult]) -> List[JobMatchResult]:
        self.load_model()
        
        if not jobs:
            return []

        # [디버깅] 사용자 텍스트 확인
        user_text = self._create_user_text(user)
        print(f"\n👤 [User Text]: {user_text[:100]}...") # 앞 100자만 출력

        job_texts = []
        for job in jobs:
            j_text = self._create_job_text(job)
            job_texts.append(j_text)
            # [디버깅] 공고 텍스트 확인
            # print(f"   🏢 [Job Text]: {j_text[:50]}...") 

        # 임베딩 및 점수 계산
        user_vector = self._model.encode([user_text])
        job_vectors = self._model.encode(job_texts)
        similarities = cosine_similarity(user_vector, job_vectors)[0]

        results = []
        print("\n📊 [매칭 점수 계산 결과]")
        print("-" * 50)
        
        for i, score in enumerate(similarities):
            match_score = round(float(score) * 100, 1)
            job_title = jobs[i].title
            
            # [디버깅] 점수 로그 출력
            print(f"   🔹 {job_title[:20]}... : {match_score}점")

            if match_score >= 70:
                analysis = "🌟 AI 강력 추천 (직무/스택 일치도 매우 높음)"
            elif match_score >= 50:
                analysis = "✅ 적합 (핵심 역량 부합)"
            elif match_score >= 30:
                analysis = "🤔 검토 필요 (일부 연관성 있음)"
            else:
                analysis = "⚠️ 관련성 낮음"

            job_data = jobs[i].model_dump()
            results.append(JobMatchResult(
                **job_data,
                match_score=match_score,
                ai_analysis=analysis
            ))

        print("-" * 50 + "\n")

        # 점수 높은 순 정렬
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

def get_matcher():
    return JobMatcher()