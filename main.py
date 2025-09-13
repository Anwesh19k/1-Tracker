# ================= Fear-to-Top1% Tracker — Streamlit (no matplotlib) =================
# Mobile-friendly tracker for Coding, Driving, Business, Trading, Body.
# - Separate tracking for SQL, Python, SAS, Tableau, Power BI, etc.
# - Advanced calculations: XP, streaks, unlocks, difficulty multipliers, decay.
# - Live charts (domain bar, time-series line) using Streamlit's native charts.
# - "Intelligence" recommendations on where to focus next.
#
# Run: streamlit run main.py

import streamlit as st
import pandas as pd
import datetime as dt
from pathlib import Path

st.set_page_config(page_title="Fear → Top 1% Tracker", layout="wide")

# --------------------------- CONFIG ---------------------------
DATA_FILE = Path("tracker_data.csv")
LOG_FILE  = Path("activity_log.csv")

DOMAINS = {
    "Coding": ["SQL", "Python", "SAS", "Tableau", "Power BI"],
    "Driving": ["Parking", "Traffic", "Highway"],
    "Business": ["Learning", "Idea Generation", "Execution"],
    "Trading": ["Paper Trading", "Backtesting", "Real Trading"],
    "Body Discipline": ["Workout", "Diet Logging", "Advanced Diet"]
}

# daily minutes goal per task (tweak freely)
GOALS_MIN = {
    "SQL": 45, "Python": 45, "SAS": 30, "Tableau": 30, "Power BI": 30,
    "Parking": 20, "Traffic": 20, "Highway": 20,
    "Learning": 15, "Idea Generation": 15, "Execution": 30,
    "Paper Trading": 15, "Backtesting": 30, "Real Trading": 10,
    "Workout": 30, "Diet Logging": 5, "Advanced Diet": 10
}

# difficulty 1–3 (affects XP multiplier)
DIFFICULTY = {
    "SQL": 2, "Python": 3, "SAS": 2, "Tableau": 2, "Power BI": 2,
    "Parking": 1, "Traffic": 2, "Highway": 3,
    "Learning": 1, "Idea Generation": 2, "Execution": 3,
    "Paper Trading": 1, "Backtesting": 2, "Real Trading": 3,
    "Workout": 2, "Diet Logging": 1, "Advanced Diet": 2
}

# priority weights per domain (used by recommender)
DOMAIN_WEIGHTS = {"Coding": 0.40, "Body Discipline": 0.20, "Driving": 0.15, "Business": 0.15, "Trading": 0.10}

LEVELS = [
    ("Beginner", 0, 99),
    ("Intermediate", 100, 299),
    ("Pro", 300, 699),
    ("Top 1%", 700, 999999),
]

BASE_XP = {"daily": 10, "weekly": 50, "monthly": 200}

UNLOCKS = {  # task -> condition(lambda df->bool)
    "Python":  lambda df: df.query("Task=='SQL'")["XP"].sum() >= 300,
    "Tableau": lambda df: df.query("Task=='Python'")["XP"].sum() >= 300,
    "Power BI":lambda df: df.query("Task=='Python'")["XP"].sum() >= 300,
    "SAS":     lambda df: df.query("Task=='Python'")["XP"].sum() >= 300,
    "Highway": lambda df: df.query("Task=='Traffic'")["XP"].sum() >= 200,
    "Execution": lambda df: df.query("Task=='Idea Generation'")["XP"].sum() >= 150,
    "Real Trading": lambda df: df.query("Task=='Paper Trading'")["XP"].sum() >= 200,
    "Advanced Diet": lambda df: df.query("Task=='Workout'")["Streak"].max() >= 14,
}

# --------------------------- INIT / LOAD ---------------------------
def init_data():
    rows = []
    for domain, tasks in DOMAINS.items():
        for t in tasks:
            rows.append([domain, t, 0, 0, None])  # XP, Streak, LastDone
    return pd.DataFrame(rows, columns=["Domain", "Task", "XP", "Streak", "LastDone"])

