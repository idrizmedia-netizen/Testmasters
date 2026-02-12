import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
import random
from datetime import datetime

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmasters_LC" 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- DIZAYN VA STIL ---
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
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{bg_url}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    /* Tugmalar dizayni */
    div.stButton > button {{
        width: 100%;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: black !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 15px !important;
        transition: 0.3s ease all;
        box-shadow: 0 4px 15px rgba(0, 201, 255, 0.4);
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 201, 255, 0.6);
    }}
    /* Savollar qutisi */
    .question-card {{
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 10px;
    }}
    .timer-card {{
        background: rgba(0, 0, 0, 0.6);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #00C9FF;
    }}
    .stMarkdown, p, h1, h2, h3, label {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNKSIYALAR ---
@st.cache_data(ttl=600)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

def check_already_finished(name, subject):
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        exists = df[(df['Ism-familiya'].str.strip().str.lower() == name.strip().lower()) & 
                    (df['Fan'].str.strip().str.lower() == subject.strip().lower())]
        return not exists.empty
    except: return False

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "HOME"

# --- ASOSIY EKRAN BOSHQARUVI ---
main_container = st.empty() # Hamma narsani tozalash uchun konteyner

# 1. NATIJA EKRANI
if st.session_state.page == "RESULT":
    with main_container.container():
        apply_styles()
        res = st.session_state.final_score
        st.balloons()
        st.markdown(f"""
            <div style="background:rgba(0,0,0,0.8); padding:50px; border-radius:30px; text-align:center; border:2px solid #92FE9D;">
                <h1 style="color:#92FE9D; font-size:80px;">{res['ball']}%</h1>
                <h2>{res['name']}</h2>
                <p>Natijangiz muvaffaqiyatli saqlandi!</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"):
            st.session_state.page = "HOME"
            st.rerun()

# 2. TEST TOPSHIRISH EKRANI
elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    
    with main_container.container():
        # Taymer hisobi
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, int(st.session_state.total_time - elapsed))
        
        # Sidebar (Faqat test paytida chiqadi)
        st.sidebar.markdown(f'<div class="timer-card"><h1 style="color:#00C9FF; margin:0;">{rem//60:02d}:{rem%60:02d}</h1><small>VAQT QOLDI</small></div>', unsafe_allow_html=True)
        st.sidebar.write(f"👤 **{st.session_state.full_name}**")
        st.sidebar.write(f"📚 **{st.session_state.selected_subject}**")

        if rem <= 0:
            st.error("⌛ Vaqt tugadi!")
            st.session_state.page = "RESULT"
            st.rerun()

        with st.form("quiz_form", clear_on_submit=True):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.markdown(f"**{i+1}. {item['q']}**")
                user_answers[i] = st.radio("Javob:", item['o'], index=None, key=f"q_{i}", label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("🏁 TESTNI TUGATISH")
            
            if submit:
                if None in user_answers.values():
                    st.error("⚠️ Iltimos, barcha savollarni belgilang!")
                else:
                    corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                    ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                    
                    # Saqlash mantiqi...
                    st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball}
                    st.session_state.page = "RESULT"
                    st.rerun()
        
        time.sleep(1)
        st.rerun()

# 3. KIRISH EKRANI (FAQAT BOSHIDA KO'RINADI)
elif st.session_state.page == "HOME":
    apply_styles()
    with main_container.container():
        st.markdown("<h1 style='text-align:center;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
        
        st.markdown('''<div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:15px; border-left:5px solid #00C9FF;">
            <h3 style="margin-top:0;">📝 Yo'riqnoma:</h3>
            <p>1. Ismingizni kiriting va fanni tanlang.<br>
            2. "Testni boshlash" tugmasini bosing.<br>
            3. Test boshlanganda bu yo'riqnoma yashiriladi.</p>
        </div>''', unsafe_allow_html=True)
        
        st.write("")
        u_name = st.text_input("Ism-familiyangiz:", placeholder="Masalan: Ali Valiyev")
        
        q_df = load_questions()
        if q_df is not None:
            all_subs = sorted(q_df['Fan'].dropna().unique().tolist())
            selected_subject = st.selectbox("Fanni tanlang:", all_subs)

            if st.button("🚀 TESTNI BOSHLASH"):
                if not u_name:
                    st.error("⚠️ Iltimos, ism-familiyangizni yozing!")
                elif check_already_finished(u_name, selected_subject):
                    st.warning("⚠️ Siz bu fandan test topshirib bo'lgansiz!")
                else:
                    # Savollarni tayyorlash
                    sub_qs = q_df[q_df['Fan'] == selected_subject].copy()
                    selected_qs = sub_qs.sample(n=min(len(sub_qs), 30))
                    
                    test_items = []
                    for _, row in selected_qs.iterrows():
                        opts = [str(row['A']), str(row['B']), str(row['C']), str(row['D'])]
                        random.shuffle(opts)
                        test_items.append({"q": row['Savol'], "o": opts, "c": str(row['Javob']), "t": 30})
                    
                    # Holatni o'zgartirish
                    st.session_state.full_name = u_name
                    st.session_state.selected_subject = selected_subject
                    st.session_state.test_items = test_items
                    st.session_state.total_time = len(test_items) * 30
                    st.session_state.start_time = time.time()
                    st.session_state.page = "TEST"
                    st.rerun()
