"""Setup script for Trust-aware Paper Searcher"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="trust-aware-paper-searcher",
    version="0.1.0",
    author="Your Name",
    description="Small LLM 기반 논문 검색 및 랭킹 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/trust-aware-paper-searcher",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "collect-papers=scripts.collect_papers:main",
            "generate-sft-dataset=scripts.generate_sft_dataset:main",
            "train-sft=scripts.train_sft:main",
            "evaluate=scripts.evaluate:main",
        ],
    },
)