def load_df():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        # parse dates
        if "LastDone" in df.columns:
            df["LastDone"] = pd.to_datetime(df["LastDone"], errors="coerce").dt.date
        return df
    return init_data()

def load_log():
    if LOG_FILE.exists():
        log = pd.read_csv(LOG_FILE, parse_dates=["timestamp"])
        return log
    return pd.DataFrame(columns=["timestamp","date","domain","task","minutes","xp_gain","note"])

df = load_df()
log = load_log()

# --------------------------- HELPERS ---------------------------
def get_level(xp:int) -> str:
    for name, lo, hi in LEVELS:
        if lo <= xp <= hi:
            return name
    return "Top 1%"

def is_locked(task:str, df_state:pd.DataFrame) -> bool:
    cond = UNLOCKS.get(task)
    return (cond is not None) and (not cond(df_state))

def calc_decay(last_done:dt.date) -> float:
    """Gentle XP decay if idle: -1% per idle day after day 3, capped -20%."""
    if not last_done:
        return 1.0
    idle = (dt.date.today() - last_done).days
    if idle <= 3:
        return 1.0
    dec = min(0.20, 0.01 * (idle - 3))
    return 1.0 - dec

def xp_formula(task:str, minutes:int, met_goal:bool, current_streak:int) -> int:
    base = BASE_XP["daily"]
    goal = GOALS_MIN.get(task, 20)
    diff = DIFFICULTY.get(task, 2)
    ratio_bonus = min(1.5, max(0.2, minutes / goal))  # keeps within [0.2, 1.5]
    streak_bonus = 1 + min(0.30, current_streak * 0.03)  # up to +30%
    multiplier = (1 + (diff - 1) * 0.25) * ratio_bonus * streak_bonus
    xp = round(base * multiplier)
    # flat bonuses for milestones
    if met_goal and current_streak in (5, 10, 20, 30):
        xp += BASE_XP["weekly"]
    return xp

def update_progress(domain:str, task:str, minutes:int, met_goal:bool, note:str=""):
    global df, log

    # locked check
    if is_locked(task, df):
        st.warning(f"🔒 {task} is locked. Meet the unlock condition first.")
        return

    idx = df[(df["Domain"] == domain) & (df["Task"] == task)].index[0]

    today = dt.date.today()
    last = df.loc[idx, "LastDone"]
    # streak logic
    if last == today:
        # already logged today -> allow additive minutes/xp but don't bump streak twice
        current_streak = int(df.loc[idx, "Streak"])
    elif last == today - dt.timedelta(days=1):
        current_streak = int(df.loc[idx, "Streak"]) + 1
    else:
        current_streak = 1  # new streak starting today

    gain = xp_formula(task, minutes, met_goal, current_streak)
    # decay on existing XP for inactivity, then add gain
    decay_factor = calc_decay(last if last else None)
    df.loc[idx, "XP"] = int(round(df.loc[idx, "XP"] * decay_factor)) + gain
    df.loc[idx, "Streak"] = current_streak
    df.loc[idx, "LastDone"] = today

    # log row
    log = pd.concat([log, pd.DataFrame([{
        "timestamp": pd.Timestamp.utcnow(),
        "date": today,
        "domain": domain,
        "task": task,
        "minutes": minutes,
        "xp_gain": gain,
        "note": note
    }])], ignore_index=True)

    # persist
    df.to_csv(DATA_FILE, index=False)
    log.to_csv(LOG_FILE, index=False)

    st.success(f"Updated: {domain} → {task} | +{gain} XP | Streak = {current_streak}")

def domain_summary(df_state:pd.DataFrame) -> pd.DataFrame:
    agg = df_state.groupby("Domain", as_index=False).agg(
        XP=("XP","sum"),
        AvgStreak=("Streak","mean")
    )
    agg["Level"] = agg["XP"].apply(get_level)
    return agg.sort_values("XP", ascending=False)

