# tracker_widgets.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime as dt

st.set_page_config(page_title="Fear → Top 1% Tracker", layout="wide")

# ---------------------------
# CONFIG
# ---------------------------
DOMAINS = ["Coding", "Driving", "Business", "Trading", "Body Discipline"]

# Dummy progress (replace with real calc later)
progress = {
    "Coding": {"XP": 220, "Streak": 7, "Goal": 700},
    "Driving": {"XP": 80, "Streak": 2, "Goal": 300},
    "Business": {"XP": 60, "Streak": 1, "Goal": 300},
    "Trading": {"XP": 150, "Streak": 5, "Goal": 500},
    "Body Discipline": {"XP": 320, "Streak": 10, "Goal": 700},
}

# ---------------------------
# CUSTOM CSS (Apple-like cards)
# ---------------------------
st.markdown("""
    <style>
    .apple-card {
        background: rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 20px;
        margin: 10px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 30px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.3);
        text-align: center;
        color: white;
    }
    .big-text { font-size: 24px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# FUNCTION: Circular Progress (Apple Fitness Style)
# ---------------------------
def circular_progress(title, value, goal, streak):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={'reference': goal, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, goal]},
            'bar': {'color': "lime"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, goal*0.5], 'color': "pink"},
                {'range': [goal*0.5, goal], 'color': "purple"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 6},
                'thickness': 0.8,
                'value': goal
            }
        }
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=250,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=16)
    )
    st.markdown(f"<div class='apple-card'><div class='big-text'>{title}</div><br>🔥 Streak: {streak} days</div>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# MAIN UI
# ---------------------------
st.title("🚀 Fear → Top 1% Tracker (iOS-Style)")

col1, col2, col3 = st.columns(3)
for i, domain in enumerate(DOMAINS):
    with [col1, col2, col3][i % 3]:
        data = progress[domain]
        circular_progress(domain, data["XP"], data["Goal"], data["Streak"])
