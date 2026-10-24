import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "buildpay_streamlit.db"

SITES = [
    "Orchid Residency · Site A",
    "Metro Tower · Site B",
    "Riverfront Villas · Site C",
]
INITIAL_WORKERS = [
    ("23491A1213", "M.VYSHNAVI", "Mason", 850, SITES[0], "Skilled", "Pending", "1234"),
    ("23491A1214", "M.AISWARYA", "Electrician", 950, SITES[1], "Skilled", "Pending", "1234"),
    ("23491A1216", "N.GREESHMA", "Helper", 600, SITES[0], "Unskilled", "Pending", "1234"),
    ("23491A1218", "P.VARSHITHA", "Carpenter", 900, SITES[2], "Skilled", "Pending", "1234"),
    ("23491A1222", "A.KOWSHIK REDDY", "Plumber", 1000, SITES[1], "Skilled", "Pending", "1234"),
    ("23491A1254", "M.SANTHOSH", "Mason", 850, SITES[2], "Skilled", "Pending", "1234"),
    ("BP1001", "Ravi Kumar", "Mason", 850, SITES[0], "Skilled", "Completed", "1234"),
    ("BP1002", "Suresh Naidu", "Electrician", 950, SITES[1], "Skilled", "Completed", "1234"),
    ("BP1003", "Lakshmi Devi", "Painter", 750, SITES[0], "Semi-skilled", "Pending", "1234"),
    ("BP1004", "Arjun Reddy", "Carpenter", 900, SITES[1], "Skilled", "Completed", "1234"),
    ("BP1005", "Manoj Das", "Helper / General labour", 600, SITES[0], "Unskilled", "Pending", "1234"),
    ("BP1006", "Imran Khan", "Steel fixer", 875, SITES[2], "Skilled", "Completed", "1234"),
]

