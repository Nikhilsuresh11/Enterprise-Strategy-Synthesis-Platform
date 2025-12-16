"""Chart generation service using Plotly."""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
import json


class ChartService:
    """Service for generating Plotly charts as JSON."""
    
    @staticmethod
    def create_market_sizing_chart(
        tam: float,
        sam: float,
        som: float
    ) -> str:
        """
        Create funnel chart for TAM/SAM/SOM.
        
        Args:
            tam: Total Addressable Market
            sam: Serviceable Addressable Market
            som: Serviceable Obtainable Market
            
        Returns:
            Plotly chart as JSON string
        """
        fig = go.Figure(go.Funnel(
            y=["TAM<br>(Total Market)", "SAM<br>(Serviceable)", "SOM<br>(Obtainable)"],
            x=[tam, sam, som],
            textinfo="value+percent initial",
            marker=dict(
                color=["#1f77b4", "#ff7f0e", "#2ca02c"]
            )
        ))
        
        fig.update_layout(
            title="Market Sizing Analysis (USD Millions)",
            font=dict(size=14),
            height=400
        )
        
        return fig.to_json()
    
    @staticmethod
    def create_revenue_projection_chart(
        scenarios: Dict[str, List[float]],
        years: Optional[List[int]] = None
    ) -> str:
        """
        Create line chart with 3 revenue scenarios.
        
        Args:
            scenarios: Dict with 'base', 'upside', 'downside' keys
            years: Optional list of year labels
            
        Returns:
            Plotly chart as JSON string
        """
        if years is None:
            years = list(range(1, len(scenarios.get('base', [])) + 1))
        
        fig = go.Figure()
        
        # Base case
        if 'base' in scenarios:
            fig.add_trace(go.Scatter(
                x=years,
                y=scenarios['base'],
                mode='lines+markers',
                name='Base Case',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
        
        # Upside case
        if 'upside' in scenarios:
            fig.add_trace(go.Scatter(
                x=years,
                y=scenarios['upside'],
                mode='lines+markers',
                name='Upside',
                line=dict(color='#2ca02c', width=2, dash='dash'),
                marker=dict(size=6)
            ))
        
        # Downside case
        if 'downside' in scenarios:
            fig.add_trace(go.Scatter(
                x=years,
                y=scenarios['downside'],
                mode='lines+markers',
                name='Downside',
                line=dict(color='#d62728', width=2, dash='dash'),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="Revenue Projections - 3 Scenarios",
            xaxis_title="Year",
            yaxis_title="Revenue (USD Millions)",
            hovermode='x unified',
            font=dict(size=12),
            height=450,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_json()
    
    @staticmethod
    def create_porters_five_forces_chart(
        forces: Dict[str, Dict[str, any]]
    ) -> str:
        """
        Create radar chart for Porter's Five Forces.
        
        Args:
            forces: Dict with force names as keys, each containing 'score'
            
        Returns:
            Plotly chart as JSON string
        """
        # Extract force names and scores
        categories = []
        values = []
        
        force_labels = {
            'new_entrants': 'Threat of<br>New Entrants',
            'supplier_power': 'Supplier<br>Power',
            'buyer_power': 'Buyer<br>Power',
            'substitutes': 'Threat of<br>Substitutes',
            'rivalry': 'Competitive<br>Rivalry'
        }
        
        for key, label in force_labels.items():
            if key in forces:
                categories.append(label)
                values.append(forces[key].get('score', 0))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Industry Forces',
            line=dict(color='#ff7f0e', width=2),
            fillcolor='rgba(255, 127, 14, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickvals=[1, 2, 3, 4, 5],
                    ticktext=['1<br>Low', '2', '3<br>Medium', '4', '5<br>High']
                )
            ),
            title="Porter's Five Forces Analysis",
            font=dict(size=12),
            height=500,
            showlegend=False
        )
        
        return fig.to_json()
    
    @staticmethod
    def create_competitor_comparison(
        data: List[Dict[str, any]],
        metric: str = "revenue"
    ) -> str:
        """
        Create bar chart comparing competitors.
        
        Args:
            data: List of dicts with 'name' and metric keys
            metric: Metric to compare (default: 'revenue')
            
        Returns:
            Plotly chart as JSON string
        """
        companies = [d.get('name', 'Unknown') for d in data]
        values = [d.get(metric, 0) for d in data]
        
        fig = go.Figure(data=[
            go.Bar(
                x=companies,
                y=values,
                marker=dict(
                    color=values,
                    colorscale='Blues',
                    showscale=False
                ),
                text=values,
                texttemplate='%{text:.1f}M',
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title=f"Competitive Comparison - {metric.title()}",
            xaxis_title="Company",
            yaxis_title=f"{metric.title()} (USD Millions)",
            font=dict(size=12),
            height=400,
            showlegend=False
        )
        
        return fig.to_json()
    
    @staticmethod
    def create_unit_economics_chart(
        cac: float,
        ltv: float
    ) -> str:
        """
        Create bar chart showing CAC vs LTV.
        
        Args:
            cac: Customer Acquisition Cost
            ltv: Lifetime Value
            
        Returns:
            Plotly chart as JSON string
        """
        fig = go.Figure(data=[
            go.Bar(
                x=['CAC', 'LTV'],
                y=[cac, ltv],
                marker=dict(color=['#d62728', '#2ca02c']),
                text=[f'${cac:.0f}', f'${ltv:.0f}'],
                textposition='outside'
            )
        ])
        
        ratio = ltv / cac if cac > 0 else 0
        
        fig.update_layout(
            title=f"Unit Economics - LTV/CAC Ratio: {ratio:.1f}x",
            yaxis_title="Value (USD)",
            font=dict(size=12),
            height=400,
            showlegend=False
        )
        
        return fig.to_json()
    
    @staticmethod
    def create_risk_matrix_heatmap(risks: List[Dict]) -> str:
        """
        Create 5x5 risk matrix heatmap.
        
        Args:
            risks: List of risk dictionaries with probability and impact
            
        Returns:
            Plotly chart as JSON string
        """
        # Create 5x5 grid
        matrix = [[0]*5 for _ in range(5)]
        risk_labels = [[[] for _ in range(5)] for _ in range(5)]
        
        for risk in risks:
            prob = risk.get("probability", 3) - 1  # 0-indexed
            impact = risk.get("impact", 3) - 1
            
            # Ensure within bounds
            prob = max(0, min(4, prob))
            impact = max(0, min(4, impact))
            
            matrix[prob][impact] += 1
            risk_labels[prob][impact].append(risk.get("risk", "Unknown")[:30])
        
        # Create annotations
        annotations = []
        for i in range(5):
            for j in range(5):
                if matrix[i][j] > 0:
                    label = f"{matrix[i][j]} risk(s)"
                    if risk_labels[i][j]:
                        label += f"<br>{'<br>'.join(risk_labels[i][j][:2])}"
                    
                    annotations.append(
                        dict(
                            x=j,
                            y=i,
                            text=label,
                            showarrow=False,
                            font=dict(size=8, color='white' if matrix[i][j] > 2 else 'black')
                        )
                    )
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=['Minimal', 'Low', 'Medium', 'High', 'Critical'],
            y=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
            colorscale='Reds',
            showscale=True
        ))
        
        fig.update_layout(
            title="Regulatory Risk Matrix (Probability × Impact)",
            xaxis_title="Impact",
            yaxis_title="Probability",
            annotations=annotations,
            font=dict(size=12),
            height=500
        )
        
        return fig.to_json()

