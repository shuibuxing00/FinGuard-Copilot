"""
Dashboard module for risk metrics visualization.
Displays key compliance indicators and statistics.
"""

import streamlit as st
import pandas as pd
from typing import Optional


def render_dashboard(transactions_df: Optional[pd.DataFrame] = None) -> None:
    """
    Render risk metrics dashboard with key compliance indicators.
    
    Args:
        transactions_df: Transactions dataframe for analysis
    """
    try:
        st.markdown("### Compliance Dashboard")
        
        if transactions_df is None or transactions_df.empty:
            st.info("No transaction data available for analysis.")
            return
        
        # Calculate metrics
        metrics = _calculate_metrics(transactions_df)
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "High Risk",
                metrics['high_risk_count'],
                f"{metrics['high_risk_pct']:.1f}%"
            )
        
        with col2:
            st.metric(
                "Total Volume",
                f"${metrics['total_volume']:,.0f}",
                f"{metrics['avg_amount']:.0f} avg"
            )
        
        with col3:
            st.metric(
                "Unique Devices",
                metrics['device_anomalies'],
                "in dataset"
            )
        
        with col4:
            st.metric(
                "Rules Triggered",
                metrics['rules_triggered'],
                f"{metrics['avg_violations']:.1f} avg"
            )
        
        # Risk distribution chart
        st.markdown("#### Risk Distribution")
        risk_dist = _get_risk_distribution(transactions_df)
        
        if not risk_dist.empty:
            st.bar_chart(risk_dist)
        
    except Exception as e:
        st.error(f"Dashboard rendering error: {str(e)}")


def _calculate_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate compliance metrics from transactions.
    
    Args:
        df: Transactions dataframe
        
    Returns:
        Dictionary of metric values
    """
    try:
        total = len(df)
        
        # High risk = risk_score > 70 or anomaly detected
        high_risk = len(df[
            (df.get('risk_score', 0) > 70) |
            (df.get('anomaly_type', '').str.len() > 0)
        ]) if 'risk_score' in df.columns else 0
        
        # Total and average amounts
        total_volume = df.get('amount', pd.Series()).sum() if 'amount' in df.columns else 0
        avg_amount = df.get('amount', pd.Series()).mean() if 'amount' in df.columns else 0
        
        # Device anomalies
        device_anomalies = df['device_id'].nunique() if 'device_id' in df.columns else 0
        
        # Rules triggered
        rules_triggered = len(df[df.get('violation_flags', '') != ''])
        
        return {
            'high_risk_count': high_risk,
            'high_risk_pct': (high_risk / total * 100) if total > 0 else 0,
            'total_volume': total_volume,
            'avg_amount': avg_amount,
            'device_anomalies': device_anomalies,
            'rules_triggered': rules_triggered,
            'avg_violations': (rules_triggered / total) if total > 0 else 0
        }
    
    except Exception as e:
        print(f"Metric calculation error: {e}")
        return {
            'high_risk_count': 0,
            'high_risk_pct': 0,
            'total_volume': 0,
            'avg_amount': 0,
            'device_anomalies': 0,
            'rules_triggered': 0,
            'avg_violations': 0
        }


def _get_risk_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get risk score distribution for charting.
    
    Args:
        df: Transactions dataframe
        
    Returns:
        DataFrame with risk distribution
    """
    try:
        if 'risk_score' not in df.columns:
            return pd.DataFrame()
        
        # Bin risk scores
        bins = [0, 30, 50, 70, 100]
        labels = ['Low (0-30)', 'Medium (30-50)', 'High (50-70)', 'Critical (70+)']
        
        risk_bins = pd.cut(df['risk_score'], bins=bins, labels=labels, right=False)
        distribution = risk_bins.value_counts().sort_index()
        
        return distribution
    
    except Exception as e:
        print(f"Risk distribution error: {e}")
        return pd.DataFrame()
