# fear_to_top1_streamlit.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# ---------------------------
# CONFIG
# ---------------------------
DOMAINS = {
    "Coding": ["SQL", "Python", "SAS", "Tableau", "Power BI"],
    "Driving": ["Parking", "Traffic", "Highway"],
    "Business": ["Learning", "Idea Generation", "Execution"],
    "Trading": ["Paper Trading", "Backtesting", "Real Trading"],
    "Body Discipline": ["Workout", "Diet Logging", "Advanced Diet"]
}

LEVELS = {
    "Beginner": (0, 99),
    "Intermediate": (100, 299),
    "Pro": (300, 699),
    "Top 1%": (700, 9999)
}

XP_RULES = {
    "daily": 10,
    "weekly": 50,
    "monthly": 200
}

# ---------------------------
# FUNCTIONS
# ---------------------------
def get_level(xp):
    for lvl, (low, high) in LEVELS.items():
        if low <= xp <= high:
            return lvl
    return "Top 1%"

def calc_progress(data):
    progress = {}
    for domain, tasks in DOMAINS.items():
        xp_total = 0
        streak_total = 0
        for task in tasks:
            xp_total += data.loc[(data["Domain"] == domain) & (data["Task"] == task), "XP"].sum()
            streak_total += data.loc[(data["Domain"] == domain) & (data["Task"] == task), "Streak"].sum()
        progress[domain] = {
            "XP": xp_total,
            "Level": get_level(xp_total),
            "Avg_Streak": streak_total // len(tasks)
        }
    return progress

def recommendation(progress):
    # Suggest focus area (lowest XP domain)
    weakest = min(progress.items(), key=lambda x: x[1]["XP"])
    return f"Focus on **{weakest[0]}** – it has the lowest XP ({weakest[1]['XP']}), improve streaks here first!"

# ---------------------------
# STREAMLIT APP
# ---------------------------
st.set_page_config(page_title="Fear-to-Top1% Tracker", layout="wide")

st.title("🚀 Fear-to-Top 1% Tracker")
st.write("Track your progress across coding, driving, business, trading, and body discipline.")

# Load or initialize data
if "data" not in st.session_state:
    rows = []
    for domain, tasks in DOMAINS.items():
        for task in tasks:
            rows.append([domain, task, 0, 0])  # XP, Streak
    st.session_state.data = pd.DataFrame(rows, columns=["Domain", "Task", "XP", "Streak"])

df = st.session_state.data

# ---------------------------
# Update Section
# ---------------------------
st.header("✅ Daily Progress Update")
domain = st.selectbox("Select Domain", list(DOMAINS.keys()))
task = st.selectbox("Select Task", DOMAINS[domain])
done = st.checkbox("Task Completed Today?")

if st.button("Update Progress"):
    idx = df[(df["Domain"] == domain) & (df["Task"] == task)].index[0]
    if done:
        df.loc[idx, "XP"] += XP_RULES["daily"]
        df.loc[idx, "Streak"] += 1
    else:
        df.loc[idx, "Streak"] = 0
    st.success(f"Updated {task} in {domain}!")

# ---------------------------
# Live Dashboard
# ---------------------------
st.header("📊 Progress Dashboard")
progress = calc_progress(df)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Domain Overview")
    for domain, stats in progress.items():
        st.write(f"**{domain}** → XP: {stats['XP']}, Level: {stats['Level']}, Avg Streak: {stats['Avg_Streak']} days")

with col2:
    st.subheader("Live XP Chart")
    fig, ax = plt.subplots()
    ax.bar(progress.keys(), [stats["XP"] for stats in progress.values()], color="skyblue")
    ax.set_ylabel("XP Points")
    ax.set_title("XP by Domain")
    st.pyplot(fig)

# ---------------------------
# Task-Level Breakdown
# ---------------------------
st.header("🔍 Task-Level Tracking")
st.dataframe(df)

# ---------------------------
# Intelligence Tool
# ---------------------------
st.header("🧠 Smart Recommendation")
st.info(recommendation(progress))