st.set_page_config(page_title="BuildPay | Construction Payroll", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
.stApp { background: #f4f7fb; color: #101828; }
section[data-testid="stSidebar"] { background: #071a35; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
h1,h2,h3,h4,p,label,span,div[data-testid="stMetricLabel"] { color: #101828; }
div[data-testid="stMetric"] { background: #ffffff; padding: 16px; border-radius: 12px; border: 1px solid #e4e7ec; }
div.stButton > button { background: #0b5fff; color: #ffffff; border-radius: 8px; border: 0; font-weight: 600; }
div.stButton > button:hover { background: #0847c7; color: white; }
[data-testid="stDataFrame"] { background: white; }
</style>
""", unsafe_allow_html=True)

def connect_db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    with connect_db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT DEFAULT '',
            site TEXT NOT NULL,
            wage REAL NOT NULL CHECK(wage >= 0),
            worker_type TEXT NOT NULL DEFAULT 'Skilled',
            emergency TEXT DEFAULT '',
            safety TEXT NOT NULL DEFAULT 'Pending',
            pin TEXT NOT NULL DEFAULT '1234',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT NOT NULL,
            work_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Late','Absent')),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(worker_id, work_date),
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE CASCADE
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
        if count == 0:
            for wid, name, role, wage, site, wtype, safety, pin in INITIAL_WORKERS:
                con.execute("""INSERT INTO workers
                    (id,name,role,wage,site,worker_type,safety,pin)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (wid, name, role, wage, site, wtype, safety, pin))
            roles = ["Helper / General labour", "Mason", "Electrician", "Plumber",
                     "Carpenter", "Machine operator", "Painter", "Steel fixer",
                     "Site supervisor", "Helper / General labour", "Mason", "Plumber"]
            names = ["Kiran Kumar", "Ramesh Babu", "Anil Prasad", "Vijay Rao",
                     "Sita Ram", "Naveen Kumar", "Raju", "Mohan", "Prakash",
                     "Kavitha", "Ravi Teja", "Srinivas"]
            wages = [600, 750, 850, 900, 950, 700, 800, 875, 1200, 600, 850, 900]
            for i in range(12):
                con.execute("""INSERT INTO workers
                    (id,name,role,wage,site,worker_type,safety,pin)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (f"BP{1007+i}", names[i], roles[i], wages[i], SITES[i % 3],
                     "Unskilled" if wages[i] <= 650 else "Skilled",
                     "Pending" if i % 4 == 0 else "Completed", "1234"))
init_db()

def fetch_workers():
    with connect_db() as con:
        return pd.read_sql_query(
            "SELECT id, name, role, phone, site, wage, worker_type, emergency, safety FROM workers ORDER BY name",
            con)

def fetch_attendance(work_date):
    with connect_db() as con:
        return pd.read_sql_query("""
            SELECT w.id AS worker_id, w.name, w.role, w.site, w.wage,
                   COALESCE(a.status, 'Present') AS status
            FROM workers w
            LEFT JOIN attendance a ON a.worker_id=w.id AND a.work_date=?
            ORDER BY w.name
        """, con, params=(str(work_date),))

def login(role, user_id, pin):
    if role == "Admin":
        return user_id.strip().lower() == "admin" and pin == "admin123", None
    with connect_db() as con:
        row = con.execute("SELECT * FROM workers WHERE lower(id)=lower(?) AND pin=?",
                          (user_id.strip(), pin)).fetchone()
    return (row is not None), (dict(row) if row else None)

def money(value):
    return f"₹{float(value):,.2f}"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None
if "worker" not in st.session_state:
    st.session_state.worker = None

with st.sidebar:
    st.markdown("# 🏗️ BuildPay")
    st.caption("Construction Payroll Management")
    st.divider()
    if st.session_state.authenticated:
        st.success(f"Signed in: {st.session_state.role}")
        if st.button("Log out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.worker = None
            st.rerun()
    else:
        st.info("Please sign in to continue.")
    st.caption("Academic demo • Do not use real payroll data")

st.title("BuildPay")
st.subheader("Smart Construction Worker Payroll Management")
st.write("Manage worker records, daily attendance, payroll estimates and worker self-service.")

if not st.session_state.authenticated:
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### Welcome back")
        st.write("Sign in to open the admin dashboard or worker portal.")
        st.markdown("- Worker records and wage details")
        st.markdown("- Date-wise attendance")
        st.markdown("- Payroll estimates and CSV exports")
    with right:
        with st.container(border=True):
            st.markdown("### Sign in")
            role = st.radio("Login as", ["Worker", "Admin"], horizontal=True)
            user_id = st.text_input("Worker ID / Admin username",
                                    value="" if role == "Worker" else "admin")
            pin = st.text_input("PIN / Password", type="password")
            if st.button("Sign in", use_container_width=True):
                ok, worker = login(role, user_id, pin)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.role = role
                    st.session_state.worker = worker
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error("Login details are incorrect.")
            with st.expander("Demo login details"):
                st.write("Admin username: `admin`")
                st.write("Admin password: `admin123`")
                st.write("Worker IDs: `23491A1213`, `23491A1214`, `23491A1216`, `23491A1218`, `23491A1222`, `23491A1254`")
                st.write("Worker PIN: `1234`")
    st.stop()

if st.session_state.role == "Worker":
    worker = st.session_state.worker
    with connect_db() as con:
        row = con.execute("SELECT * FROM workers WHERE id=?", (worker["id"],)).fetchone()
    if row is None:
        st.error("Worker record was not found. Please log in again.")
        st.stop()
    worker = dict(row)
    st.header("👷 Worker Portal")
    st.write(f"Welcome, **{worker['name']}**")
    a, b, c, d = st.columns(4)
    a.metric("Worker ID", worker["id"])
    b.metric("Daily wage", money(worker["wage"]))
    c.metric("Role", worker["role"])
    d.metric("Safety induction", worker["safety"])
    st.markdown("### My profile")
    st.dataframe(pd.DataFrame([{
        "Name": worker["name"], "Phone": worker["phone"], "Role": worker["role"],
        "Site": worker["site"], "Worker type": worker["worker_type"],
        "Emergency contact": worker["emergency"]
    }]), use_container_width=True, hide_index=True)
    chosen_month = st.date_input("Choose a date to view attendance", value=date.today())
    with connect_db() as con:
        att = pd.read_sql_query(
            "SELECT work_date, status FROM attendance WHERE worker_id=? AND work_date=?",
            con, params=(worker["id"], chosen_month.isoformat()))
    if att.empty:
        st.info(f"No attendance record saved for {chosen_month.isoformat()}. Ask the site admin to update it.")
    else:
        st.dataframe(att, use_container_width=True, hide_index=True)
    st.markdown("### Estimated monthly pay")
    days = st.slider("Paid work days", 0, 31, 26)
    overtime = st.number_input("Overtime hours", min_value=0.0, value=0.0, step=1.0)
    deductions = st.number_input("Deductions (₹)", min_value=0.0, value=0.0, step=50.0)
    gross = worker["wage"] * days + (worker["wage"] / 8 * 1.5 * overtime)
    st.metric("Estimated net pay", money(max(0, gross - deductions)))
    st.caption("This is an estimate only; confirm actual payroll with your employer.")

else:
    page = st.sidebar.radio("Admin menu", [
        "Dashboard", "Workers", "Attendance", "Payroll & Reports"
    ])
    workers = fetch_workers()
    today = date.today()
    att_today = fetch_attendance(today)
    if page == "Dashboard":
        st.header("📊 Admin Dashboard")
        total = len(workers)
        present = int(att_today["status"].isin(["Present", "Late"]).sum())
        absent = int((att_today["status"] == "Absent").sum())
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total workers", total)
        col2.metric("Present / Late today", present)
        col3.metric("Absent today", absent)
        col4.metric("Average daily wage", money(workers["wage"].mean() if total else 0))
        st.markdown("### Today's worker status")
        st.dataframe(att_today[["worker_id", "name", "role", "site", "wage", "status"]],
                     use_container_width=True, hide_index=True)
        st.download_button("Download worker list CSV", workers.to_csv(index=False).encode("utf-8"),
                           "buildpay_workers.csv", "text/csv")
    elif page == "Workers":
        st.header("👥 Worker Management")
        with st.expander("➕ Add a worker", expanded=False):
            with st.form("add_worker_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                name = c1.text_input("Full name *")
                role = c2.selectbox("Role", ["Helper / General labour", "Mason", "Electrician",
                    "Plumber", "Carpenter", "Machine operator", "Painter", "Steel fixer", "Site supervisor"])
                c3, c4 = st.columns(2)
                wage = c3.number_input("Daily wage (₹) *", min_value=1.0, value=700.0, step=50.0)
                site = c4.selectbox("Site", SITES)
                c5, c6 = st.columns(2)
                phone = c5.text_input("Phone")
                emergency = c6.text_input("Emergency contact")
                worker_type = st.selectbox("Worker type", ["Skilled", "Semi-skilled", "Unskilled"])
                safety = st.selectbox("Safety induction", ["Pending", "Completed"])
                submitted = st.form_submit_button("Save worker")
                if submitted:
                    if not name.strip():
                        st.error("Please enter the worker's name.")
                    else:
                        with connect_db() as con:
                            next_num = con.execute(
                                "SELECT COALESCE(MAX(CAST(substr(id,3) AS INTEGER)),1000)+1 FROM workers WHERE id LIKE 'BP%'"
                            ).fetchone()[0]
                            wid = f"BP{next_num}"
                            try:
                                con.execute("""INSERT INTO workers
                                    (id,name,role,phone,site,wage,worker_type,emergency,safety,pin)
                                    VALUES (?,?,?,?,?,?,?,?,?,'1234')""",
                                    (wid, name.strip(), role, phone.strip(), site, wage,
                                     worker_type, emergency.strip(), safety))
                                st.success(f"Worker added. New worker ID: {wid}; demo PIN: 1234")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Could not add worker. Please try again.")
        st.markdown("### Worker directory")
        st.dataframe(workers, use_container_width=True, hide_index=True)
        st.download_button("Export workers CSV", workers.to_csv(index=False).encode("utf-8"),
                           "buildpay_workers.csv", "text/csv")
    elif page == "Attendance":
        st.header("🗓️ Attendance Management")
        work_date = st.date_input("Attendance date", value=today, key="attendance_date")
        data = fetch_attendance(work_date)
        st.write("Set each worker's status, then save attendance.")
        edited = st.data_editor(
            data[["worker_id", "name", "role", "site", "status"]],
            use_container_width=True, hide_index=True,
            disabled=["worker_id", "name", "role", "site"],
            column_config={"status": st.column_config.SelectboxColumn(
                "Status", options=["Present", "Late", "Absent"], required=True)}
        )
        if st.button("💾 Save attendance", type="primary"):
            with connect_db() as con:
                for _, rec in edited.iterrows():
                    con.execute("""INSERT INTO attendance(worker_id,work_date,status)
                        VALUES(?,?,?) ON CONFLICT(worker_id,work_date) DO UPDATE SET
                        status=excluded.status, updated_at=CURRENT_TIMESTAMP""",
                        (rec["worker_id"], work_date.isoformat(), rec["status"]))
            st.success(f"Attendance saved for {work_date.isoformat()}.")
            st.rerun()
        st.download_button("Export attendance CSV", edited.to_csv(index=False).encode("utf-8"),
                           f"buildpay_attendance_{work_date.isoformat()}.csv", "text/csv")
    else:
        st.header("💰 Payroll & Reports")
        c1, c2, c3 = st.columns(3)
        days = c1.slider("Paid days", 0, 31, 26)
        overtime = c2.number_input("Overtime hours", min_value=0.0, value=6.0, step=1.0)
        deductions = c3.number_input("Deductions per worker (₹)", min_value=0.0, value=300.0, step=50.0)
        report = workers[["id", "name", "role", "site", "wage"]].copy()
        report["paid_days"] = days
        report["base_pay"] = report["wage"] * days
        report["overtime_pay"] = (report["wage"] / 8) * 1.5 * overtime
        report["deductions"] = deductions
        report["net_pay"] = (report["base_pay"] + report["overtime_pay"] - deductions).clip(lower=0)
        st.metric("Estimated payroll total", money(report["net_pay"].sum()))
        st.dataframe(report, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download payroll CSV", report.to_csv(index=False).encode("utf-8"),
                           "buildpay_payroll.csv", "text/csv")
        st.markdown("### Attendance summary")
        st.dataframe(att_today["status"].value_counts().rename_axis("Status").reset_index(name="Workers"),
                     use_container_width=True, hide_index=True)

st.divider()
st.caption("BuildPay academic demo. Demo credentials are not secure for production use.")
