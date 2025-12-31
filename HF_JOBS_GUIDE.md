# Hugging Face Jobs 사용 가이드

이 프로젝트는 **Hugging Face Jobs**를 사용하여 클라우드에서 모든 작업을 실행합니다. 로컬 GPU나 venv 설정이 필요 없습니다.

## 🎯 핵심 개념

- **모든 스크립트는 HF Jobs에서 실행**: 데이터셋 생성, 학습, 평가 모두 클라우드에서 실행
- **로컬 환경 불필요**: GPU, CUDA, venv 설정 없이 바로 시작 가능
- **비용 효율적**: 사용한 만큼만 비용 지불 (Pro/Team/Enterprise 플랜 필요)

## 📋 필수 사항

1. **Hugging Face 계정**: [Pro](https://hf.co/pro), [Team](https://hf.co/enterprise), 또는 [Enterprise](https://hf.co/enterprise) 플랜
2. **HF_TOKEN**: Hugging Face에서 발급받은 토큰
3. **NCBI_EMAIL**: PubMed API 사용을 위한 이메일 (무료)

## 🚀 워크플로우

### 1. 데이터셋 생성 (HF Jobs)

```python
# scripts/generate_sft_dataset.py를 HF Jobs로 제출
# PEP 723 형식의 스크립트로 자동 의존성 설치
```

**MCP 도구 사용 예시:**
```python
hf_jobs("uv", {
    "script": open("scripts/generate_sft_dataset.py").read(),
    "flavor": "cpu-medium",  # 데이터셋 생성은 CPU로 충분
    "timeout": "1h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN", "NCBI_EMAIL": "$NCBI_EMAIL"}
})
```

### 2. 모델 학습 (HF Jobs)

```bash
# train_sft.py 실행하여 job configuration 생성
python scripts/train_sft.py \
    --dataset your-username/trust-aware-paper-searcher-dataset \
    --base_model Qwen/Qwen2.5-0.5B \
    --hub_model_id your-username/trust-aware-paper-searcher \
    --flavor a10g-large \
    --timeout 3h
```

생성된 job configuration을 `hf_jobs` MCP 도구로 제출:

```python
hf_jobs("uv", {
    "script": "<generated_script>",
    "flavor": "a10g-large",
    "timeout": "3h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"}
})
```

### 3. 평가 (HF Jobs)

```python
# evaluate.py를 HF Jobs로 제출
hf_jobs("uv", {
    "script": open("scripts/evaluate.py").read(),
    "flavor": "a10g-large",
    "timeout": "1h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"}
})
```

## 📝 스크립트 구조

모든 스크립트는 **PEP 723 형식**을 사용하여 의존성을 자동으로 설치합니다:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#     "trl>=0.12.0",
#     "peft>=0.7.0",
#     "transformers>=4.36.0",
#     ...
# ]
# ///
```

## 🔧 환경 변수 전달

HF Jobs에서 환경 변수를 사용하려면 `secrets` 파라미터를 사용:

```python
hf_jobs("uv", {
    "script": "...",
    "secrets": {
        "HF_TOKEN": "$HF_TOKEN",  # 로컬 환경 변수 참조
        "NCBI_EMAIL": "$NCBI_EMAIL"
    }
})
```

## 💡 팁

1. **데이터셋은 Hub에 업로드**: 로컬에서 생성한 데이터셋은 Hub에 업로드하여 재사용
2. **캐싱 활용**: arXiv/PubMed API 호출 결과는 캐싱하여 비용 절감
3. **하드웨어 선택**: 
   - 데이터셋 생성: `cpu-medium` 또는 `cpu-large`
   - 학습: `a10g-large` (권장) 또는 `a100`
   - 평가: `a10g-large`
4. **타임아웃 설정**: 충분한 시간을 할당 (최소 1-2시간, 학습은 3-6시간)

## 📊 모니터링

- **Trackio**: 학습 진행 상황 실시간 모니터링
- **HF Jobs 대시보드**: 작업 상태 확인
- **Hub**: 학습된 모델 자동 저장

## ❓ 문제 해결

### 작업이 실패하는 경우
- 로그 확인: `hf_jobs("logs", {"job_id": "..."})`
- 타임아웃 증가
- 하드웨어 업그레이드

### 메모리 부족
- 배치 크기 감소
- Gradient accumulation 증가
- 더 큰 하드웨어 사용

### 의존성 오류
- PEP 723 헤더에 필요한 패키지 추가
- 버전 명시 (예: `"transformers>=4.36.0"`)

