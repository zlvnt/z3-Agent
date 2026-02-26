"""
Streamlit monitoring dashboard for z3-Agent.

Run with: streamlit run app/monitoring/dashboard.py
"""

try:
    import streamlit as st
    import requests
    import time

    API_BASE = "http://localhost:8000"

    st.set_page_config(
        page_title="z3-Agent Monitoring",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("z3-Agent Monitoring Dashboard")

    # Fetch metrics
    try:
        metrics = requests.get(f"{API_BASE}/metrics", timeout=5).json()
    except Exception:
        st.error("Cannot connect to backend. Is it running?")
        st.stop()

    summary = metrics.get("summary", {})
    alerts = metrics.get("alerts", {})
    rag = metrics.get("rag", {})
    users = metrics.get("users", {})

    # Overview cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Requests", summary.get("total_requests", 0))
    col2.metric("Error Rate", f"{summary.get('error_rate', 0):.1%}")
    col3.metric("Avg Response Time", f"{summary.get('avg_response_time', 0):.2f}s")
    col4.metric("Uptime", f"{summary.get('uptime_seconds', 0) / 3600:.1f}h")

    # Alert status
    if alerts.get("high_error_rate") or alerts.get("slow_response"):
        st.warning("Active alerts detected!")

    # RAG stats
    st.subheader("RAG System")
    rcol1, rcol2, rcol3 = st.columns(3)
    rcol1.metric("Total Queries", rag.get("total_queries", 0))
    rcol2.metric("Success Rate", f"{rag.get('success_rate', 0):.1%}")
    rcol3.metric("Top Mode", rag.get("most_used_mode", "-"))

    routing = rag.get("routing_distribution", {})
    if routing:
        st.bar_chart(routing)

    # User stats
    st.subheader("User Activity")
    ucol1, ucol2 = st.columns(2)
    ucol1.metric("Unique Users Today", users.get("unique_users_today", 0))
    ucol2.metric("Avg Requests/User", users.get("avg_requests_per_user", 0))

    # Recent requests
    st.subheader("Recent Requests")
    try:
        req_data = requests.get(f"{API_BASE}/metrics/requests", timeout=5).json()
        recent = req_data.get("recent_requests", [])
        if recent:
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No recent requests")
    except Exception:
        st.error("Failed to load recent requests")

    # Auto refresh
    time.sleep(10)
    st.rerun()

except ImportError:
    print("Streamlit not installed. Run: pip install streamlit")
