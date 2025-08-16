"""
Simple Streamlit dashboard for early-stage monitoring.
Shows real-time metrics without external dependencies.
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from .enhanced_metrics import get_enhanced_metrics_instance
from .simple_alerts import get_alerts_instance


def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="Instagram AI Agent - Monitoring",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("🤖 Instagram AI Agent - Real-Time Monitoring")
    st.markdown("*Simple dashboard for early-stage monitoring (100 queries/day)*")
    
    # Auto-refresh every 30 seconds
    if st.button("🔄 Refresh Data") or st.empty():
        st.rerun()
    
    # Get current metrics
    metrics = get_enhanced_metrics_instance()
    stats = metrics.get_enhanced_stats()
    alerts = get_alerts_instance()
    alert_status = alerts.get_alert_status()
    
    # Layout in columns
    col1, col2, col3, col4 = st.columns(4)
    
    # Key metrics cards
    with col1:
        st.metric(
            label="📊 Total Requests",
            value=stats['summary']['total_requests'],
            delta=f"{stats['recent_activity']['requests_last_hour']} last hour"
        )
    
    with col2:
        error_rate = stats['summary']['error_rate'] * 100
        st.metric(
            label="❌ Error Rate",
            value=f"{error_rate:.1f}%",
            delta=f"{stats['recent_activity']['errors_last_hour']} errors/hour",
            delta_color="inverse"
        )
    
    with col3:
        avg_time = stats['summary']['avg_response_time']
        st.metric(
            label="⏱️ Avg Response Time",
            value=f"{avg_time:.2f}s",
            delta="Good" if avg_time < 3.0 else "Slow",
            delta_color="normal" if avg_time < 3.0 else "inverse"
        )
    
    with col4:
        uptime_hours = stats['summary']['uptime_seconds'] / 3600
        st.metric(
            label="⚡ Uptime",
            value=f"{uptime_hours:.1f}h",
            delta=stats['health_status'].capitalize()
        )
    
    st.divider()
    
    # Channel breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📱 Channel Performance")
        
        if stats['channels']:
            channel_data = []
            for channel, data in stats['channels'].items():
                channel_data.append({
                    'Channel': channel.capitalize(),
                    'Requests': data['requests'],
                    'Error Rate': f"{data['error_rate']*100:.1f}%",
                    'Avg Time': f"{data['avg_response_time']:.2f}s",
                    'Last Hour': data['requests_last_hour']
                })
            
            df_channels = pd.DataFrame(channel_data)
            st.dataframe(df_channels, use_container_width=True)
            
            # Channel requests pie chart
            fig_pie = px.pie(
                df_channels, 
                values='Requests', 
                names='Channel',
                title="Requests by Channel"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No channel data available yet")
    
    with col2:
        st.subheader("🎯 RAG System Performance")
        
        rag_stats = stats['rag']
        
        # RAG metrics
        st.metric("Success Rate", f"{rag_stats['success_rate']*100:.1f}%")
        st.metric("Total Queries", rag_stats['total_queries'])
        st.metric("Most Used Mode", rag_stats.get('most_used_mode', 'none'))
        
        # Routing distribution
        if rag_stats['routing_distribution']:
            routing_data = [
                {'Mode': mode.capitalize(), 'Count': count}
                for mode, count in rag_stats['routing_distribution'].items()
            ]
            df_routing = pd.DataFrame(routing_data)
            
            fig_bar = px.bar(
                df_routing,
                x='Mode',
                y='Count',
                title="Routing Mode Distribution",
                color='Mode'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    # User activity and recent logs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 User Activity")
        
        user_stats = stats['users']
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Unique Users Today", user_stats['unique_users_today'])
            st.metric("Repeat Users", user_stats['repeat_users_today'])
        
        with col_b:
            st.metric("Total Sessions", user_stats['total_user_sessions'])
            st.metric("Avg Requests/User", f"{user_stats['avg_requests_per_user']:.1f}")
        
        # Most active users
        if user_stats['most_active_users']:
            st.write("**Most Active Users:**")
            for user, count in list(user_stats['most_active_users'].items())[:5]:
                st.write(f"• {user}: {count} requests")
    
    with col2:
        st.subheader("📋 Recent Activity")
        
        # Show recent log entries
        log_file = Path("logs/monitoring.jsonl")
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                recent_logs = []
                for line in lines[-10:]:  # Last 10 entries
                    try:
                        entry = json.loads(line)
                        recent_logs.append({
                            'Time': entry['timestamp'].split('T')[1][:8],
                            'Step': entry['step'],
                            'Duration': f"{entry['duration']:.3f}s",
                            'Severity': entry['severity']
                        })
                    except:
                        continue
                
                if recent_logs:
                    df_logs = pd.DataFrame(recent_logs)
                    st.dataframe(df_logs, use_container_width=True)
                else:
                    st.info("No recent log entries")
                    
            except Exception as e:
                st.error(f"Could not read logs: {e}")
        else:
            st.info("No log file found")
    
    st.divider()
    
    # Alert status
    st.subheader("🚨 Alert Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alert_color = "🟢" if alert_status['configured'] else "🔴"
        st.write(f"{alert_color} **Alert System:** {'Configured' if alert_status['configured'] else 'Not Configured'}")
        
        if not alert_status['configured']:
            st.warning("Set TELEGRAM_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID to enable alerts")
    
    with col2:
        st.write(f"**Error Threshold:** {alert_status['error_rate_threshold']*100:.0f}%")
        st.write(f"**Response Threshold:** {alert_status['response_time_threshold']:.1f}s")
        
        # Check current alert conditions
        current_alerts = stats.get('alerts', {})
        if current_alerts.get('high_error_rate'):
            st.error(f"🚨 High Error Rate: {current_alerts.get('error_rate_value', 0)*100:.1f}%")
        if current_alerts.get('slow_response'):
            st.warning(f"⏰ Slow Response: {current_alerts.get('avg_response_time_value', 0):.2f}s")
    
    with col3:
        st.write("**Current Status:**")
        
        # Show current metrics-based alerts
        if stats.get('alerts'):
            alert_data = stats['alerts']
            requests_hour = alert_data.get('requests_last_hour', 0)
            st.write(f"• Requests last hour: {requests_hour}")
            
            if alert_data.get('high_error_rate') or alert_data.get('slow_response'):
                st.error("⚠️ Active alerts detected!")
            else:
                st.success("✅ All systems normal")
        else:
            st.info("No alert data available")
    
    # Footer
    st.divider()
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh every 30s*")


def show_simple_metrics():
    """Alternative simple view for basic monitoring"""
    st.title("📊 Simple Metrics View")
    
    metrics = get_enhanced_metrics_instance()
    stats = metrics.get_enhanced_stats()
    
    # Basic overview
    st.write("## System Overview")
    st.write(f"- **Total Requests:** {stats['summary']['total_requests']}")
    st.write(f"- **Error Rate:** {stats['summary']['error_rate']*100:.1f}%")
    st.write(f"- **Average Response Time:** {stats['summary']['avg_response_time']:.2f}s")
    st.write(f"- **Health Status:** {stats['health_status'].title()}")
    
    # Channel breakdown
    if stats['channels']:
        st.write("## Channels")
        for channel, data in stats['channels'].items():
            st.write(f"**{channel.title()}:** {data['requests']} requests, {data['error_rate']*100:.1f}% errors")


if __name__ == "__main__":
    # Check if running in Streamlit
    try:
        main()
    except Exception as e:
        print(f"Error running dashboard: {e}")
        print("Try running with: streamlit run app/monitoring/dashboard.py")