def intelligence_tip(df_state:pd.DataFrame) -> str:
    # score combines low XP, low streak, long idle, and domain weight
    def score_row(r):
        idle_days = (dt.date.today() - r["LastDone"]).days if pd.notna(r["LastDone"]) else 999
        xp_term = 1 / (1 + r["XP"])
        streak_term = 1 / (1 + r["Streak"])
        idle_term = min(2.0, idle_days / 7)  # weekly penalty
        weight = DOMAIN_WEIGHTS.get(r["Domain"], 0.1)
        return (xp_term*0.5 + streak_term*0.3 + idle_term*0.2) * (1 + (0.4 - weight))  # lower weight → higher urgency
    tmp = df_state.copy()
    tmp["IdleScore"] = tmp.apply(score_row, axis=1)
    rec = tmp.sort_values("IdleScore", ascending=False).iloc[0]
    lock_note = " (locked—work on prerequisite)" if is_locked(rec["Task"], df_state) else ""
    return f"Focus next on **{rec['Domain']} → {rec['Task']}**{lock_note}. Idle score highest; boosting this raises overall balance fastest."

# --------------------------- UI — HEADER ---------------------------
st.title("🚀 Fear → Top 1% Tracker")
st.caption("Advanced, phased mastery across Coding, Driving, Business, Trading, and Body — with XP, streaks, unlocks, decay, and smart recommendations.")

# --------------------------- UI — UPDATE ---------------------------
with st.container():
    st.subheader("✅ Log Today's Progress")
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1, 1.6])
    domain = c1.selectbox("Domain", list(DOMAINS.keys()))
    task = c2.selectbox("Task", DOMAINS[domain])
    minutes = int(c3.number_input("Minutes", min_value=1, value=GOALS_MIN.get(task, 20), step=5))
    met_goal = c4.toggle(f"Met goal (≥ {GOALS_MIN.get(task, 20)} min)?", value=(minutes >= GOALS_MIN.get(task, 20)))
    note = st.text_input("Optional note")

    if st.button("Log Progress", use_container_width=True):
        update_progress(domain, task, minutes, met_goal, note)

# --------------------------- UI — DASHBOARD ---------------------------
st.divider()
st.subheader("📊 Domain Overview")
summary = domain_summary(df)

left, right = st.columns([1,1])
with left:
    st.dataframe(summary, use_container_width=True)
with right:
    st.bar_chart(summary.set_index("Domain")["XP"], height=280)

# --------------------------- UI — TASK TABLE ---------------------------
st.subheader("🔍 Task-Level Detail")
# add lock status for clarity
lock_status = []
for _, r in df.iterrows():
    lock_status.append("Locked" if is_locked(r["Task"], df) else "Unlocked")
df_view = df.copy()
df_view["Status"] = lock_status
st.dataframe(df_view.sort_values(["Domain","Task"]).reset_index(drop=True), use_container_width=True)

# --------------------------- UI — TIME SERIES ---------------------------
st.subheader("📈 Progress Over Time")
if not log.empty:
    daily = log.groupby(["date","domain"], as_index=False)["xp_gain"].sum()
    # pivot: rows = date, columns = domain, values = xp_gain
    pivot = daily.pivot(index="date", columns="domain", values="xp_gain").fillna(0)
    st.line_chart(pivot, height=300)
else:
    st.info("No history yet — log some progress to see your growth chart!")

# --------------------------- UI — INTELLIGENCE ---------------------------
st.subheader("🧠 Intelligence Recommendation")
st.info(intelligence_tip(df))

# --------------------------- FOOTER ---------------------------
with st.expander("How levels work / bonuses"):
    st.markdown(
        "- **Levels**: Beginner 0–99, Intermediate 100–299, Pro 300–699, Top 1% 700+  \n"
        "- **Bonuses**: Daily base XP scaled by minutes/goal, difficulty, and streak.  \n"
        "- **Milestones**: Extra +50 XP when your streak hits 5/10/20/30 on a task.  \n"
        "- **Decay**: After 3 idle days, gentle −1% XP/day on that task (max −20%) to keep you consistent.  \n"
        "- **Unlocks** (examples): Python after SQL 300 XP; Tableau/Power BI/SAS after Python 300 XP; Highway after Traffic 200 XP; Real Trading after Paper Trading 200 XP; Advanced Diet after 14-day Workout streak."
    )
