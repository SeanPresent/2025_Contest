"""Streamlit demo app for Trust-aware Paper Searcher"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PaperSearchPipeline
from src.ranking import RankingBreakdown

# Page config
st.set_page_config(
    page_title="Trust-aware Paper Searcher",
    page_icon="📚",
    layout="wide"
)

# Title
st.title("📚 Trust-aware Paper Searcher")
st.markdown("**Small LLM 기반 논문 검색 및 랭킹 시스템**")

# Initialize session state
if "pipeline" not in st.session_state:
    st.session_state.pipeline = PaperSearchPipeline(use_cache=True)
if "results" not in st.session_state:
    st.session_state.results = None

# Sidebar for search parameters
with st.sidebar:
    st.header("검색 설정")
    
    query = st.text_input(
        "검색 질문",
        placeholder="예: transformer attention mechanism",
        help="논문을 검색할 질문을 입력하세요"
    )
    
    sources = st.multiselect(
        "데이터 소스",
        options=["arxiv", "pubmed"],
        default=["arxiv", "pubmed"],
        help="검색할 데이터 소스를 선택하세요"
    )
    
    max_results = st.slider(
        "소스당 최대 결과 수",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="각 데이터 소스에서 가져올 최대 논문 수"
    )
    
    top_k = st.slider(
        "상위 K개 결과",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        help="랭킹 후 반환할 상위 논문 수"
    )
    
    year_filter = st.checkbox("연도 필터 적용")
    if year_filter:
        year_range = st.slider(
            "연도 범위",
            min_value=2000,
            max_value=2025,
            value=(2015, 2025),
            help="검색할 연도 범위"
        )
    else:
        year_range = None
    
    search_button = st.button("🔍 검색", type="primary", use_container_width=True)

# Main content
if search_button and query:
    if not sources:
        st.error("⚠️ 최소 하나의 데이터 소스를 선택해주세요.")
    else:
        with st.spinner("논문을 검색하고 랭킹하는 중..."):
            try:
                results = st.session_state.pipeline.search(
                    query=query,
                    sources=sources,
                    max_results=max_results,
                    top_k=top_k,
                    year_filter=year_range if year_filter else None
                )
                st.session_state.results = results
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")
                st.exception(e)

# Display results
if st.session_state.results:
    results = st.session_state.results
    papers = results["papers"]
    breakdowns = results["breakdowns"]
    charts = results["charts"]
    summary = results["summary"]
    query = results["query"]
    
    if not papers:
        st.warning("검색 결과가 없습니다.")
    else:
        # Summary section
        st.header("📊 검색 결과 요약")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 논문 수", summary["total"])
        with col2:
            sources_str = ", ".join([f"{k}: {v}" for k, v in summary["sources"].items()])
            st.metric("소스별 분포", sources_str)
        with col3:
            if summary["year_range"]:
                st.metric("연도 범위", f"{summary['year_range'][0]}-{summary['year_range'][1]}")
        with col4:
            st.metric("평균 점수", f"{summary['avg_score']:.3f}")
        
        st.divider()
        
        # Evidence Table
        st.header("📋 Evidence Table (Top-K)")
        
        # Prepare table data
        table_data = []
        for i, (paper, breakdown) in enumerate(zip(papers, breakdowns), 1):
            table_data.append({
                "순위": i,
                "제목": paper.get("title", "")[:100] + ("..." if len(paper.get("title", "")) > 100 else ""),
                "저자": ", ".join(paper.get("authors", [])[:3]) + ("..." if len(paper.get("authors", [])) > 3 else ""),
                "연도": paper.get("year", "N/A"),
                "저널/학회": paper.get("venue", "N/A"),
                "연구 유형": paper.get("study_type", "other"),
                "총점": f"{breakdown.total_score:.3f}",
                "URL": paper.get("url", "")
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Ranking Breakdown
        st.header("🔍 랭킹 근거 (Ranking Breakdown)")
        
        breakdown_data = []
        for breakdown in breakdowns:
            breakdown_data.append({
                "순위": breakdowns.index(breakdown) + 1,
                "제목": breakdown.title[:80] + "...",
                "총점": f"{breakdown.total_score:.3f}",
                "쿼리 매칭": f"{breakdown.query_match:.3f}",
                "최신성": f"{breakdown.recency:.3f}",
                "연구 유형": f"{breakdown.study_type_priority:.3f}",
                "증거 완성도": f"{breakdown.evidence_completeness:.3f}",
                "중복 페널티": f"{breakdown.duplicate_penalty:.3f}"
            })
        
        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(
            breakdown_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed paper information
        st.header("📄 논문 상세 정보")
        
        for i, paper in enumerate(papers[:top_k], 1):
            with st.expander(f"{i}. {paper.get('title', 'No title')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**저자:** {', '.join(paper.get('authors', []))}")
                    st.markdown(f"**연도:** {paper.get('year', 'N/A')}")
                    st.markdown(f"**저널/학회:** {paper.get('venue', 'N/A')}")
                    st.markdown(f"**연구 유형:** {paper.get('study_type', 'other')}")
                    st.markdown(f"**랭킹 점수:** {paper.get('retrieval_score', 0):.3f}")
                    
                    if paper.get("keywords"):
                        st.markdown(f"**키워드:** {', '.join(paper.get('keywords', [])[:10])}")
                    
                    if paper.get("abstract"):
                        st.markdown("**초록:**")
                        st.markdown(paper.get("abstract", "")[:500] + "...")
                
                with col2:
                    if paper.get("url"):
                        st.markdown(f"[논문 링크]({paper.get('url')})")
                    if paper.get("pdf_url"):
                        st.markdown(f"[PDF 다운로드]({paper.get('pdf_url')})")
                    if paper.get("doi"):
                        st.markdown(f"**DOI:** {paper.get('doi')}")
        
        # Charts
        st.header("📈 시각화")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if charts.get("year_trend"):
                st.plotly_chart(charts["year_trend"], use_container_width=True)
            
            if charts.get("study_type_distribution"):
                st.plotly_chart(charts["study_type_distribution"], use_container_width=True)
        
        with col2:
            if charts.get("venue_distribution"):
                st.plotly_chart(charts["venue_distribution"], use_container_width=True)
        
        # Answer Summary (placeholder for LLM-generated summary)
        st.header("💡 검색 결과 요약")
        st.info("""
        **검색된 논문 요약:**
        
        - 총 {total}개의 논문이 검색되었습니다.
        - 주요 저널/학회: {venues}
        - 연도 범위: {year_range}
        - 연구 유형 분포: {study_types}
        
        *이 요약은 Small LLM에 의해 생성될 예정입니다.*
        """.format(
            total=summary["total"],
            venues=", ".join(list(summary["sources"].keys())),
            year_range=f"{summary['year_range'][0]}-{summary['year_range'][1]}" if summary.get("year_range") else "N/A",
            study_types=", ".join([f"{k}({v})" for k, v in summary.get("study_types", {}).items()])
        ))

else:
    # Welcome message
    st.info("""
    👋 **사용 방법:**
    
    1. 왼쪽 사이드바에서 검색 질문을 입력하세요
    2. 데이터 소스를 선택하세요 (arXiv, PubMed, 또는 둘 다)
    3. 검색 파라미터를 조정하세요
    4. "🔍 검색" 버튼을 클릭하세요
    
    **주요 기능:**
    - 📋 Evidence Table: 검색된 논문의 상위 K개를 테이블로 표시
    - 🔍 랭킹 근거: 각 논문의 점수 구성 요소를 공개
    - 📈 시각화: 연도별 트렌드, 저널 분포, 연구 유형 분포
    - 📄 상세 정보: 각 논문의 메타데이터와 초록
    """)

