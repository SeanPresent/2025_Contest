# 빠른 시작 가이드

## 🚀 Hugging Face Jobs 중심 워크플로우

**모든 작업은 Hugging Face 클라우드에서 실행됩니다. 로컬 GPU나 venv 설정이 필요 없습니다.**

### 1. 환경 변수 설정 (필수)

```bash
# HF_TOKEN과 NCBI_EMAIL만 설정하면 됩니다
export HF_TOKEN="your_huggingface_token_here"  # https://huggingface.co/settings/tokens 에서 발급
export NCBI_EMAIL="your_email@example.com"
```

또는 `.env` 파일 생성:
```bash
HF_TOKEN=your_huggingface_token_here
NCBI_EMAIL=your_email@example.com
```

### 2. SFT 데이터셋 생성 (HF Jobs)

데이터셋 생성 스크립트를 HF Jobs로 제출:

```python
# generate_sft_dataset.py를 HF Jobs로 제출
# 또는 로컬에서 실행 후 Hub에 업로드
```

또는 로컬에서 실행 후 Hub에 업로드:
```bash
python scripts/generate_sft_dataset.py \
    --num_queries 50 \
    --max_results 30 \
    --top_k 10 \
    --output data/sft_dataset/train.jsonl
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

스크립트가 생성한 job configuration을 `hf_jobs` MCP 도구로 제출하세요.

---

## 💻 로컬 개발 (선택사항)

로컬에서 테스트하거나 Streamlit 앱을 실행하려면:

```bash
# 가상 환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 로컬 테스트

```bash
# 파이프라인 테스트
python scripts/test_pipeline.py

# 논문 수집 테스트
python scripts/collect_papers.py \
    --query "transformer attention mechanism" \
    --sources arxiv pubmed \
    --max_results 20 \
    --normalize \
    --output data/raw/test_papers.json

# Streamlit 데모 앱 실행
streamlit run app/streamlit_app.py
```

---

## 📊 전체 워크플로우

### 방법 1: 모든 것을 HF Jobs에서 실행 (권장)

1. **데이터셋 생성**: `generate_sft_dataset.py` → HF Jobs
2. **모델 학습**: `train_sft.py` → HF Jobs  
3. **평가**: `evaluate.py` → HF Jobs

### 방법 2: 데이터셋만 로컬에서 생성

1. **데이터셋 생성**: 로컬에서 실행 후 Hub에 업로드
2. **모델 학습**: Hub의 데이터셋 사용 → HF Jobs
3. **평가**: HF Jobs

---

## 4. 모델 학습 (Hugging Face Jobs)

### 학습 작업 제출

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

스크립트가 생성한 job configuration을 사용하여 `hf_jobs` MCP 도구로 작업을 제출하세요.

## 5. 모델 평가

```bash
python scripts/evaluate.py \
    --model_path your-username/trust-aware-paper-searcher \
    --test_dataset data/sft_dataset/test.jsonl \
    --output evaluation_metrics.json
```

## 6. Python API 사용 예제

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

# 결과 확인
papers = results["papers"]
breakdowns = results["breakdowns"]
charts = results["charts"]
summary = results["summary"]

# Evidence Table 출력
for i, (paper, breakdown) in enumerate(zip(papers, breakdowns), 1):
    print(f"{i}. {paper['title']}")
    print(f"   점수: {breakdown.total_score:.3f}")
    print(f"   URL: {paper['url']}")
    print()
```

## 문제 해결

### arXiv API 레이트 리밋
- 기본적으로 3초 대기 시간이 포함되어 있습니다
- 캐싱을 활성화하여 중복 요청을 방지하세요

### PubMed API 레이트 리밋
- API 키 없이: 초당 3개 요청
- API 키 있음: 초당 10개 요청
- NCBI_EMAIL 환경 변수를 설정해야 합니다

### 메모리 부족
- `max_results`를 줄이세요
- 배치 크기를 줄이거나 gradient accumulation을 늘리세요

### 학습 작업 타임아웃
- `timeout` 파라미터를 늘리세요 (예: "6h")
- `num_epochs`를 줄이거나 데이터셋 크기를 줄이세요

