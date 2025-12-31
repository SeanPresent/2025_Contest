# Trust-aware Paper Searcher

Small LLM 기반 논문 검색 및 랭킹 시스템

## 📖 프로젝트 소개

**Trust-aware Paper Searcher**는 연구자들이 arXiv와 PubMed에서 논문을 검색하고, 신뢰할 수 있는 근거 기반으로 랭킹된 결과를 받을 수 있도록 도와주는 AI 시스템입니다.

### 🎯 해결하는 문제

연구자들이 논문을 검색할 때 겪는 주요 문제들:

1. **신뢰성 부족**: 검색 결과의 랭킹 근거가 불명확하여 어떤 논문이 왜 상위에 랭크되었는지 알 수 없음
2. **증거 부재**: 답변에 사용된 논문의 출처와 근거가 명시되지 않아 검증이 어려움
3. **주관적 랭킹**: 검색 엔진의 불투명한 알고리즘에 의존하여 재현성이 낮음
4. **시각화 부족**: 검색 결과의 트렌드나 분포를 한눈에 파악하기 어려움

### ✨ 주요 특징

이 시스템은 다음과 같은 원칙을 따릅니다:

- **Evidence-based**: 모든 답변은 검색된 논문에 근거하며, Evidence Table을 함께 제공
- **Transparent Ranking**: 랭킹 점수의 각 구성 요소(쿼리 매칭, 최신성, 연구 유형 등)를 공개
- **Reproducible**: 동일한 질문에 대해 항상 동일한 파이프라인과 결과를 보장
- **Visualized**: 연도별 트렌드, 저널 분포 등 최소 2개 이상의 차트 제공
- **Trustworthy**: Hallucination 방지를 위한 검증 메커니즘 포함

### 🔍 작동 방식

1. **논문 수집**: arXiv와 PubMed API를 통해 실시간으로 논문 검색
2. **정규화**: 다양한 소스의 논문을 공통 스키마로 변환
3. **랭킹**: 피처 기반 점수 계산 (Query match, Recency, Study type, Evidence completeness)
4. **시각화**: 검색 결과를 차트로 시각화
5. **답변 생성**: Small LLM이 Evidence Table과 Ranking Breakdown을 바탕으로 답변 생성

### 💡 사용 사례

- **문헌 조사**: 특정 주제에 대한 최신 연구 동향 파악
- **메타 분석**: 체계적 문헌고찰을 위한 논문 수집 및 정리
- **연구 트렌드 분석**: 연도별, 저널별 연구 트렌드 시각화
- **신뢰할 수 있는 답변**: 증거 기반으로 검증 가능한 답변 제공

### 🛠️ 기술 스택

- **LLM**: Qwen/Qwen2.5-0.5B (Small LLM, LoRA/QLoRA fine-tuning)
- **Training**: Hugging Face Jobs (클라우드 GPU)
- **Data Sources**: arXiv API, PubMed Entrez API
- **Ranking**: 피처 기반 스코어링 시스템
- **Visualization**: Plotly, Matplotlib
- **Framework**: TRL (Transformer Reinforcement Learning), PEFT

### 🎓 학습 목표

Small LLM을 학습시켜 다음을 수행하도록 합니다:

- 사용자 질문을 분석하여 검색 계획 수립
- Evidence Table 형식으로 논문 정리
- Ranking Breakdown을 포함한 투명한 랭킹 근거 제공
- 차트 설명과 함께 검색 결과 요약 생성

## 프로젝트 구조

