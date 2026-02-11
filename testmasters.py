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

# --- FONLAR RO'YXATI ---
bg_styles = {
    "Matematika": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2000",
    "Fizika": "https://images.unsplash.com/photo-1636466484292-78351adcb72e?q=80&w=2000",
    "Informatika": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2000",
    "Tarix": "https://images.unsplash.com/photo-1461360226052-7236aadb12c1?q=80&w=2000",
    "Ona-tili": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?q=80&w=2000",
    "Kimyo": "https://images.unsplash.com/photo-1532187878418-9f1100188665?q=80&w=2000",
    "Biologiya": "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=2000",
    "Ingliz tili": "https://images.unsplash.com/photo-1543167664-c92155e96916?q=80&w=2000",
    "Geografiya": "https://images.unsplash.com/photo-1521295121683-bc014fe1003e?q=80&w=2000",
    "Default": "https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000"
}

def apply_styles(subject):
    bg_url = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
    <style>
    /* ASOSIY FON */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{bg_url}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    
    /* YO'RIQNOMA VA FORMALAR */
    .info-box {{
        background: rgba(0, 0, 0, 0.75);
        padding: 25px; border-radius: 15px;
        border-left: 8px solid #00C9FF; margin-bottom: 25px;
    }}

    div[data-testid="stForm"] {{
        background: rgba(0, 0, 0, 0.8) !important;
        padding: 30px; border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    /* GRADIENT TUGMA */
    button[kind="primaryFormSubmit"], .stButton > button {{
        width: 100% !important; 
        background: linear-gradient(45deg, #00C9FF, #92FE9D) !important;
        color: black !important; font-size: 22px !important; font-weight: bold !important; 
        border-radius: 15px !important; border: none !important;
        box-shadow: 0px 4px 15px rgba(0, 201, 255, 0.4);
        transition: 0.3s;
    }}
    
    /* GRADIENT VAQT BLOKI */
    .timer-card {{
        background: linear-gradient(135deg, rgba(0, 201, 255, 0.9), rgba(146, 254, 157, 0.9));
        padding: 20px; border-radius: 15px; text-align: center;
        color: black !important; font-weight: bold;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.5);
    }}

    .stMarkdown, p, h1, h2, h3, span, label {{ 
        color: white !important; 
        text-shadow: 2px 2px 8px rgba(0,0,0,1); 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNKSIYALAR ---
def send_to_telegram(name, subject, corrects, total, ball):
    text = f"🏆 YANGI NATIJA!\n👤: {name}\n📚: {subject}\n✅: {corrects}\n❌: {total-corrects}\n📊: {ball}%"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except: pass

def save_to_sheets(name, subject, corrects, total, ball):
    try:
        new_data = pd.DataFrame([{"Sana": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ism-familiya": name, "Fan": subject, "To'g'ri javoblar": corrects, "Umumiy savollar": total, "Ball (%)": ball}])
        existing_res = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        updated_res = pd.concat([existing_res, new_data], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_res)
    except: pass

@st.cache_data(ttl=600)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- SESSION STATE ---
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None
if 'completed' not in st.session_state: st.session_state.completed = False

q_df = load_questions()

if q_df is not None:
    available_subjects = q_df['Fan'].dropna().unique().tolist()

    # 1. BOSHLANG'ICH OYNA
    if not st.session_state.test_run and st.session_state.final_score is None:
        apply_styles("Default")
        st.title("🎓 Testmasters Online")
        
        if st.session_state.completed:
            st.error("⚠️ Siz testni topshirib bo'ldingiz. Qayta urinish taqiqlanadi!")
        else:
            st.markdown('<div class="info-box"><h3>📝 Yo\'riqnoma:</h3><ul><li>Ism-familiyani to\'liq yozing.</li><li>Vaqt tugashidan oldin yakunlang.</li></ul></div>', unsafe_allow_html=True)
            u_name = st.text_input("Ism-familiyangiz:", key="main_name")
            selected_subject = st.selectbox("Fanni tanlang:", available_subjects)
            
            if st.button("🚀 TESTNI BOSHLASH") and u_name:
                sub_qs = q_df[q_df['Fan'] == selected_subject].copy()
                selected_qs = sub_qs.sample(n=min(len(sub_qs), 30))
                test_items = []
                for _, row in selected_qs.iterrows():
                    opts = [row['A'], row['B'], row['C'], row['D']]
                    random.shuffle(opts)
                    test_items.append({"q": row['Savol'], "o": opts, "c": row['Javob'], "t": pd.to_numeric(row['Vaqt'], errors='coerce') or 30})
                
                st.session_state.test_items = test_items
                st.session_state.total_time = sum(item['t'] for item in test_items)
                st.session_state.start_time = time.time()
                st.session_state.full_name = u_name
                st.session_state.selected_subject = selected_subject
                st.session_state.test_run = True
                st.rerun()

    # 2. TEST JARAYONI
    elif st.session_state.test_run:
        apply_styles(st.session_state.selected_subject)
        
        # Taymer mantiqi (Yuradigan qilish uchun har 1 soniyada yangilanadi)
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, int(st.session_state.total_time - elapsed))
        
        st.sidebar.markdown(f"""
            <div class="timer-card">
                <h1 style="color:black !important; margin:0;">{rem//60:02d}:{rem%60:02d}</h1>
                <p style="color:black !important; margin:0;">QOLGAN VAQT</p>
            </div>
        """, unsafe_allow_html=True)

        if rem <= 0:
            st.session_state.test_run = False
            st.session_state.completed = True
            st.rerun()

        st.markdown(f"### 👤 {st.session_state.full_name} | 📚 {st.session_state.selected_subject}")
        
        with st.form("quiz_form"):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.write(f"**{i+1}. {item['q']}**")
                user_answers[i] = st.radio("Javobingiz:", item['o'], index=None, key=f"q_{i}")
            
            if st.form_submit_button("🏁 TESTNI YAKUNLASH"):
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                
                st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball, "score": corrects, "total": len(st.session_state.test_items)}
                st.session_state.test_run = False
                st.session_state.completed = True
                st.rerun()
        
        # Vaqt yurishi uchun (avtomatik yangilanish)
        time.sleep(1)
        st.rerun()

    # 3. NATIJA OYNASI
    elif st.session_state.final_score:
        apply_styles("Default")
        res = st.session_state.final_score
        st.balloons()
        st.markdown(f"""
            <div style="background:rgba(0,0,0,0.8); padding:40px; border-radius:25px; text-align:center; border:3px solid #92FE9D;">
                <h1 style="color:#92FE9D; font-size:70px;">{res['ball']}%</h1>
                <h2>{res['name']}</h2>
                <p>Natijangiz saqlandi. Tizimdan chiqishingiz mumkin.</p>
            </div>
        """, unsafe_allow_html=True)
