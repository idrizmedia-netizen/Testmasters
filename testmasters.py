import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import gspread
from google.oauth2 import service_account  # Yangi import

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SECRETS VA ULANISH
try:
    TELEGRAM_TOKEN = st.secrets["general"]["telegram_token"]
    CHAT_ID = st.secrets["general"]["chat_id"]
    
    # GSheets o'qish uchun ulanish
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Sozalamalarda xatolik: {e}")
    st.stop()

# --- 3. YORDAMCHI FUNKSIYALAR ---

def load_questions():
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTA1Ws84mZCqZvmj53YWxR3Xd7_Qd8V-Ro_w_79eklEXyDOt0BP6Vr8WJUodsXUo3WYb3sYMBijM5k9/pub?output=csv"
        df = pd.read_csv(csv_url)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            if "Fan" in df.columns:
                return df
            else:
                st.error(f"Xato: Jadvalda 'Fan' ustuni topilmadi.")
        return None
    except Exception as e:
        st.error(f"Ma'lumot o'qishda xatolik: {e}")
        return None

def check_already_finished(name, subject):
    try:
        df = conn.read(worksheet="Results", ttl=0)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            exists = df[(df['Ism-familiya'].astype(str) == str(name)) & (df['Fan'].astype(str) == str(subject))]
            return len(exists) > 0
    except: return False
    return False

def background_tasks(name, subject, corrects, total, ball):
    # Google Sheets'ga yozish (gspread + google-auth orqali)
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # google-auth yordamida autentifikatsiya
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Jadvalga ulanish
        sheet = client.open_by_key("1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U").worksheet("Results")
        
        row = [datetime.now().strftime("%Y-%m-%d %H:%M"), str(name), str(subject), int(corrects), int(total - corrects), f"{ball}%"]
        sheet.append_row(row)
    except Exception as e:
        st.error(f"Google Sheets yozish xatosi: {e}")

    # Telegram xabarnomasi
    try:
        text = f"🏆 YANGI NATIJA!\n👤: {name}\n📚: {subject}\n✅: {corrects}\n❌: {total-corrects}\n📊: {ball}%"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except: 
        pass

def apply_styles(subject="Default"):
    bg_images = {
        "Matematika": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2000",
        "Fizika": "https://images.unsplash.com/photo-1636466484292-78351adcb72e?q=80&w=2000",
        "Informatika": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2000",
        "Default": "https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000"
    }
    bg_url = bg_images.get(subject, bg_images["Default"])
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{bg_url}") no-repeat center center fixed !important; background-size: cover !important; font-family: 'Inter', sans-serif; }}
    .main-card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 20px; }}
    .analysis-card {{ background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid; }}
    div.stButton > button {{ width: 100%; background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; color: #001f3f !important; font-size: 20px !important; font-weight: 800 !important; border-radius: 15px !important; border: none !important; padding: 18px !important; text-transform: uppercase; }}
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

def show_html_timer():
    if st.session_state.get('page') == "TEST" and 'start_time' in st.session_state:
        st_autorefresh(interval=1000, key="timer_refresh")
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, int(st.session_state.total_time - elapsed))
        
        st.sidebar.markdown(f"""
        <div style="background: rgba(0,201,255,0.1); padding:15px; border-radius:15px; border: 2px solid #00C9FF; text-align:center; margin-bottom: 20px;">
            <h1 style="color:#00C9FF; margin:0; font-size:40px; font-family:sans-serif;">{remaining//60:02d}:{remaining%60:02d}</h1>
            <p style="color:white; margin:0; font-weight:bold; font-size:12px;">VAQT QOLDI</p>
        </div>
        """, unsafe_allow_html=True)
        
        if remaining <= 0:
            st.session_state.page = "HOME"
            st.rerun()

# --- 5. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "HOME"
if 'user_logs' not in st.session_state: st.session_state.user_logs = []

# --- 7. SAHIFALAR ---
if st.session_state.page == "RESULT":
    apply_styles()
    res = st.session_state.final_score
    st.markdown(f'<div class="main-card" style="text-align:center;"><h1 style="color:#92FE9D; font-size:100px; margin:0;">{res["ball"]}%</h1><h2>{res["name"]}</h2></div>', unsafe_allow_html=True)
    with st.expander("🔍 Batafsil tahlil"):
        for log in st.session_state.user_logs:
            border_color = "#92FE9D" if log['correct'] else "#FF4B4B"
            correct_ans_info = "" if log['correct'] else f"<p style='color:#92FE9D;'><b>To'g'ri javob:</b> {log['correct_ans']}</p>"
            
            st.markdown(f'''
            <div class="analysis-card" style="border-left-color: {border_color};">
                <p><b>Savol:</b> {log["question"]}</p>
                <p>Sizning javobingiz: {log["user_ans"]}</p>
                {correct_ans_info}
            </div>
            ''', unsafe_allow_html=True)
    if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"):
        st.session_state.page = "HOME"; st.rerun()

elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    show_html_timer()
    st.markdown(f"### 📚 Fan: {st.session_state.selected_subject}")
    with st.form(key="quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"**{i+1}. {item['q']}**")
            if item.get('image') and str(item['image']) != 'nan':
                st.image(item['image'])
            user_answers[i] = st.radio("Tanlang:", item['o'], index=None, key=f"q_{i}")
            st.markdown("---")
        if st.form_submit_button("🏁 TESTNI TUGATISH"):
            if None in user_answers.values():
                st.error("⚠️ Barcha savollarni belgilang!")
            else:
                logs = []
                corrects = 0
                for i, item in enumerate(st.session_state.test_items):
                    c_ans = item['map'].get(str(item['c']).strip().upper(), item['c'])
                    is_correct = str(user_answers[i]).lower() == str(c_ans).lower()
                    if is_correct: corrects += 1
                    logs.append({
                        "question": item['q'], 
                        "user_ans": user_answers[i], 
                        "correct": is_correct,
                        "correct_ans": c_ans
                    })
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                st.session_state.update({"user_logs": logs, "final_score": {"name": st.session_state.full_name, "ball": ball}, "page": "RESULT"})
                background_tasks(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                st.rerun()

elif st.session_state.page == "HOME":
    apply_styles()
    st.markdown("<h1 style='text-align:center;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
    u_name = st.text_input("Ism-familiyangiz:", key="user_name_input")
    q_df = load_questions()
    if q_df is not None and not q_df.empty:
        all_subs = sorted(q_df['Fan'].dropna().unique().tolist())
        selected_subject = st.selectbox("Fanni tanlang:", all_subs)
        if st.button("🚀 TESTNI BOSHLASH"):
            if not u_name: st.error("⚠️ Ism-familiyangizni yozing!")
            elif check_already_finished(u_name, selected_subject): st.error("❌ Siz topshirib bo'lgansiz!")
            else:
                sub_qs = q_df[q_df['Fan'] == selected_subject]
                sample_size = min(len(sub_qs), 30)
                sampled_qs = sub_qs.sample(n=sample_size)
                test_items = []
                for _, row in sampled_qs.iterrows():
                    mapping = {'A': str(row.get('A','')), 'B': str(row.get('B','')), 'C': str(row.get('C','')), 'D': str(row.get('D',''))}
                    opts = [v for v in mapping.values() if v not in ['nan', '']]
                    random.shuffle(opts)
                    test_items.append({"q": row['Savol'], "o": opts, "c": row['Javob'], "map": mapping, "image": row.get('Rasm')})
                st.session_state.update({"full_name": u_name, "selected_subject": selected_subject, "test_items": test_items, "total_time": len(test_items) * 45, "start_time": time.time(), "page": "TEST"})
                st.rerun()
