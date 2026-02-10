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

# --- FONLAR LUG'ATI ---
bg_styles = {
    "Kimyo": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1603126731702-5094e430ba31?auto=format&fit=crop&w=1600&q=80')",
    "Biologiya": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1530026405186-ed1f139313f8?auto=format&fit=crop&w=1600&q=80')",
    "Ingliz tili": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1543167664-c92155e96916?auto=format&fit=crop&w=1600&q=80')",
    "Geografiya": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1521295121683-bc014fe1003e?auto=format&fit=crop&w=1600&q=80')",
    "Huquq": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1600&q=80')",
    "Rus tili": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?auto=format&fit=crop&w=1600&q=80')",
    "Fizika": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1636466483764-15252f7c016f?auto=format&fit=crop&w=1600&q=80')",
    "Matematika": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1509228468518-180dd482180c?auto=format&fit=crop&w=1600&q=80')",
    "Default": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)"
}

def set_background(subject):
    bg = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""<style>.stApp {{ background: {bg}; background-size: cover; background-attachment: fixed; }}
    .stMarkdown, p, h1, h2, h3, span {{ color: white !important; }}
    div[data-testid="stForm"] {{ background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(15px); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2); }}
    </style>""", unsafe_allow_html=True)

# --- MA'LUMOTLARNI YUKLASH ---
@st.cache_data(ttl=600)
def load_questions_cached():
    return conn.read(spreadsheet=SHEET_URL, worksheet="Questions")

def check_user_fresh(name):
    u = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
    existing = [str(n).strip().lower() for n in u['Ism'].tolist()]
    return name.lower() in existing, u

# SESSION STATE INIZIALIZATSIYA
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None
if 'user_checked' not in st.session_state: st.session_state.user_checked = False

q_df = load_questions_cached()
available_subjects = q_df['Fan'].unique().tolist()

st.title("🚀 Testmasters Online")

# --- LOGIN QISMI ---
if not st.session_state.test_run and st.session_state.final_score is None:
    u_name_raw = st.text_input("Ism-familiyangizni kiriting:").strip()
    if u_name_raw:
        if not st.session_state.user_checked or st.session_state.current_user != u_name_raw.lower():
            is_blocked, u_df = check_user_fresh(u_name_raw)
            st.session_state.is_blocked = is_blocked
            st.session_state.u_df = u_df
            st.session_state.user_checked = True
            st.session_state.current_user = u_name_raw.lower()
            st.session_state.full_name = u_name_raw

        if st.session_state.is_blocked:
            st.error(f"🛑 {u_name_raw}, siz avval test topshirgansiz!")
        else:
            selected_subject = st.selectbox("Fanni tanlang:", available_subjects)
            set_background(selected_subject)
            if st.button(f"🚀 {selected_subject} fanidan boshlash"):
                sub_qs = q_df[q_df['Fan'] == selected_subject]
                st.session_state.questions = sub_qs.sample(n=min(len(sub_qs), 30))
                st.session_state.total_time = int(st.session_state.questions['Vaqt'].sum())
                st.session_state.start_time = time.time()
                st.session_state.selected_subject = selected_subject
                st.session_state.test_run = True
                st.rerun()

# --- TEST JARAYONI ---
if st.session_state.test_run:
    set_background(st.session_state.selected_subject)
    st.subheader(f"Fan: {st.session_state.selected_subject} | O'quvchi: {st.session_state.full_name}")
    
    rem = max(0, st.session_state.total_time - int(time.time() - st.session_state.start_time))
    st.sidebar.markdown(f"# ⏳ Vaqt: {rem//60:02d}:{rem%60:02d}")
    
    if rem <= 0:
        st.session_state.test_run = False
        st.warning("Vaqt tugadi!")
        st.rerun()
    
    with st.form("quiz_form"):
        u_ans = {}
        for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
            st.write(f"**{i+1}. {row['Savol']}**")
            u_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
        
        if st.form_submit_button("🏁 Yakunlash"):
            corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
            total = len(st.session_state.questions)
            final_ball = round((corrects / total) * 100, 1)
            
            # Google Sheets yangilash
            new_entry = pd.DataFrame([{"Ism": st.session_state.full_name, "Fan": st.session_state.selected_subject, "Natija": f"{corrects}/{total}", "Ball": final_ball}])
            updated_u_df = pd.concat([st.session_state.u_df, new_entry], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_u_df, worksheet="Sheet1")
            
            # Telegramga yuborish
            msg = f"🏆 *NATIJA*: {st.session_state.full_name}\n📚 *Fan*: {st.session_state.selected_subject}\n✅ *To'g'ri*: {corrects}/{total}\n📊 *Ball*: {final_ball}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

            st.session_state.final_score = {"score": corrects, "total": total, "ball": final_ball}
            st.session_state.test_run = False
            st.rerun()
    
    time.sleep(1)
    st.rerun()

# --- NATIJA EKRANI ---
if st.session_state.final_score is not None:
    set_background("Default")
    st.balloons()
    res = st.session_state.final_score
    st.success(f"### 🎉 Test yakunlandi!\n**O'quvchi:** {st.session_state.full_name}\n**To'g'ri javoblar:** {res['score']} ta\n**Umumiy ball:** {res['ball']} ball")
    if st.button("Qayta boshlash"):
        st.session_state.final_score = None
        st.session_state.user_checked = False
        st.rerun()
    st.link_button("🏆 Kanalga o'tish", "https://t.me/Testmasters_LC", use_container_width=True)
