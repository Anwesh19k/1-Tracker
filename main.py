# advanced_tracker.py
import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Fear → Top 1% Tracker", layout="wide")

# ---------------- CONFIG ----------------
DOMAINS = {
    "Coding": ["SQL", "Python", "SAS", "Tableau", "Power BI"],
    "Driving": ["Parking", "Traffic", "Highway"],
    "Business": ["Learning", "Idea Generation", "Execution"],
    "Trading": ["Paper Trading", "Backtesting", "Real Trading"],
    "Body Discipline": ["Workout", "Diet Logging", "Advanced Diet"]
}

LEVELS = [
    ("Beginner", 0, 99),
    ("Intermediate", 100, 299),
    ("Pro", 300, 699),
    ("Top 1%", 700, 9999),
]

# ---------------- HELPERS ----------------
def get_level(xp:int) -> str:
    for name, lo, hi in LEVELS:
        if lo <= xp <= hi:
            return name
    return "Top 1%"

def create_gauge(domain, xp, goal=700):
    """Radial progress widget"""
    percent = min(100, int((xp / goal) * 100))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percent,
        title={'text': domain},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "limegreen"},
               'steps': [
                   {'range': [0, 30], 'color': "lightgray"},
                   {'range': [30, 70], 'color': "skyblue"},
                   {'range': [70, 100], 'color': "lightgreen"}]}
    ))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# ---------------- INIT DATA ----------------
if "data" not in st.session_state:
    rows = []
    for domain, tasks in DOMAINS.items():
        for t in tasks:
            rows.append([domain, t, 0, 0])
    st.session_state.data = pd.DataFrame(rows, columns=["Domain","Task","XP","Streak"])

df = st.session_state.data

# ---------------- UI: HEADER ----------------
st.markdown("<h1 style='text-align:center; color:#2b2b2b;'>🚀 Fear → Top 1% Tracker</h1>", unsafe_allow_html=True)
st.caption("iOS-style smart tracker with progress rings, streaks, and focus tips.")

# ---------------- UI: UPDATE ----------------
st.subheader("✅ Log Progress")
col1, col2, col3 = st.columns(3)
domain = col1.selectbox("Domain", DOMAINS.keys())
task = col2.selectbox("Task", DOMAINS[domain])
minutes = col3.number_input("Minutes", min_value=5, step=5, value=30)

if st.button("Add Progress", use_container_width=True):
    idx = df[(df["Domain"]==domain) & (df["Task"]==task)].index[0]
    df.loc[idx,"XP"] += minutes // 5 * 10   # 10 XP per 5 minutes
    df.loc[idx,"Streak"] += 1
    st.success(f"Updated {domain} → {task} (+{minutes//5*10} XP)")

# ---------------- DASHBOARD ----------------
st.subheader("📊 Domain Progress (iOS Widget Style)")

summary = df.groupby("Domain", as_index=False).agg({"XP":"sum","Streak":"mean"})
cols = st.columns(len(summary))

for i, row in summary.iterrows():
    with cols[i]:
        st.plotly_chart(create_gauge(row["Domain"], row["XP"]), use_container_width=True)
        st.metric("Level", get_level(row["XP"]))
        st.metric("Avg Streak", f"{int(row['Streak'])} days")

# ---------------- HISTORY ----------------
st.subheader("📈 XP Growth Over Time")
df["Date"] = dt.date.today()
daily = df.groupby(["Date","Domain"], as_index=False)["XP"].sum()
chart = px.line(daily, x="Date", y="XP", color="Domain", markers=True)
chart.update_layout(hovermode="x unified", height=350)
st.plotly_chart(chart, use_container_width=True)

# ---------------- SMART TIP ----------------
st.subheader("🧠 Smart Tip")
weakest = summary.sort_values("XP").iloc[0]
st.info(f"Focus today on **{weakest['Domain']}** — it has the lowest XP ({weakest['XP']}). Strengthening this will balance your growth!")
