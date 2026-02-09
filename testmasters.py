import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="📚")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmaster_LC" 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def send_to_telegram(name, score, total, percent, subject):
    msg = (f"📊 *YANGI NATIJA*\n👤 {name}\n📚 *Fan:* {subject}\n✅ {score}/{total} ({percent:.1f}%)")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- MUHIM O'ZGARIŞ: Ma'lumotlarni kesh bilan yuklash (10 daqiqa davomida qayta so'ramaydi) ---
@st.cache_data(ttl=600)
def load_data_cached():
    q = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    u = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    return q, u

# Bloklash uchun Users jadvalini har safar yangi o'qish (faqat ism kiritilganda bir marta)
def check_user_fresh():
    u = conn.read(spreadsheet=SHEET_URL, worksheet="Users", ttl=0)
    return [str(name).strip().lower() for name in u['Ism'].tolist()]

try:
    q_df, _ = load_data_cached()
    available_subjects = q_df['Fan'].unique().tolist()
except Exception as e:
    st.error("Google Sheets kvotasi tugagan. 1 daqiqa kuting...")
    st.stop()

# SESSION STATE
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

st.title("🚀 Testmasters Online Testlar Markazi")

u_name_raw = st.text_input("Ism-familiyangizni kiriting:").strip()

if u_name_raw:
    # Faqat ism kiritilganda Users ro'yxatini tekshiramiz
    if 'user_checked' not in st.session_state:
        existing_users = check_user_fresh()
        if u_name_raw.lower() in existing_users:
            st.session_state.blocked = True
        else:
            st.session_state.blocked = False
        st.session_state.user_checked = True

    if st.session_state.get('blocked', False):
        st.error(f"🛑 {u_name_raw}, siz avval test topshirgansiz!")
    else:
        selected_subject = st.selectbox("Test topshirmoqchi bo'lgan fanni tanlang:", available_subjects)

        if not st.session_state.test_run and st.session_state.final_score is None:
            if st.button(f"🚀 {selected_subject} fanidan testni boshlash"):
                sub_qs = q_df[q_df['Fan'] == selected_subject]
                st.session_state.questions = sub_qs.sample(n=min(len(sub_qs), 30))
                st.session_state.total_time = int(st.session_state.questions['Vaqt'].sum())
                st.session_state.start_time = time.time()
                st.session_state.selected_subject = selected_subject
                st.session_state.test_run = True
                st.rerun()

        if st.session_state.test_run:
            timer_place = st.sidebar.empty()
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.total_time - int(elapsed))
            m, s = divmod(remaining, 60)
            timer_place.markdown(f"## ⏳ Fan: {st.session_state.selected_subject}\n### Vaqt: {m:02d}:{s:02d}")
            
            if remaining <= 0:
                st.session_state.test_run = False
                st.rerun()
            
            with st.form("quiz_form"):
                u_ans = {}
                for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                    st.write(f"**{i+1}. {row['Savol']}**")
                    u_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
                
                if st.form_submit_button("🏁 Yakunlash"):
                    corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                    total = len(st.session_state.questions)
                    percent = (corrects / total) * 100
                    
                    # Natijani bazaga yozish
                    _, u_df_old = load_data_cached()
                    new_user = pd.concat([u_df_old, pd.DataFrame([{"Ism": u_name_raw}])], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=new_user, worksheet="Users")
                    
                    send_to_telegram(u_name_raw, corrects, total, percent, st.session_state.selected_subject)
                    st.session_state.final_score = corrects
                    st.session_state.test_run = False
                    st.rerun()
            
            time.sleep(1)
            st.rerun()

if st.session_state.final_score is not None:
    st.success(f"### Natijangiz: {st.session_state.final_score}")
    st.link_button("🔗 Kanalga o'tish", "https://t.me/Testmasters_LC")