```
trust-aware-paper-searcher/
├── README.md
├── requirements.txt
├── .env.example
├── setup.py
│
├── src/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── arxiv_collector.py      # arXiv API 수집기
│   │   ├── pubmed_collector.py     # PubMed Entrez 수집기
│   │   └── base_collector.py       # 공통 인터페이스
│   │
│   ├── normalizers/
│   │   ├── __init__.py
│   │   └── paper_normalizer.py     # 정규화 스키마 및 변환
│   │
│   ├── ranking/
│   │   ├── __init__.py
│   │   └── scorer.py               # 피처 기반 랭킹 점수
│   │
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── charts.py               # matplotlib/plotly 차트 생성
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Small LLM 오케스트레이션
│   │   └── tools.py                # 검색/랭킹/그래프 도구
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cache.py                 # SQLite 캐시
│       └── retry.py                 # 재시도 로직
│
├── data/
│   ├── raw/                         # 원본 수집 데이터
│   ├── normalized/                 # 정규화된 데이터
│   └── sft_dataset/                 # SFT 학습용 데이터셋
│
├── scripts/
│   ├── collect_papers.py           # 수집 스크립트
│   ├── generate_sft_dataset.py     # SFT 데이터셋 생성
│   ├── train_sft.py                # 학습 스크립트 (HF Jobs)
│   └── evaluate.py                 # 평가 스크립트
│
├── app/
│   ├── __init__.py
│   └── streamlit_app.py            # Streamlit 데모 앱
│
├── config/
│   └── config.yaml                 # 설정 파일
│
└── tests/
    ├── test_collectors.py
    ├── test_ranking.py
    └── test_normalizer.py
```

## 핵심 파일 책임

| 파일 | 책임 |
|------|------|
| `src/collectors/arxiv_collector.py` | arXiv API 쿼리, 결과 파싱, 에러 핸들링 |
| `src/collectors/pubmed_collector.py` | Entrez ESearch/EFetch, 메타데이터/초록 수집 |
| `src/normalizers/paper_normalizer.py` | 공통 스키마로 변환, study_type 추정 |
| `src/ranking/scorer.py` | 피처 기반 점수 계산, breakdown 제공 |
| `src/visualization/charts.py` | 연도별 트렌드, 저널 분포 차트 생성 |
| `src/llm/orchestrator.py` | Small LLM이 Tool 호출 계획 수립 |
| `src/llm/tools.py` | 검색/랭킹/그래프 생성 도구 함수 |
| `app/streamlit_app.py` | 사용자 인터페이스, 결과 표시 |
| `scripts/generate_sft_dataset.py` | 질문 템플릿 → 실제 검색 → instruction/response 생성 |
| `scripts/train_sft.py` | LoRA/QLoRA 학습, HF Jobs 제출 |

## 빠른 시작 (Hugging Face Jobs 중심)

**모든 작업은 Hugging Face 클라우드에서 실행됩니다. 로컬 GPU나 venv 설정이 필요 없습니다.**

### 1. 환경 변수 설정 (필수)

```bash
# .env 파일 생성 (또는 환경 변수로 설정)
HF_TOKEN=your_huggingface_token_here  # Hugging Face 토큰 (https://huggingface.co/settings/tokens)
NCBI_EMAIL=your_email@example.com  # PubMed API용 이메일
```

### 2. SFT 데이터셋 생성 (HF Jobs)

데이터셋 생성 스크립트를 HF Jobs로 제출:

```python
# scripts/generate_sft_dataset.py를 HF Jobs로 제출
# 또는 로컬에서 실행 후 Hub에 업로드
```

### 3. 모델 학습 (HF Jobs)

```bash
python scripts/train_sft.py \
    --dataset data/sft_dataset/train.jsonl \
    --base_model Qwen/Qwen2.5-0.5B \
    --hub_model_id your-username/trust-aware-paper-searcher \
    --num_epochs 3 \
    --batch_size 4 \
    --flavor a10g-large \
    --timeout 3h
```

생성된 job configuration을 `hf_jobs` MCP 도구로 제출하세요.

### 4. 평가 (HF Jobs 또는 로컬)

```bash
# HF Jobs에서 평가 스크립트 실행
python scripts/evaluate.py \
    --model_path your-username/trust-aware-paper-searcher \
    --test_dataset data/sft_dataset/test.jsonl
```

---

## 로컬 개발 (선택사항)

로컬에서 테스트하거나 Streamlit 앱을 실행하려면:

```bash
# 가상 환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# Streamlit 데모 앱 실행
streamlit run app/streamlit_app.py
```

자세한 사용법은 [QUICKSTART.md](QUICKSTART.md)를 참조하세요.

## 주요 기능

