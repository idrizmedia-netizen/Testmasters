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

# --- FONLARNING ANIQ RO'YXATI ---
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
        background: url("{bg_url}");
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    /* BLUR VA OQARISHNI YO'QOTISH */
    .stApp > header {{ background: transparent !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    
    .stMarkdown, p, h1, h2, h3, span, label {{ 
        color: white !important; 
        text-shadow: 2px 2px 10px rgba(0,0,0,1) !important; 
    }}
    .info-box {{
        background: rgba(0, 0, 0, 0.7);
        padding: 20px; border-radius: 15px;
        border-left: 6px solid #92FE9D; margin-bottom: 20px;
    }}
    button[kind="primaryFormSubmit"], .stButton > button {{
        width: 100% !important; 
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: black !important; font-size: 20px !important; font-weight: bold !important; 
        border-radius: 10px !important; border: none !important; padding: 10px !important;
    }}
    div[data-testid="stForm"] {{
        background: rgba(0, 0, 0, 0.8) !important;
        padding: 30px; border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNKSIYALAR ---
def send_to_telegram(name, subject, corrects, total, ball):
    text = f"🏆 YANGI NATIJA!\n\n👤 O'quvchi: {name}\n📚 Fan: {subject}\n✅ To'g'ri: {corrects}\n❌ Xato: {total-corrects}\n📊 Ball: {ball}%\n🤖 @Testmasters1_bot"
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
    
    # 1. BOSHLANG'ICH OYNA (faqat test boshlanmagan bo'lsa ko'rinadi)
    if not st.session_state.test_run and st.session_state.final_score is None:
        apply_styles("Default")
        st.title("🎓 Testmasters Online")
        
        if st.session_state.completed:
            st.warning("⚠️ Siz testni topshirib bo'ldingiz.")
        else:
            st.markdown('<div class="info-box"><h3>📝 Yo\'riqnoma:</h3><ul><li>Ismingizni kiriting va fanni tanlang.</li><li>"Boshlash" tugmasini bosgach test yuklanadi.</li></ul></div>', unsafe_allow_html=True)
            u_name = st.text_input("Ism-familiyangiz:", placeholder="Masalan: Ali Valiyev")
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

    # 2. TEST JARAYONI (bu yerda ism/fan tanlash oynasi butunlay yo'qoladi)
    elif st.session_state.test_run:
        apply_styles(st.session_state.selected_subject)
        st.markdown(f"### 👤 O'quvchi: {st.session_state.full_name}")
        
        rem = max(0, int(st.session_state.total_time - (time.time() - st.session_state.start_time)))
        st.sidebar.markdown(f'<div style="text-align:center;padding:15px;background:black;border-radius:10px;border:2px solid #92FE9D;"><h2 style="color:#92FE9D;margin:0;">⏳ {rem//60:02d}:{rem%60:02d}</h2></div>', unsafe_allow_html=True)
        
        if rem <= 0:
            st.session_state.test_run = False
            st.session_state.completed = True
            st.rerun()

        with st.form("quiz_form"):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.write(f"**{i+1}. {item['q']}**")
                user_answers[i] = st.radio("Javob:", item['o'], index=None, key=f"q_{i}")
            
            if st.form_submit_button("🏁 TESTNI YAKUNLASH"):
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                
                st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball, "score": corrects, "total": len(st.session_state.test_items)}
                st.session_state.test_run = False
                st.session_state.completed = True
                st.rerun()
        
        time.sleep(1)
        st.rerun()

    # 3. NATIJA OYNASI
    elif st.session_state.final_score:
        apply_styles("Default")
        res = st.session_state.final_score
        st.balloons()
        st.markdown(f'<div style="background:rgba(0,0,0,0.8);padding:40px;border-radius:20px;text-align:center;border:2px solid #92FE9D;"><h2>🎉 Natija: {res["name"]}</h2><h1 style="color:#92FE9D;font-size:60px;">{res["ball"]}%</h1><p>To\'g\'ri javoblar: {res["score"]} / {res["total"]}</p></div>', unsafe_allow_html=True)
