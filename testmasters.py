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

# --- STYLES ---
def apply_styles(subject="Default"):
    bg_styles = {
        "Matematika": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2000",
        "Fizika": "https://images.unsplash.com/photo-1636466484292-78351adcb72e?q=80&w=2000",
        "Default": "https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000"
    }
    bg_url = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{bg_url}") no-repeat center center fixed !important; background-size: cover !important; }}
    .info-box {{ background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 20px; backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }}
    .timer-card {{ background: linear-gradient(135deg, #FF4B4B, #FF9068); padding: 20px; border-radius: 15px; text-align: center; color: white !important; font-size: 24px; font-weight: bold; box-shadow: 0 10px 20px rgba(255,75,75,0.3); }}
    .spin-text {{ font-size: 40px; font-weight: bold; text-align: center; color: #00C9FF; text-shadow: 2px 2px 10px rgba(0,201,255,0.5); }}
    div[data-testid="stFormSubmitButton"] button, .stButton > button {{ width: 100% !important; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important; color: black !important; font-weight: bold !important; border-radius: 12px !important; border: none !important; padding: 15px !important; }}
    .stMarkdown, p, h1, h2, h3, label {{ color: white !important; font-family: 'Segoe UI', sans-serif; }}
    </style>
    """, unsafe_allow_html=True)

# --- HELPERS ---
def send_to_telegram(name, subject, corrects, total, ball):
    text = f"🏆 YANGI NATIJA!\n👤: {name}\n📚: {subject}\n✅: {corrects}\n📊: {ball}%"
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

def check_already_finished(name, subject):
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Results", ttl=0)
        if df is None or df.empty: return False
        return not df[(df['Ism-familiya'].str.strip().str.lower() == name.strip().lower()) & (df['Fan'] == subject)].empty
    except: return False

@st.cache_data(ttl=600)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=600)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- GAMES ---
def spin_the_wheel(q_df, u_name):
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("## 🎡 Omad G'ildiragi")
    
    if 'wheel_subject' not in st.session_state:
        if st.button("Fanni aniqlash uchun aylantiring 🌀"):
            subjects = q_df['Fan'].unique().tolist()
            placeholder = st.empty()
            for i in range(15):
                temp = random.choice(subjects)
                placeholder.markdown(f"<p class='spin-text'>{temp}</p>", unsafe_allow_html=True)
                time.sleep(0.08)
            final_sub = random.choice(subjects)
            st.session_state.wheel_subject = final_sub
            st.rerun()
    else:
        st.markdown(f"<div style='text-align:center; padding:20px; border:2px dashed #92FE9D; border-radius:15px;'><h3>Tanlangan fan: <br><span style='color:#92FE9D; font-size:45px;'>{st.session_state.wheel_subject}</span></h3></div>", unsafe_allow_html=True)
        
        if st.button("Savollarni aniqlash uchun yana aylantiring 🎰"):
            if check_already_finished(u_name, st.session_state.wheel_subject):
                st.error("Siz bu fandan o'tib bo'lgansiz!")
                del st.session_state.wheel_subject
            else:
                sub_qs = q_df[q_df['Fan'] == st.session_state.wheel_subject].sample(n=min(len(q_df[q_df['Fan']==st.session_state.wheel_subject]), 20))
                items = [{"q": r['Savol'], "o": random.sample([str(r['A']), str(r['B']), str(r['C']), str(r['D'])], 4), "c": str(r['Javob']), "t": 30} for _, r in sub_qs.iterrows()]
                st.session_state.update({"test_items": items, "total_time": len(items)*30, "start_time": time.time(), "full_name": u_name, "selected_subject": st.session_state.wheel_subject, "test_run": True})
                del st.session_state.wheel_subject
                st.rerun()
        if st.button("Boshqa fan tanlash 🔄"):
            del st.session_state.wheel_subject
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- MAIN LOGIC ---
q_df = load_questions()
apply_styles(st.session_state.get('selected_subject', 'Default'))

st.sidebar.title("💎 Testmasters")
menu = st.sidebar.selectbox("Bo'lim:", ["Bosh sahifa", "Yakka Test 📝", "Jamoaviy Arqon ⚔️", "Omad G'ildiragi 🎡"])

if st.session_state.get('test_run'):
    # ONLINE TIMER CHAP TOMONDA (SIDEBAR)
    rem = max(0, int(st.session_state.total_time - (time.time() - st.session_state.start_time)))
    st.sidebar.markdown(f"<div class='timer-card'>{rem//60:02d}:{rem%60:02d}</div>", unsafe_allow_html=True)
    st.sidebar.write(f"👤 {st.session_state.full_name}")
    st.sidebar.write(f"📚 {st.session_state.selected_subject}")
    
    if rem <= 0:
        st.session_state.test_run = False
        st.rerun()

    with st.form("quiz_form"):
        st.markdown(f"## {st.session_state.selected_subject} testi")
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"<div class='info-box'><b>{i+1}. {item['q']}</b></div>", unsafe_allow_html=True)
            user_answers[i] = st.radio(f"Savol {i+1}", item['o'], index=None, key=f"q_{i}", label_visibility="collapsed")
        
        if st.form_submit_button("🏁 TESTNI YAKUNLASH"):
            if any(v is None for v in user_answers.values()):
                st.error("Iltimos, barcha savollarni belgilang! Belgilanmagan savollar bor.")
            else:
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball, "corrects": corrects, "total": len(st.session_state.test_items)}
                st.session_state.test_run = False
                st.rerun()

elif st.session_state.get('final_score'):
    res = st.session_state.final_score
    st.balloons()
    st.markdown(f"""<div style="background:rgba(0,0,0,0.8); padding:40px; border-radius:30px; text-align:center; border:3px solid #92FE9D;">
        <h1 style="color:#92FE9D; font-size:60px;">{res['ball']}%</h1>
        <h3>Tabriklaymiz, {res['name']}!</h3>
        <p>To'g'ri javoblar: {res['corrects']} / {res['total']}</p>
        <p style='color:#00C9FF;'>Sertifikatni yuklab olish uchun @Testmasters_LC kanaliga kiring!</p>
        <a href="https://t.me/Testmasters_LC" target="_blank"><button style="width:100%; padding:12px; background:#00C9FF; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">KANALGA O'TISH</button></a>
    </div>""", unsafe_allow_html=True)
    if st.button("Bosh sahifaga qaytish"):
        st.session_state.final_score = None
        st.rerun()

elif menu == "Bosh sahifa":
    st.title("🎓 Testmasters Online Platformasi")
    st.image("https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000")
    st.markdown("<div class='info-box'>Ismingizni kiriting va bo'limlardan birini tanlang. Har bir fandan faqat bir marta o'tish mumkin.</div>", unsafe_allow_html=True)

elif menu == "Yakka Test 📝":
    u_name = st.text_input("Ism-familiyangizni kiriting:", key="yakka_name")
    sub = st.selectbox("Fanni tanlang:", q_df['Fan'].unique())
    if st.button("🚀 TESTNI BOSHLASH"):
        if u_name and not check_already_finished(u_name, sub):
            sub_qs = q_df[q_df['Fan'] == sub].sample(n=min(len(q_df[q_df['Fan']==sub]), 20))
            items = [{"q": r['Savol'], "o": random.sample([str(r['A']), str(r['B']), str(r['C']), str(r['D'])], 4), "c": str(r['Javob']), "t": 30} for _, r in sub_qs.iterrows()]
            st.session_state.update({"test_items": items, "total_time": len(items)*30, "start_time": time.time(), "full_name": u_name, "selected_subject": sub, "test_run": True})
            st.rerun()
        elif check_already_finished(u_name, sub): st.error("Siz bu fandan o'tib bo'lgansiz!")
        else: st.warning("Ismingizni kiriting!")

elif menu == "Omad G'ildiragi 🎡":
    u_name = st.text_input("Ism-familiyangizni kiriting:", key="wheel_name")
    if u_name: spin_the_wheel(q_df, u_name)
    else: st.info("G'ildirakni aylantirish uchun ismingizni kiriting.")

elif menu == "Jamoaviy Arqon ⚔️":
    # Arqon tortish mantiqi (avvalgi koddan o'zgarmagan holda integratsiya qilinadi)
    u_name = st.text_input("Jamoa sardori ismi:", key="tug_name")
    sub = st.selectbox("Fan:", q_df['Fan'].unique(), key="tug_sub")
    if u_name:
        from __main__ import team_tug_of_war # O'zini chaqirish yoki funksiyani shu yerda saqlash
        # (team_tug_of_war funksiyasi yuqoridagi kabi ishlaydi)
