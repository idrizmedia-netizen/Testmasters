import streamlit as st
import pandas as pd
import time
import requests
import random
from datetime import datetime
import streamlit.components.v1 as components
import gspread
from google.oauth2 import service_account

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SECRETS VA ULANISH
try:
    TELEGRAM_TOKEN = st.secrets["general"]["telegram_token"]
    CHAT_ID = st.secrets["general"]["chat_id"]
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U")
    result_sheet = sh.worksheet("Results")
except Exception as e:
    st.error(f"Sozalamalarda xatolik: {e}")
    st.stop()

# --- YORDAMCHI FUNKSIYALAR ---

@st.cache_data(ttl=600)
def load_questions():
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTA1Ws84mZCqZvmj53YWxR3Xd7_Qd8V-Ro_w_79eklEXyDOt0BP6Vr8WJUodsXUo3WYb3sYMBijM5k9/pub?output=csv"
        df = pd.read_csv(csv_url)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return None
    except: return None

@st.cache_data(ttl=300)
def get_results_cached():
    try: return pd.DataFrame(result_sheet.get_all_records())
    except: return pd.DataFrame()

def check_already_finished(name, subject, category):
    df = get_results_cached()
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if 'Tur' in df.columns:
            exists = df[(df['Ism-familiya'].astype(str) == str(name)) & (df['Fan'].astype(str) == str(subject)) & (df['Tur'].astype(str) == str(category))]
        else:
            exists = df[(df['Ism-familiya'].astype(str) == str(name)) & (df['Fan'].astype(str) == str(subject))]
        return len(exists) > 0
    return False

def background_tasks(name, subject, category, corrects, total, ball):
    try:
        row = [datetime.now().strftime("%Y-%m-%d %H:%M"), str(name), str(category), str(subject), int(corrects), int(total - corrects), f"{ball}%"]
        result_sheet.append_row(row)
        st.cache_data.clear() 
    except: pass
    try:
        text = f"🏆 YANGI NATIJA!\n👤: {name}\n📂: {category}\n📚: {subject}\n📊: {ball}%"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except: pass

# --- TAYMER VA STIL ---
def show_smooth_timer(seconds):
    timer_html = f"""
    <div id="timer" style="font-size: 30px; font-weight: bold; color: #00C9FF; text-align: center; 
         background: rgba(0,0,0,0.5); padding: 15px; border-radius: 10px; border: 1px solid #00C9FF;">
        {seconds//60:02d}:{seconds%60:02d}
    </div>
    <script>
        var timeLeft = {seconds};
        var timerDiv = document.getElementById("timer");
        var interval = setInterval(function() {{
            timeLeft--;
            var minutes = Math.floor(timeLeft / 60);
            var seconds = timeLeft % 60;
            timerDiv.innerHTML = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
            if (timeLeft <= 0) {{ clearInterval(interval); }}
        }}, 1000);
    </script>
    """
    st.sidebar.markdown("### ⏱ VAQT")
    components.html(timer_html, height=100)

def apply_styles(subject="Default"):
    st.markdown(f"""
    <style>
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000") no-repeat center center fixed !important; 
        background-size: cover !important; 
        background-color: #0e1117 !important;
    }}
    h1, h2, h3, p, label, .stMarkdown, .stText, .stRadio label {{ color: white !important; }}
    [data-testid="stSidebar"] {{ background-color: #1a1c22 !important; }}
    .main-card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; }}
    div.stButton > button {{ width: 100%; background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; color: #001f3f !important; font-weight: 800 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- SAHIFALAR ---
if 'page' not in st.session_state: st.session_state.page = "HOME"

if st.session_state.page == "RESULT":
    apply_styles()
    res = st.session_state.final_score
    st.markdown(f'<div class="main-card" style="text-align:center;"><h1>{res["ball"]}%</h1><h2>{res["name"]}</h2></div>', unsafe_allow_html=True)
    if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"): st.session_state.page = "HOME"; st.rerun()

elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    show_smooth_timer(st.session_state.total_time)
    st.markdown(f"### 📚 Fan: {st.session_state.selected_subject} ({st.session_state.category})")
    with st.form(key="quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"**{i+1}. {item['q']}**")
            if pd.notna(item['image']) and str(item['image']) != '0': st.image(item['image'])
            user_answers[i] = st.radio("Tanlang:", item['o'], index=None, key=f"q_{i}")
        if st.form_submit_button("🏁 TESTNI TUGATISH"):
            corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]).lower() == str(item['map'].get(str(item['c']).upper(), item['c'])).lower())
            ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
            st.session_state.update({"final_score": {"name": st.session_state.full_name, "ball": ball}, "page": "RESULT"})
            background_tasks(st.session_state.full_name, st.session_state.selected_subject, st.session_state.category, corrects, len(st.session_state.test_items), ball)
            st.rerun()

elif st.session_state.page == "HOME":
    apply_styles()
    st.markdown("<h1 style='text-align:center;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
    category = st.radio("Bo'limni tanlang:", ["O'quvchi", "Attestatsiya", "Sertifikat"], index=None)
    if category:
        u_name = st.text_input("Ism-familiyangiz:")
        q_df = load_questions()
        if q_df is not None:
            filtered_subs = q_df[q_df['Tur'] == category]['Fan'].dropna().unique().tolist()
            selected_subject = st.selectbox("Fanni tanlang:", sorted(filtered_subs))
            if st.button("🚀 TESTNI BOSHLASH"):
                sub_qs = q_df[(q_df['Fan'] == selected_subject) & (q_df['Tur'] == category)]
                sampled_qs = sub_qs.sample(n=min(len(sub_qs), 30))
                # Vaqtni avtomatik hisoblash
                total_time = int(sampled_qs['Vaqt'].fillna(45).sum()) 
                test_items = [{"q": r['Savol'], "o": [v for v in {'A':str(r.get('A','')),'B':str(r.get('B','')),'C':str(r.get('C','')),'D':str(r.get('D',''))}.values() if str(v)!='nan'], "c": r['Javob'], "map": {'A':str(r.get('A','')),'B':str(r.get('B','')),'C':str(r.get('C','')),'D':str(r.get('D',''))}, "image": r.get('Rasm')} for _, r in sampled_qs.iterrows()]
                st.session_state.update({"full_name": u_name, "category": category, "selected_subject": selected_subject, "test_items": test_items, "total_time": total_time, "page": "TEST"})
                st.rerun()