- ✅ **arXiv/PubMed 자동 수집**: 공개 API를 통한 논문 수집
- ✅ **정규화된 공통 스키마**: 다양한 소스의 논문을 통일된 형식으로 변환
- ✅ **피처 기반 랭킹**: Query match, Recency, Study type, Evidence completeness 기반 점수 계산
- ✅ **랭킹 근거 공개**: 각 논문의 점수 구성 요소를 투명하게 제공
- ✅ **Evidence Table**: 검색된 논문의 상위 K개를 테이블 형식으로 제시
- ✅ **시각화**: 연도별 트렌드, 저널 분포, 연구 유형 분포 차트 생성
- ✅ **캐싱**: SQLite 기반 캐싱으로 중복 요청 방지
- ✅ **에러 핸들링**: 재시도 로직과 레이트 리밋 처리
- ✅ **SFT 데이터셋 자동 생성**: 질문 템플릿에서 실제 검색 결과 기반 데이터셋 생성
- ✅ **Hugging Face Jobs 기반 학습**: 클라우드 GPU에서 LoRA/QLoRA 학습

## 📊 결과 예시

### 검색 질문
```
"transformer attention mechanism"
```

### 1. Evidence Table (Top-K)

| 순위 | 제목 | 저자 | 연도 | 저널/학회 | 연구 유형 | 총점 | URL |
|------|------|------|------|-----------|-----------|------|-----|
| 1 | Attention Is All You Need | Vaswani et al. | 2017 | NeurIPS | theoretical | 0.892 | [링크] |
| 2 | BERT: Pre-training of Deep Bidirectional Transformers | Devlin et al. | 2019 | NAACL | experimental | 0.856 | [링크] |
| 3 | GPT-3: Language Models are Few-Shot Learners | Brown et al. | 2020 | NeurIPS | experimental | 0.834 | [링크] |
| 4 | RoBERTa: A Robustly Optimized BERT Pretraining Approach | Liu et al. | 2019 | arXiv | experimental | 0.821 | [링크] |
| 5 | The Illustrated Transformer | Alammar | 2018 | Blog | other | 0.798 | [링크] |

### 2. Ranking Breakdown (랭킹 근거)

| 순위 | 제목 | 총점 | 쿼리 매칭 | 최신성 | 연구 유형 | 증거 완성도 | 중복 페널티 |
|------|------|------|-----------|--------|-----------|-------------|-------------|
| 1 | Attention Is All You Need | 0.892 | 0.95 | 0.70 | 0.50 | 0.90 | 0.00 |
| 2 | BERT: Pre-training... | 0.856 | 0.88 | 0.80 | 0.70 | 0.95 | 0.00 |
| 3 | GPT-3: Language Models... | 0.834 | 0.82 | 0.90 | 0.70 | 0.98 | 0.00 |

**점수 구성 요소 설명:**
- **쿼리 매칭 (0.4)**: 제목, 초록, 키워드에서 검색어 매칭 정도
- **최신성 (0.2)**: 논문 발표 연도 (최근일수록 높은 점수)
- **연구 유형 (0.2)**: 메타분석 > 체계적 문헌고찰 > 무작위 대조 시험 > 실험 연구
- **증거 완성도 (0.15)**: 제목, 초록, 저자, 연도, 저널, 키워드, DOI 등 완성도
- **중복 페널티 (-0.05)**: 중복 논문에 대한 감점

### 3. 시각화

#### 연도별 트렌드
```
연도별 논문 수 분포를 보여주는 차트
- 2017년: 5개
- 2018년: 8개
- 2019년: 12개
- 2020년: 15개
- 2021년: 18개
- 2022년: 20개
- 2023년: 22개
- 2024년: 10개
```

#### 저널/학회 분포
```
상위 저널/학회:
- NeurIPS: 8개
- arXiv: 12개
- ICML: 5개
- ACL: 4개
- ICLR: 3개
```

#### 연구 유형 분포
```
- 실험 연구: 60%
- 이론 연구: 25%
- 체계적 문헌고찰: 10%
- 기타: 5%
```

### 4. 답변 요약 (Small LLM 생성)

**검색 질문**: "transformer attention mechanism"

**검색 결과 요약**:
- 총 10개의 논문이 검색되었습니다.
- 소스별 분포: arxiv(8), pubmed(2)
- 연도 범위: 2017-2024
- 평균 랭킹 점수: 0.823

