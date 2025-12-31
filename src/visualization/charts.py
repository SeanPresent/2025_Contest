"""Chart generation for paper analysis"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Optional
from collections import Counter
import io
import base64


class ChartGenerator:
    """Generate charts for paper analysis"""
    
    def __init__(self, backend: str = "plotly"):
        """
        Initialize chart generator
        
        Args:
            backend: 'plotly' or 'matplotlib'
        """
        self.backend = backend
    
    def generate_year_trend(
        self,
        papers: List[Dict[str, Any]],
        output_format: str = "plotly"
    ) -> Any:
        """
        Generate year trend chart
        
        Args:
            papers: List of paper dictionaries
            output_format: 'plotly', 'matplotlib', or 'html'
            
        Returns:
            Chart object or HTML string
        """
        # Extract years
        years = []
        for paper in papers:
            year = paper.get("year")
            if year:
                years.append(year)
        
        if not years:
            return None
        
        # Count by year
        year_counts = Counter(years)
        sorted_years = sorted(year_counts.keys())
        counts = [year_counts[y] for y in sorted_years]
        
        if output_format == "plotly" or self.backend == "plotly":
            fig = go.Figure()
            
            # Bar chart
            fig.add_trace(go.Bar(
                x=sorted_years,
                y=counts,
                name="논문 수",
                marker_color='rgb(55, 83, 109)',
                text=counts,
                textposition='outside'
            ))
            
            # Trend line
            fig.add_trace(go.Scatter(
                x=sorted_years,
                y=counts,
                mode='lines+markers',
                name="트렌드",
                line=dict(color='rgb(255, 127, 14)', width=2),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="연도별 논문 수 트렌드",
                xaxis_title="연도",
                yaxis_title="논문 수",
                hovermode='x unified',
                template="plotly_white",
                height=400
            )
            
            if output_format == "html":
                return fig.to_html(include_plotlyjs='cdn', div_id="year_trend")
            return fig
        
        elif output_format == "matplotlib" or self.backend == "matplotlib":
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.bar(sorted_years, counts, alpha=0.7, color='steelblue', label='논문 수')
            ax.plot(sorted_years, counts, marker='o', color='orange', linewidth=2, label='트렌드')
            
            ax.set_xlabel("연도", fontsize=12)
            ax.set_ylabel("논문 수", fontsize=12)
            ax.set_title("연도별 논문 수 트렌드", fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if output_format == "html":
                # Convert to base64 HTML img tag
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode()
                plt.close()
                return f'<img src="data:image/png;base64,{img_base64}" alt="Year Trend">'
            
            return fig
    
    def generate_venue_distribution(
        self,
        papers: List[Dict[str, Any]],
        top_n: int = 10,
        output_format: str = "plotly"
    ) -> Any:
        """
        Generate venue/journal distribution chart
        
        Args:
            papers: List of paper dictionaries
            top_n: Number of top venues to show
            output_format: 'plotly', 'matplotlib', or 'html'
            
        Returns:
            Chart object or HTML string
        """
        # Extract venues
        venues = []
        for paper in papers:
            venue = paper.get("venue") or paper.get("journal")
            if venue:
                venues.append(venue)
        
        if not venues:
            return None
        
        # Count by venue
        venue_counts = Counter(venues)
        top_venues = venue_counts.most_common(top_n)
        
        venue_names = [v[0] for v in top_venues]
        counts = [v[1] for v in top_venues]
        
        if output_format == "plotly" or self.backend == "plotly":
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=counts,
                y=venue_names,
                orientation='h',
                marker_color='rgb(55, 83, 109)',
                text=counts,
                textposition='outside'
            ))
            
            fig.update_layout(
                title=f"상위 {top_n}개 저널/학회 분포",
                xaxis_title="논문 수",
                yaxis_title="저널/학회",
                hovermode='y',
                template="plotly_white",
                height=max(400, len(venue_names) * 30)
            )
            
            if output_format == "html":
                return fig.to_html(include_plotlyjs='cdn', div_id="venue_distribution")
            return fig
        
        elif output_format == "matplotlib" or self.backend == "matplotlib":
            fig, ax = plt.subplots(figsize=(10, max(6, len(venue_names) * 0.5)))
            
            ax.barh(venue_names, counts, color='steelblue', alpha=0.7)
            
            ax.set_xlabel("논문 수", fontsize=12)
            ax.set_ylabel("저널/학회", fontsize=12)
            ax.set_title(f"상위 {top_n}개 저널/학회 분포", fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            
            plt.tight_layout()
            
            if output_format == "html":
                # Convert to base64 HTML img tag
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode()
                plt.close()
                return f'<img src="data:image/png;base64,{img_base64}" alt="Venue Distribution">'
            
            return fig
    
    def generate_study_type_distribution(
        self,
        papers: List[Dict[str, Any]],
        output_format: str = "plotly"
    ) -> Any:
        """
        Generate study type distribution pie chart
        
        Args:
            papers: List of paper dictionaries
            output_format: 'plotly', 'matplotlib', or 'html'
            
        Returns:
            Chart object or HTML string
        """
        study_types = [paper.get("study_type", "other") for paper in papers]
        type_counts = Counter(study_types)
        
        labels = list(type_counts.keys())
        values = list(type_counts.values())
        
        # Korean labels mapping
        korean_labels = {
            "meta_analysis": "메타분석",
            "systematic_review": "체계적 문헌고찰",
            "randomized_trial": "무작위 대조 시험",
            "experimental": "실험 연구",
            "case_study": "사례 연구",
            "survey": "설문 조사",
            "theoretical": "이론 연구",
            "other": "기타"
        }
        
        display_labels = [korean_labels.get(label, label) for label in labels]
        
        if output_format == "plotly" or self.backend == "plotly":
            fig = go.Figure(data=[go.Pie(
                labels=display_labels,
                values=values,
                hole=0.3,
                textinfo='label+percent',
                textposition='outside'
            )])
            
            fig.update_layout(
                title="연구 유형 분포",
                template="plotly_white",
                height=400
            )
            
            if output_format == "html":
                return fig.to_html(include_plotlyjs='cdn', div_id="study_type_distribution")
            return fig
        
        elif output_format == "matplotlib" or self.backend == "matplotlib":
            fig, ax = plt.subplots(figsize=(8, 8))
            
            ax.pie(values, labels=display_labels, autopct='%1.1f%%', startangle=90)
            ax.set_title("연구 유형 분포", fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            if output_format == "html":
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150)
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode()
                plt.close()
                return f'<img src="data:image/png;base64,{img_base64}" alt="Study Type Distribution">'
            
            return fig
    
    def generate_all_charts(
        self,
        papers: List[Dict[str, Any]],
        output_format: str = "plotly"
    ) -> Dict[str, Any]:
        """
        Generate all charts
        
        Args:
            papers: List of paper dictionaries
            output_format: 'plotly', 'matplotlib', or 'html'
            
        Returns:
            Dictionary of chart objects/HTML strings
        """
        charts = {}
        
        charts["year_trend"] = self.generate_year_trend(papers, output_format)
        charts["venue_distribution"] = self.generate_venue_distribution(papers, output_format=output_format)
        charts["study_type_distribution"] = self.generate_study_type_distribution(papers, output_format)
        
        return charts

