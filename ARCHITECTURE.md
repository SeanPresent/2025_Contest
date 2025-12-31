# 아키텍처 문서

## 시스템 개요

Trust-aware Paper Searcher는 Small LLM을 사용하여 arXiv와 PubMed에서 논문을 검색하고, 신뢰할 수 있는 랭킹과 증거 기반 답변을 제공하는 시스템입니다.

## 핵심 원칙

1. **지식 단정 금지**: 검색 결과(증거) 없이 주장하지 않음
2. **Evidence Table 제공**: 모든 답변은 Top-K 논문 테이블과 함께 제공
3. **랭킹 근거 공개**: 점수 피처(Recency, Query-match, Study-type 등) 공개
4. **시각화**: 최소 2개 그래프 생성 (연도별 트렌드, 저널 분포)
5. **재현 가능성**: 동일 질문 → 동일 파이프라인 → 동일 결과
6. **Small LLM 오케스트레이션**: LLM은 계획 수립, 실제 작업은 Tool로 수행

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                         │
│              (Streamlit App / API)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  PaperSearchPipeline                         │
│  (검색 → 정규화 → 랭킹 → 시각화 → 결과 반환)                │
└─────┬──────────────┬──────────────┬──────────────┬──────────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Arxiv    │  │ PubMed    │  │ Paper    │  │ Paper    │
│ Collector│  │ Collector │  │ Normalizer│  │ Scorer   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    외부 API                                  │
│         (arXiv API, PubMed Entrez API)                      │
└─────────────────────────────────────────────────────────────┘
```

## 데이터 흐름

1. **수집 단계**
   - 사용자 질문 → ArxivCollector / PubMedCollector
   - API 호출 → 원본 논문 데이터 수집
   - 캐싱 (SQLite) → 중복 요청 방지

2. **정규화 단계**
   - 원본 데이터 → PaperNormalizer
   - 공통 스키마로 변환
   - Study type 추정
   - Evidence completeness 계산

3. **랭킹 단계**
   - 정규화된 논문 → PaperScorer
   - 피처 기반 점수 계산:
     - Query match (0.4)
     - Recency (0.2)
     - Study type priority (0.2)
     - Evidence completeness (0.15)
     - Duplicate penalty (-0.05)
   - Ranking breakdown 생성

4. **시각화 단계**
   - 랭킹된 논문 → ChartGenerator
   - 연도별 트렌드 차트
   - 저널 분포 차트
   - 연구 유형 분포 차트

5. **결과 반환**
   - Evidence Table (Top-K)
   - Ranking Breakdown
   - Charts
   - Summary

## 정규화 스키마

모든 논문은 다음 공통 스키마로 정규화됩니다:

```python
{
    "source": "arxiv" | "pubmed",
    "id": str,                    # arXiv ID or PubMed ID
    "title": str,
    "authors": List[str],
    "year": int | None,
    "venue": str,                 # Journal or conference name
    "journal": str | None,        # Full journal name
    "abstract": str,
    "url": str,
    "keywords": List[str],        # Keywords or MeSH terms
    "study_type": str,            # Inferred study type
    "retrieval_score": float,     # Ranking score
    "doi": str | None,
    "pdf_url": str | None,
    "categories": List[str],      # arXiv categories
    "primary_category": str | None,
    "study_type_priority": float, # Priority score for study type
    "evidence_completeness": float # Completeness score
}
```

## 랭킹 알고리즘

### 점수 계산식

```
total_score = w1 * query_match 
            + w2 * recency 
            + w3 * study_type_priority 
            + w4 * evidence_completeness 
            - w5 * duplicate_penalty
```

### 피처 설명

1. **Query Match (0.4)**
   - 제목, 초록, 키워드에서 쿼리 용어 매칭
   - 제목 매칭이 가장 중요 (가중치 0.5)

2. **Recency (0.2)**
   - 최근 논문일수록 높은 점수
   - 현재 연도 = 1.0, 10년 전 = 0.0

3. **Study Type Priority (0.2)**
   - 메타분석 > 체계적 문헌고찰 > 무작위 대조 시험 > 실험 연구 > 기타

4. **Evidence Completeness (0.15)**
   - 제목, 초록, 저자, 연도, 저널, 키워드, DOI 등 완성도

5. **Duplicate Penalty (-0.05)**
   - 중복 논문에 대한 페널티

## Small LLM 통합 (향후)

현재는 파이프라인이 직접 실행되지만, 향후 Small LLM을 통합하여:

1. **오케스트레이션**: LLM이 검색 계획 수립
2. **Tool 호출**: 검색, 랭킹, 그래프 생성 도구 호출
3. **답변 생성**: Evidence Table과 Ranking Breakdown을 바탕으로 답변 생성

## 학습 파이프라인

1. **데이터셋 생성**
   - 질문 템플릿 생성
   - 실제 검색 수행
   - Instruction-Response 쌍 생성

2. **SFT 학습**
   - Qwen/Qwen2.5-0.5B 기반
   - LoRA/QLoRA 사용
   - Hugging Face Jobs에서 실행

3. **평가**
   - Format compliance
   - Evidence inclusion
   - Ranking breakdown inclusion
   - Hallucination detection

## 확장 가능성

- 추가 데이터 소스 (Google Scholar, Semantic Scholar 등)
- 더 정교한 랭킹 알고리즘 (학습 기반)
- 멀티모달 지원 (이미지, 표 등)
- 실시간 업데이트 (새 논문 알림)

