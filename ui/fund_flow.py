"""
Fund Flow visualization module.
Displays directed graph of fund movements between accounts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple


def render_fund_flow(transactions_df: Optional[pd.DataFrame] = None) -> None:
    """
    Render fund flow diagram showing transaction patterns.
    
    Args:
        transactions_df: Transactions dataframe with from_id, to_id, amount columns
    """
    try:
        st.markdown("#### 💸 Fund Flow Network")
        
        if transactions_df is None or transactions_df.empty:
            st.info("No transaction data available for fund flow visualization.")
            return
        
        # Create network graph
        fig = _create_fund_flow_graph(transactions_df)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not generate fund flow visualization.")
    
    except Exception as e:
        st.error(f"Fund flow rendering error: {str(e)}")


def _create_fund_flow_graph(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create directed graph of fund movements.
    
    Args:
        df: Transactions dataframe
        
    Returns:
        Plotly figure object
    """
    try:
        # Handle different column names
        from_col = 'from_account' if 'from_account' in df.columns else 'user_id'
        to_col = 'to_account' if 'to_account' in df.columns else 'recipient_id'
        
        if from_col not in df.columns or to_col not in df.columns:
            return None
        
        # Aggregate flows
        flows = _aggregate_flows(df, from_col, to_col)
        
        if not flows:
            return None
        
        # Create nodes and edges
        nodes, edges, edge_colors, edge_widths = _prepare_graph_data(flows, df)
        
        # Build figure
        fig = go.Figure()
        
        # Add edges
        for edge, color, width in zip(edges, edge_colors, edge_widths):
            x = [edge['start'][0], edge['end'][0]]
            y = [edge['start'][1], edge['end'][1]]
            
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                line=dict(width=width, color=color),
                hovertemplate=f"{edge['label']}<br>Amount: ${edge['amount']:.0f}<extra></extra>",
                showlegend=False
            ))
        
        # Add nodes
        node_x = [n['pos'][0] for n in nodes]
        node_y = [n['pos'][1] for n in nodes]
        node_colors = [n['color'] for n in nodes]
        node_sizes = [n['size'] for n in nodes]
        node_labels = [n['label'] for n in nodes]
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_labels,
            textposition='top center',
            hovertemplate='%{text}<br>Risk: High<extra></extra>',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                opacity=0.8,
                line=dict(width=2, color='white')
            ),
            showlegend=False
        ))
        
        # Style figure
        fig.update_layout(
            title="Fund Movement Network (High Risk Accounts in Red)",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font=dict(color='#e6edf3', size=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400
        )
        
        return fig
    
    except Exception as e:
        print(f"Fund flow graph error: {e}")
        return None


def _aggregate_flows(
    df: pd.DataFrame,
    from_col: str,
    to_col: str
) -> Dict[Tuple[str, str], Dict]:
    """
    Aggregate flows between account pairs.
    
    Args:
        df: Transactions dataframe
        from_col: Source column name
        to_col: Destination column name
        
    Returns:
        Dictionary of flows with aggregated amounts
    """
    flows = {}
    
    for _, row in df.iterrows():
        try:
            from_account = str(row.get(from_col, 'Unknown'))
            to_account = str(row.get(to_col, 'Unknown'))
            amount = float(row.get('amount', 0))
            risk_score = float(row.get('risk_score', 0))
            
            if from_account and to_account:
                key = (from_account, to_account)
                
                if key not in flows:
                    flows[key] = {
                        'amount': 0,
                        'count': 0,
                        'max_risk': risk_score
                    }
                
                flows[key]['amount'] += amount
                flows[key]['count'] += 1
                flows[key]['max_risk'] = max(flows[key]['max_risk'], risk_score)
        
        except (ValueError, TypeError):
            continue
    
    return flows


def _prepare_graph_data(
    flows: Dict[Tuple[str, str], Dict],
    df: pd.DataFrame
) -> Tuple[List, List, List, List]:
    """
    Prepare nodes and edges for Plotly visualization.
    
    Args:
        flows: Aggregated flows
        df: Original dataframe for risk scoring
        
    Returns:
        Tuple of (nodes, edges, edge_colors, edge_widths)
    """
    import math
    
    # Get unique accounts
    accounts = set()
    for (from_acc, to_acc) in flows.keys():
        accounts.add(from_acc)
        accounts.add(to_acc)
    
    accounts = list(accounts)
    
    # Position nodes in circle
    nodes = []
    node_dict = {}
    
    for i, account in enumerate(accounts):
        angle = 2 * math.pi * i / len(accounts)
        x = math.cos(angle)
        y = math.sin(angle)
        
        # Determine if high risk
        is_high_risk = _is_high_risk_account(account, df)
        
        node = {
            'label': account[:8],  # Truncate for display
            'pos': (x, y),
            'color': '#ff6b6b' if is_high_risk else '#4dabf7',  # Red for high risk, blue for normal
            'size': 20 if is_high_risk else 15
        }
        
        nodes.append(node)
        node_dict[account] = (x, y)
    
    # Create edges
    edges = []
    edge_colors = []
    edge_widths = []
    
    max_amount = max((flow['amount'] for flow in flows.values()), default=1)
    
    for (from_acc, to_acc), flow in flows.items():
        if from_acc in node_dict and to_acc in node_dict:
            edge = {
                'start': node_dict[from_acc],
                'end': node_dict[to_acc],
                'label': f"{from_acc[:6]}→{to_acc[:6]}",
                'amount': flow['amount']
            }
            
            edges.append(edge)
            
            # Color based on risk
            is_high_risk_flow = flow['max_risk'] > 70
            color = '#ff6b6b' if is_high_risk_flow else '#4dabf7'
            edge_colors.append(color)
            
            # Width based on volume
            normalized_width = 1 + (flow['amount'] / max_amount) * 5
            edge_widths.append(normalized_width)
    
    return nodes, edges, edge_colors, edge_widths


def _is_high_risk_account(account: str, df: pd.DataFrame) -> bool:
    """
    Check if account is marked as high risk.
    
    Args:
        account: Account identifier
        df: Transactions dataframe
        
    Returns:
        True if account has high risk transactions
    """
    try:
        from_col = 'from_account' if 'from_account' in df.columns else 'user_id'
        
        account_txns = df[df.get(from_col, '') == account]
        
        if account_txns.empty:
            return False
        
        # Check risk score
        avg_risk = account_txns.get('risk_score', pd.Series()).mean()
        
        return avg_risk > 50
    
    except Exception:
        return False
