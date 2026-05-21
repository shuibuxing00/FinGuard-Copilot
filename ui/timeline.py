"""
Timeline visualization module.
Displays user behavioral timeline with anomaly indicators.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional, List, Dict


def render_timeline() -> None:
    """
    Render user behavioral timeline showing login, transactions, and anomalies.
    """
    try:
        st.markdown("#### 📅 User Activity Timeline")
        
        # Generate sample timeline events
        events = _generate_timeline_events()
        
        if not events:
            st.info("No timeline events available.")
            return
        
        # Create timeline visualization
        fig = _create_timeline_chart(events)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not generate timeline visualization.")
    
    except Exception as e:
        st.error(f"Timeline rendering error: {str(e)}")


def _generate_timeline_events() -> List[Dict]:
    """
    Generate sample timeline events for demonstration.
    
    Returns:
        List of event dictionaries
    """
    events = [
        {
            'time': '08:00 AM',
            'event': 'Login',
            'device': 'PC (NY)',
            'risk': 'Low',
            'anomaly': False
        },
        {
            'time': '09:15 AM',
            'event': 'Transfer',
            'device': 'PC (NY)',
            'amount': '$5,000',
            'risk': 'Low',
            'anomaly': False
        },
        {
            'time': '02:30 AM',
            'event': 'Transfer',
            'device': 'Mobile (Unknown)',
            'amount': '$25,000',
            'risk': 'High',
            'anomaly': True
        },
        {
            'time': '03:00 AM',
            'event': 'Password Change',
            'device': 'Mobile (Unknown)',
            'risk': 'Critical',
            'anomaly': True
        },
        {
            'time': '03:15 AM',
            'event': 'Transfer',
            'device': 'Mobile (Unknown)',
            'amount': '$18,500',
            'risk': 'Critical',
            'anomaly': True
        },
        {
            'time': '10:30 AM',
            'event': 'Logout',
            'device': 'PC (NY)',
            'risk': 'Low',
            'anomaly': False
        }
    ]
    
    return events


def _create_timeline_chart(events: List[Dict]) -> Optional[go.Figure]:
    """
    Create timeline scatter plot with anomaly markers.
    
    Args:
        events: List of timeline events
        
    Returns:
        Plotly figure object
    """
    try:
        fig = go.Figure()
        
        # Process events
        normal_events = [e for e in events if not e.get('anomaly', False)]
        anomaly_events = [e for e in events if e.get('anomaly', False)]
        
        # Add normal events
        if normal_events:
            event_texts = [f"{e['event']}<br>{e['device']}" for e in normal_events]
            times = list(range(len(normal_events)))
            
            fig.add_trace(go.Scatter(
                x=times,
                y=[0] * len(normal_events),
                mode='markers',
                marker=dict(
                    size=12,
                    color='#4dabf7',  # Blue for normal
                    symbol='circle'
                ),
                text=event_texts,
                hovertemplate='%{text}<extra></extra>',
                name='Normal Activity',
                showlegend=True
            ))
        
        # Add anomaly events
        if anomaly_events:
            event_texts = [f"⚠️ {e['event']}<br>{e['device']}<br>Risk: {e['risk']}" 
                          for e in anomaly_events]
            times = [i for i in range(len(events)) if events[i].get('anomaly', False)]
            
            fig.add_trace(go.Scatter(
                x=times,
                y=[0.5] * len(anomaly_events),
                mode='markers',
                marker=dict(
                    size=16,
                    color='#ff6b6b',  # Red for anomalies
                    symbol='diamond',
                    line=dict(width=2, color='#ff0000')
                ),
                text=event_texts,
                hovertemplate='%{text}<extra></extra>',
                name='Anomalies',
                showlegend=True
            ))
        
        # Add event labels
        all_times = []
        all_labels = []
        all_y = []
        
        for i, event in enumerate(events):
            all_times.append(i)
            all_labels.append(event['time'])
            all_y.append(-0.3)
        
        fig.add_trace(go.Scatter(
            x=all_times,
            y=all_y,
            mode='text',
            text=all_labels,
            textposition='bottom center',
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Update layout
        fig.update_layout(
            title="User Behavior Timeline",
            xaxis_title="Activity Sequence",
            yaxis_title="",
            showlegend=True,
            hovermode='x unified',
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font=dict(color='#e6edf3', size=11),
            height=300,
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.5, 1]
            ),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#30363d',
                zeroline=False,
                showticklabels=False
            ),
            margin=dict(b=60, l=20, r=20, t=40)
        )
        
        return fig
    
    except Exception as e:
        print(f"Timeline chart error: {e}")
        return None