**주요 발견**:
- 상위 논문들은 주로 NeurIPS, arXiv에서 발표되었습니다.
- 연구 유형 분포: 실험 연구(60%), 이론 연구(25%), 체계적 문헌고찰(10%)
- 최근 트렌드: 2020년 이후 transformer 기반 모델 연구가 급증
- 핵심 논문: "Attention Is All You Need" (2017)이 가장 높은 점수를 받았으며, 쿼리 매칭 점수가 0.95로 매우 높습니다.

**Evidence Table의 논문들에 근거하여**:
1. Attention 메커니즘은 2017년 Vaswani et al.의 논문에서 처음 제안되었습니다.
2. 이후 BERT, GPT-3 등 다양한 모델에서 활용되었습니다.
3. 최근 연구들은 attention 메커니즘의 효율성과 확장성에 집중하고 있습니다.

---

### 실제 사용 예시 (Python API)

```python
from src.pipeline import PaperSearchPipeline

# 파이프라인 초기화
pipeline = PaperSearchPipeline(use_cache=True)

# 검색 및 랭킹
results = pipeline.search(
    query="transformer attention mechanism",
    sources=["arxiv", "pubmed"],
    max_results=50,
    top_k=10
)

# Evidence Table 출력
print("📋 Evidence Table (Top-10)")
for i, (paper, breakdown) in enumerate(zip(results["papers"], results["breakdowns"]), 1):
    print(f"\n[{i}] {paper['title']}")
    print(f"    점수: {breakdown.total_score:.3f}")
    print(f"    - 쿼리 매칭: {breakdown.query_match:.3f}")
    print(f"    - 최신성: {breakdown.recency:.3f}")
    print(f"    - 연구 유형: {breakdown.study_type_priority:.3f}")
    print(f"    URL: {paper['url']}")

# 차트 생성
charts = results["charts"]
# charts["year_trend"].show()  # Plotly 차트 표시
# charts["venue_distribution"].show()
```

### Streamlit 앱 화면 예시

```
┌─────────────────────────────────────────────────────────┐
│  📚 Trust-aware Paper Searcher                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  검색 질문: [transformer attention mechanism    ] [🔍] │
│                                                         │
│  📊 검색 결과 요약                                      │
│  총 논문 수: 10  │ 소스별 분포: arxiv(8), pubmed(2)   │
│                                                         │
│  📋 Evidence Table (Top-K)                             │
│  [테이블 표시]                                          │
│                                                         │
│  🔍 랭킹 근거 (Ranking Breakdown)                       │
│  [점수 구성 요소 테이블]                                │
│                                                         │
│  📈 시각화                                              │
│  [연도별 트렌드 차트]  [저널 분포 차트]                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 핵심 원칙

1. **지식 단정 금지**: 검색 결과(증거) 없이 주장하지 않음
2. **Evidence Table 제공**: 모든 답변은 Top-K 논문 테이블과 함께 제공
3. **랭킹 근거 공개**: 점수 피처를 명시하여 투명성 확보
4. **시각화**: 최소 2개 그래프 생성 (연도별 트렌드, 저널 분포)
5. **재현 가능성**: 동일 질문 → 동일 파이프라인 → 동일 결과
6. **Small LLM 오케스트레이션**: LLM은 계획 수립, 실제 작업은 Tool로 수행

## 아키텍처

시스템 아키텍처에 대한 자세한 내용은 [ARCHITECTURE.md](ARCHITECTURE.md)를 참조하세요.

## 문서

- [QUICKSTART.md](QUICKSTART.md): 빠른 시작 가이드
- [HF_JOBS_GUIDE.md](HF_JOBS_GUIDE.md): Hugging Face Jobs 사용 가이드 (권장)
- [ARCHITECTURE.md](ARCHITECTURE.md): 시스템 아키텍처 설명

## 중요 사항

⚠️ **이 프로젝트는 Hugging Face Jobs를 사용하여 클라우드에서 실행됩니다.**
- 로컬 GPU나 venv 설정이 필요 없습니다
- 모든 작업(데이터셋 생성, 학습, 평가)은 HF Jobs에서 실행됩니다
- 로컬 개발은 선택사항입니다 (Streamlit 앱 테스트 등)

