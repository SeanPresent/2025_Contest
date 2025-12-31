"""Submit dataset generation job to HF Jobs"""

import os
from pathlib import Path

# Read the dataset generation script
script_path = Path(__file__).parent / "generate_sft_dataset.py"
script_content = script_path.read_text()

# Job configuration for HF Jobs
job_config = {
    "script": script_content,
    "flavor": "cpu-large",  # 데이터셋 생성은 CPU로 충분
    "timeout": "2h",
    "secrets": {
        "HF_TOKEN": os.getenv("HF_TOKEN"),  # 환경 변수에서 가져오기 (필수)
        "NCBI_EMAIL": os.getenv("NCBI_EMAIL", "your_email@example.com")
    }
}

print("📋 HF Jobs Configuration:")
print("=" * 60)
print(f"Flavor: {job_config['flavor']}")
print(f"Timeout: {job_config['timeout']}")
print("\n💡 다음 명령으로 제출:")
print("   hf_jobs('uv', job_config)")
print("\n또는 MCP 도구를 사용하여 제출하세요.")

