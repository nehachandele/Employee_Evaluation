import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# ---------------- DATABASE ----------------
conn = sqlite3.connect("employees.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    password TEXT,
    role TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS performance(
    username TEXT,
    task INT,
    attendance INT,
    quality INT,
    behavior INT,
    avg REAL
)
""")

conn.commit()

# Default users
def create_default_users():
    c.execute("SELECT * FROM users")
    if not c.fetchall():
        c.execute("INSERT INTO users VALUES ('admin','admin123','admin')")
        c.execute("INSERT INTO users VALUES ('user','user123','user')")
        conn.commit()

create_default_users()

# ---------------- LOGIN ----------------
def login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

# ---------------- BACKEND ----------------
def evaluate_performance(data):
    performance = {
        "task": data[0],
        "attendance": data[1],
        "quality": data[2],
        "behavior": data[3]
    }

    rules = {
        "Excellent Performer": {
            "conditions": {"task": 80, "attendance": 85, "quality": 80, "behavior": 75},
            "advice": "Eligible for promotion and rewards.",
            "level": "High"
        },
        "Good Performer": {
            "conditions": {"task": 60, "attendance": 70, "quality": 65, "behavior": 60},
            "advice": "Consistent work. Can improve for higher roles.",
            "level": "Medium"
        },
        "Average Performer": {
            "conditions": {"task": 40, "attendance": 50, "quality": 50, "behavior": 50},
            "advice": "Needs improvement and training.",
            "level": "Low"
        },
        "Poor Performer": {
            "conditions": {"task": 0, "attendance": 40, "quality": 40, "behavior": 40},
            "advice": "Immediate improvement required.",
            "level": "Critical"
        }
    }

    results = []

    for role, info in rules.items():
        match = 0
        total = len(info["conditions"])

        for key in performance:
            if performance[key] >= info["conditions"][key]:
                match += 1

        confidence = (match / total) * 100

        if match > 0:
            results.append((role, confidence, info["advice"], info["level"]))

    results.sort(key=lambda x: x[1], reverse=True)

    return results

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="AI Performance System", layout="wide")

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:
    st.title("🔐 Login System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = user[0]
            st.session_state.role = user[2]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")

# ---------------- MAIN APP ----------------
else:
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📊 Performance Dashboard")

    # INPUT
    task = st.slider("Task", 0, 100, 70)
    attendance = st.slider("Attendance", 0, 100, 75)
    quality = st.slider("Quality", 0, 100, 65)
    behavior = st.slider("Behavior", 0, 100, 60)

    avg_score = (task + attendance + quality + behavior) / 4

    # SAVE DATA
    if st.button("💾 Save Performance"):
        c.execute("INSERT INTO performance VALUES (?,?,?,?,?,?)",
                  (st.session_state.username, task, attendance, quality, behavior, avg_score))
        conn.commit()
        st.success("Data Saved to Database")

    # USER CHART
    df = pd.DataFrame({
        "Category": ["Task", "Attendance", "Quality", "Behavior"],
        "Score": [task, attendance, quality, behavior]
    })
    st.bar_chart(df.set_index("Category"))

    # EVALUATION
    if st.button("🚀 Evaluate"):
        results = evaluate_performance([task, attendance, quality, behavior])

        st.subheader("Results")

        for role, confidence, advice, level in results:
            st.write(f"{role} | {confidence:.2f}% | {level}")
            st.progress(int(confidence))

        # SMART SUGGESTIONS
        st.subheader("🤖 Smart Suggestions")

        if task < 60:
            st.warning("Improve task performance")
        if attendance < 70:
            st.warning("Improve attendance")
        if quality < 65:
            st.warning("Improve quality")
        if behavior < 60:
            st.warning("Improve behavior")

        if avg_score > 80:
            st.success("Excellent overall performance!")

    # ---------------- ADMIN PANEL (IMPROVED) ----------------
    # ---------------- ADMIN PANEL (ENHANCED VISUALS) ----------------
    if st.session_state.role == "admin":
        st.subheader("📊 Admin Analytics Dashboard")

        data = pd.read_sql("SELECT * FROM performance", conn)
        st.dataframe(data)

        if not data.empty:

            colors = ["#4CAF50", "#2196F3", "#FF9800", "#E91E63"]
            avg_data = data.groupby("username")["avg"].mean()

            col1, col2 = st.columns(2)

            # Chart 1
            with col1:
                fig1, ax1 = plt.subplots(figsize=(4,2.5))
                ax1.bar(avg_data.index, avg_data.values, color="#4CAF50")
                ax1.set_title("Employee Avg")
                st.pyplot(fig1)

            # Chart 2
            with col2:
                selected_user = st.selectbox("Select Employee", data["username"].unique())
                user_data = data[data["username"] == selected_user]

                if not user_data.empty:
                    latest = user_data.iloc[-1]
                    categories = ["Task", "Attendance", "Quality", "Behavior"]
                    values = [latest["task"], latest["attendance"], latest["quality"], latest["behavior"]]

                    fig2, ax2 = plt.subplots(figsize=(4,2.5))
                    ax2.barh(categories, values, color=colors)
                    st.pyplot(fig2)

            col3, col4 = st.columns(2)

            # Pie
            with col3:
                weak = data[["task","attendance","quality","behavior"]].mean()
                fig3, ax3 = plt.subplots(figsize=(3,3))
                ax3.pie(weak, labels=weak.index, autopct='%1.1f%%', colors=colors)
                st.pyplot(fig3)

            # Line
            with col4:
                fig4, ax4 = plt.subplots(figsize=(4,2.5))
                ax4.plot(data["avg"], marker='o', color="#2196F3")
                ax4.set_title("Trend")
                st.pyplot(fig4)
# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("💡 Developed using Streamlit | Advanced Mini Project")