import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmasters_LC"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"
WIN_IMAGE = "https://img.freepik.com/free-vector/winner-background-first-place-victory-concept_52683-45814.jpg"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- DIZAYN VA FONLAR ---
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
    .spin-text {{ font-size: 40px; font-weight: bold; text-align: center; color: #00C9FF; }}
    div[data-testid="stFormSubmitButton"] button, .stButton > button {{ width: 100% !important; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important; color: black !important; font-weight: bold !important; border-radius: 12px !important; border: none !important; padding: 15px !important; }}
    .stMarkdown, p, h1, h2, h3, label {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- YORDAMCHI FUNKSIYALAR ---
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

# --- O'YIN FUNKSIYALARI ---
def team_tug_of_war(q_df, subject, u_name):
    st.markdown(f"## ⚔️ Arqon Tortish: {subject}")
    if check_already_finished(u_name, f"{subject} (Arqon)"):
        st.error("Siz bu fan bo'yicha o'yinda qatnashib bo'lgansiz!")
        return

    if 'tug_score' not in st.session_state:
        st.session_state.tug_score = 50
        st.session_state.current_q = q_df[q_df['Fan'] == subject].sample(1).iloc[0]

    st.progress(st.session_state.tug_score / 100)
    c1, _, c3 = st.columns([1,1,1])
    c1.markdown("**🤖 Robotlar**")
    c3.markdown(f"**👨‍🎓 {u_name}**")

    q = st.session_state.current_q
    st.write(f"### Savol: {q['Savol']}")
    opts = [str(q['A']), str(q['B']), str(q['C']), str(q['D'])]
    ans = st.radio("Javobingiz:", opts, index=None)
    
    if st.button("TORTISH! 💪"):
        if ans is None:
            st.warning("Javobni tanlang!")
        else:
            if ans.lower().strip() == str(q['Javob']).lower().strip():
                st.session_state.tug_score = min(100, st.session_state.tug_score + 25)
                st.success("To'g'ri!")
            else:
                st.session_state.tug_score = max(0, st.session_state.tug_score - 25)
                st.error("Xato!")
            
            if st.session_state.tug_score >= 100:
                st.image(WIN_IMAGE)
                st.balloons()
                save_to_sheets(u_name, f"{subject} (Arqon)", 1, 1, 100)
                send_to_telegram(u_name, f"{subject} (Arqon)", "G'alaba", 1, 100)
                st.success("G'alaba! Sertifikat uchun kanalga kiring.")
                del st.session_state.tug_score
            elif st.session_state.tug_score <= 0:
                st.error("Robotlar yutdi!")
                del st.session_state.tug_score
            else:
                st.session_state.current_q = q_df[q_df['Fan'] == subject].sample(1).iloc[0]
                st.rerun()

# --- ASOSIY MANTIQ ---
q_df = load_questions()
apply_styles(st.session_state.get('selected_subject', 'Default'))

st.sidebar.title("💎 Testmasters")
menu = st.sidebar.selectbox("Bo'lim:", ["Bosh sahifa", "Yakka Test 📝", "Jamoaviy Arqon ⚔️", "Omad G'ildiragi 🎡"])

# --- TEST REJIMI (XATOLIK TUZATILGAN) ---
if st.session_state.get('test_run'):
    # Taymerni barqaror qilish uchun sidebar'da joy band qilamiz
    st_autorefresh(interval=1000, key="timer_refresh_v3")
    timer_placeholder = st.sidebar.empty()
    
    rem = max(0, int(st.session_state.total_time - (time.time() - st.session_state.start_time)))
    
    # Faqat placeholder'ni yangilaymiz (bu removeChild xatosini yo'qotadi)
    timer_placeholder.markdown(f"""
        <div class='timer-card'>
            <small style='font-size: 12px; display: block; opacity: 0.8;'>Qolgan vaqt:</small>
            ⏱ {rem//60:02d}:{rem%60:02d}
        </div>
    """, unsafe_allow_html=True)
    
    if rem <= 0:
        st.session_state.test_run = False
        st.error("Vaqt tugadi!")
        st.rerun()

    with st.form("quiz_form"):
        st.markdown(f"## {st.session_state.selected_subject} testi")
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"<div class='info-box'><b>{i+1}. {item['q']}</b></div>", unsafe_allow_html=True)
            user_answers[i] = st.radio(f"Savol {i+1}", item['o'], index=None, key=f"q_{i}", label_visibility="collapsed")
        
        if st.form_submit_button("🏁 TESTNI YAKUNLASH"):
            if any(v is None for v in user_answers.values()):
                st.error("Iltimos, hamma savollarni belgilang!")
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
        <h3>Rahmat, {res['name']}!</h3>
        <p>To'g'ri javoblar: {res['corrects']} / {res['total']}</p>
        <a href="https://t.me/Testmasters_LC" target="_blank"><button style="width:100%; padding:12px; background:#00C9FF; border:none; border-radius:10px; font-weight:bold;">SERTIFIKATNI YUKLASH</button></a>
    </div>""", unsafe_allow_html=True)
    if st.button("Qaytish"):
        st.session_state.final_score = None
        st.rerun()

elif menu == "Bosh sahifa":
    st.title("🎓 Testmasters Online")
    st.image("https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000")
    st.markdown("<div class='info-box'>Xush kelibsiz! Ismingizni kiriting va fanni tanlang.</div>", unsafe_allow_html=True)

elif menu == "Yakka Test 📝":
    u_name = st.text_input("Ism-familiya:")
    sub = st.selectbox("Fan:", q_df['Fan'].unique())
    if st.button("🚀 BOSHLASH"):
        if u_name and not check_already_finished(u_name, sub):
            sub_qs = q_df[q_df['Fan'] == sub].sample(n=min(len(q_df[q_df['Fan']==sub]), 20))
            items = [{"q": r['Savol'], "o": random.sample([str(r['A']), str(r['B']), str(r['C']), str(r['D'])], 4), "c": str(r['Javob'])} for _, r in sub_qs.iterrows()]
            st.session_state.update({"test_items": items, "total_time": len(items)*30, "start_time": time.time(), "full_name": u_name, "selected_subject": sub, "test_run": True})
            st.rerun()
        elif check_already_finished(u_name, sub): st.error("Siz bu fandan o'tgansiz!")

elif menu == "Omad G'ildiragi 🎡":
    u_name = st.text_input("Ism-familiya:", key="wheel_n")
    if u_name:
        if 'wheel_sub' not in st.session_state:
            if st.button("Fanni aniqlash 🌀"):
                subs = q_df['Fan'].unique().tolist()
                p = st.empty()
                for _ in range(10):
                    p.markdown(f"<p class='spin-text'>{random.choice(subs)}</p>", unsafe_allow_html=True)
                    time.sleep(0.1)
                st.session_state.wheel_sub = random.choice(subs)
                st.rerun()
        else:
            st.success(f"Tanlangan fan: {st.session_state.wheel_sub}")
            if st.button("Savollarni aniqlash va boshlash 🎰"):
                if not check_already_finished(u_name, st.session_state.wheel_sub):
                    sub_qs = q_df[q_df['Fan'] == st.session_state.wheel_sub].sample(n=min(len(q_df[q_df['Fan']==st.session_state.wheel_sub]), 20))
                    items = [{"q": r['Savol'], "o": random.sample([str(r['A']), str(r['B']), str(r['C']), str(r['D'])], 4), "c": str(r['Javob'])} for _, r in sub_qs.iterrows()]
                    st.session_state.update({"test_items": items, "total_time": len(items)*30, "start_time": time.time(), "full_name": u_name, "selected_subject": st.session_state.wheel_sub, "test_run": True})
                    del st.session_state.wheel_sub
                    st.rerun()
                else: st.error("Bu fandan o'tib bo'lingan!")

elif menu == "Jamoaviy Arqon ⚔️":
    u_name = st.text_input("Sardor ismi:")
    sub = st.selectbox("Fan:", q_df['Fan'].unique(), key="tug_s")
    if u_name: team_tug_of_war(q_df, sub, u_name)
