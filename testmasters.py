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
WIN_IMAGE = "https://img.freepik.com/free-vector/winner-background-first-place-victory-concept_52683-45814.jpg"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONLAR ---
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
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{bg_url}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    .info-box {{
        background: rgba(255, 255, 255, 0.1);
        padding: 20px; border-radius: 15px; backdrop-filter: blur(10px);
        border-left: 5px solid #00C9FF; margin-bottom: 20px;
    }}
    div[data-testid="stFormSubmitButton"] button, .stButton > button {{
        width: 100% !important;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: black !important; font-size: 20px !important; font-weight: bold !important;
        border-radius: 12px !important; border: none !important; padding: 12px !important;
        box-shadow: 0 4px 15px rgba(0,201,255,0.4);
    }}
    .timer-card {{
        background: linear-gradient(135deg, #00C9FF, #92FE9D);
        padding: 15px; border-radius: 12px; text-align: center; color: black !important;
        font-weight: bold; margin-bottom: 20px;
    }}
    .stRadio > label {{ color: white !important; font-size: 18px !important; }}
    .stMarkdown, p, h1, h2, h3, label {{ color: white !important; }}
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
        existing_res = conn.read(spreadsheet=SHEET_URL, worksheet="Results", ttl=0)
        updated_res = pd.concat([existing_res, new_data], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_res)
    except: pass

@st.cache_data(ttl=600)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=600)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- REYTING VA O'YIN FUNKSIYALARI ---
def show_leaderboard():
    st.markdown("## 🏆 Top 10 Reyting")
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Results", ttl=0)
        if df is not None and not df.empty:
            df['Ball (%)'] = pd.to_numeric(df['Ball (%)'], errors='coerce')
            top_10 = df.nlargest(10, 'Ball (%)')[['Ism-familiya', 'Fan', 'Ball (%)']]
            st.table(top_10.reset_index(drop=True))
        else: st.info("Hozircha natijalar mavjud emas.")
    except: st.error("Reytingni yuklashda xato.")

def spin_the_wheel(subjects):
    st.markdown("## 🎡 Omad G'ildiragi")
    if st.button("G'ildirakni aylantirish 🌀"):
        placeholder = st.empty()
        for i in range(10):
            temp = random.choice(subjects)
            placeholder.markdown(f"<h1 style='text-align:center;'>{temp}</h1>", unsafe_allow_html=True)
            time.sleep(0.1)
        final = random.choice(subjects)
        placeholder.markdown(f"<div style='background:#92FE9D; padding:20px; border-radius:15px; text-align:center;'><h1 style='color:black;'>{final}</h1></div>", unsafe_allow_html=True)
        st.success(f"Sizga tushgan fan: {final}")

def team_tug_of_war(q_df, subject):
    st.markdown(f"## ⚔️ Jamoaviy Arqon Tortish: {subject}")
    if 'tug_score' not in st.session_state:
        st.session_state.tug_score = 50
        sub_qs = q_df[q_df['Fan'] == subject]
        st.session_state.current_q = sub_qs.sample(1).iloc[0]

    st.progress(st.session_state.tug_score / 100)
    col1, _, col3 = st.columns([1,2,1])
    col1.write("🤖 Robotlar")
    col3.write("👨‍👩‍👧‍👦 Sizning Jamoa")

    q = st.session_state.current_q
    st.write(f"### Savol: {q['Savol']}")
    ans = st.text_input("Javobingiz:")
    
    if st.button("TORTISH! 💪"):
        if ans.lower().strip() == str(q['Javob']).lower().strip():
            st.session_state.tug_score = min(100, st.session_state.tug_score + 20)
            st.success("To'g'ri! Oldinga intilamiz!")
        else:
            st.session_state.tug_score = max(0, st.session_state.tug_score - 20)
            st.error("Xato! Robot tortib ketdi.")
        
        if st.session_state.tug_score >= 100:
            st.image(WIN_IMAGE)
            st.balloons()
            del st.session_state.tug_score
        elif st.session_state.tug_score <= 0:
            st.error("Robotlar yutdi!")
            del st.session_state.tug_score
        else:
            st.session_state.current_q = q_df[q_df['Fan'] == subject].sample(1).iloc[0]
            st.rerun()

# --- ASOSIY MANTIQ ---
q_df = load_questions()

# SIDEBAR MENYU
apply_styles("Default")
st.sidebar.title("💎 Testmasters Menyu")
menu = st.sidebar.selectbox("Bo'limni tanlang:", ["Bosh sahifa", "Yakka Test 📝", "Jamoaviy Arqon ⚔️", "Omad G'ildiragi 🎡", "Reyting 🏆"])

if menu == "Bosh sahifa":
    st.title("🎓 Testmasters Online")
    st.image("https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000")
    st.markdown('<div class="info-box">O\'zingizga kerakli bo\'limni yon menyudan tanlang!</div>', unsafe_allow_html=True)

elif menu == "Yakka Test 📝":
    if st.session_state.get('test_run'):
        # TEST KODINGIZ (O'zgartirishsiz)
        apply_styles(st.session_state.selected_subject)
        rem = max(0, int(st.session_state.total_time - (time.time() - st.session_state.start_time)))
        st.sidebar.markdown(f'<div class="timer-card"><h2>{rem//60:02d}:{rem%60:02d}</h2></div>', unsafe_allow_html=True)
        
        if rem <= 0:
            st.session_state.test_run = False
            st.rerun()

        with st.form("quiz"):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.markdown(f"**{i+1}. {item['q']}**")
                user_answers[i] = st.radio(f"ans_{i}", item['o'], index=None, label_visibility="collapsed")
            if st.form_submit_button("🏁 YAKUNLASH"):
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball}
                st.session_state.test_run = False
                st.rerun()
    elif st.session_state.get('final_score'):
        st.balloons()
        st.success(f"Natija: {st.session_state.final_score['ball']}%")
        if st.button("Qaytish"): 
            st.session_state.final_score = None
            st.rerun()
    else:
        u_name = st.text_input("Ism-familiya:")
        all_subs = q_df['Fan'].dropna().unique().tolist()
        sub = st.selectbox("Fan:", all_subs)
        if st.button("🚀 BOSHLASH") and u_name:
            sub_qs = q_df[q_df['Fan'] == sub].sample(n=min(len(q_df[q_df['Fan']==sub]), 20))
            items = []
            for _, r in sub_qs.iterrows():
                opts = [str(r['A']), str(r['B']), str(r['C']), str(r['D'])]
                random.shuffle(opts)
                items.append({"q": r['Savol'], "o": opts, "c": str(r['Javob']), "t": 30})
            st.session_state.test_items = items
            st.session_state.total_time = len(items) * 30
            st.session_state.start_time = time.time()
            st.session_state.full_name = u_name
            st.session_state.selected_subject = sub
            st.session_state.test_run = True
            st.rerun()

elif menu == "Jamoaviy Arqon ⚔️":
    sub = st.selectbox("Fan tanlang:", q_df['Fan'].unique())
    team_tug_of_war(q_df, sub)

elif menu == "Omad G'ildiragi 🎡":
    spin_the_wheel(q_df['Fan'].unique())

elif menu == "Reyting 🏆":
    show_leaderboard()
