import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmaster_LC" 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FANGA MOS FONLAR LUG'ATI ---
bg_styles = {
    "Fizika": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://img.freepik.com/free-vector/physics-formulas-science-concept_23-2148493175.jpg')",
    "Matematika": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://img.freepik.com/free-vector/mathematical-formulas-chalkboard_23-2148154143.jpg')",
    "Ona tili": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://img.freepik.com/free-vector/vintage-paper-background_23-2148286576.jpg')",
    "Tarix": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://img.freepik.com/free-photo/old-map-background_23-2148834015.jpg')",
    "Default": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
}

def set_background(subject):
    bg = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
        <style>
        .stApp {{
            background: {bg};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: white;
        }}
        .stMarkdown, p, h1, h2, h3, span {{ color: white !important; }}
        div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        </style>
    """, unsafe_allow_html=True)

# --- MA'LUMOTLARNI YUKLASH ---
@st.cache_data(ttl=600)
def load_questions_cached():
    return conn.read(spreadsheet=SHEET_URL, worksheet="Questions")

def check_user_fresh(name):
    u = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
    existing = [str(n).strip().lower() for n in u['Ism'].tolist()]
    return name.lower() in existing, u

try:
    q_df = load_questions_cached()
    available_subjects = q_df['Fan'].unique().tolist()
except:
    st.error("Google Sheets limitiga urildingiz. Biroz kuting.")
    st.stop()

# SESSION STATE
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

# --- ASOSIY INTERFEYS ---
st.title("🚀 Testmasters Online Testlar Markazi")

u_name_raw = st.text_input("Ism-familiyangizni kiriting:").strip()

if u_name_raw:
    if 'user_checked' not in st.session_state:
        is_blocked, u_df = check_user_fresh(u_name_raw)
        st.session_state.is_blocked, st.session_state.u_df, st.session_state.user_checked = is_blocked, u_df, True

    if st.session_state.is_blocked:
        st.error(f"🛑 {u_name_raw}, siz avval test topshirgansiz!")
    else:
        selected_subject = st.selectbox("Fanni tanlang:", available_subjects)
        
        # FONNI O'RNATISH
        if not st.session_state.test_run:
            set_background(selected_subject)

        if not st.session_state.test_run and st.session_state.final_score is None:
            if st.button(f"🚀 {selected_subject} fanidan boshlash"):
                sub_qs = q_df[q_df['Fan'] == selected_subject]
                st.session_state.questions = sub_qs.sample(n=min(len(sub_qs), 30))
                st.session_state.total_time = int(st.session_state.questions['Vaqt'].sum())
                st.session_state.start_time = time.time()
                st.session_state.selected_subject = selected_subject
                st.session_state.test_run = True
                st.rerun()

        if st.session_state.test_run:
            set_background(st.session_state.selected_subject)
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.total_time - int(elapsed))
            m, s = divmod(remaining, 60)
            
            st.sidebar.markdown(f"## ⏳ Vaqt: {m:02d}:{s:02d}")
            
            if remaining <= 0:
                st.session_state.test_run = False
                st.rerun()
            
            with st.form("quiz_form"):
                u_ans = {}
                for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                    st.write(f"### {i+1}. {row['Savol']}")
                    u_ans[idx] = st.radio("Javobingiz:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Yakunlash"):
                    corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    total = len(st.session_state.questions)
                    percent = (corrects / total) * 100
                    
                    # Google Sheets yangilash
                    new_entry = pd.DataFrame([{"Ism": u_name_raw, "Natija": f"{corrects}/{total}", "Fan": st.session_state.selected_subject}])
                    updated_u_df = pd.concat([st.session_state.u_df, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_u_df, worksheet="Sheet1")
                    
                    # Telegramga yuborish
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    msg = f"🏆 *NATIJA*: {u_name_raw}\n📚 *Fan*: {st.session_state.selected_subject}\n✅ {corrects}/{total}"
                    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

                    st.session_state.final_score = {"score": corrects, "total": total}
                    st.session_state.test_run = False
                    st.rerun()
            
            time.sleep(2)
            st.rerun()

# NATIJA EKRANI
if st.session_state.final_score is not None:
    set_background("Default")
    st.balloons()
    st.success(f"### 🎉 Natijangiz: {st.session_state.final_score['score']} / {st.session_state.final_score['total']}")
    st.link_button("🏆 Kanalga o'tish", "https://t.me/Testmasters_LC", use_container_width=True)
