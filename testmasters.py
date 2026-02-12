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
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{bg_url}") no-repeat center center fixed !important; background-size: cover !important; }}
    .info-box {{ background: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); border-left: 5px solid #00C9FF; margin-bottom: 20px; }}
    div[data-testid="stFormSubmitButton"] button, .stButton > button {{ width: 100% !important; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important; color: black !important; font-size: 20px !important; font-weight: bold !important; border-radius: 12px !important; border: none !important; padding: 12px !important; box-shadow: 0 4px 15px rgba(0,201,255,0.4); }}
    .timer-card {{ background: linear-gradient(135deg, #00C9FF, #92FE9D); padding: 15px; border-radius: 12px; text-align: center; color: black !important; font-weight: bold; margin-bottom: 20px; }}
    .stRadio > label {{ color: white !important; font-size: 18px !important; }}
    .stMarkdown, p, h1, h2, h3, label {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNKSIYALAR ---
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
        exists = df[(df['Ism-familiya'].str.strip().str.lower() == name.strip().lower()) & 
                    (df['Fan'].str.strip().str.lower() == subject.strip().lower())]
        return not exists.empty
    except: return False

@st.cache_data(ttl=600)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions", ttl=600)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- O'YINLAR ---
def spin_the_wheel(q_df, u_name):
    st.markdown("## 🎡 Omad G'ildiragi")
    subjects = q_df['Fan'].unique().tolist()
    
    if st.button("G'ildirakni aylantirish 🌀"):
        placeholder = st.empty()
        for i in range(12):
            temp = random.choice(subjects)
            placeholder.markdown(f"<h1 style='text-align:center; color:#00C9FF;'>{temp}</h1>", unsafe_allow_html=True)
            time.sleep(0.1)
        
        final_sub = random.choice(subjects)
        placeholder.markdown(f"<div style='background:#92FE9D; padding:20px; border-radius:15px; text-align:center;'><h1 style='color:black;'>{final_sub}</h1></div>", unsafe_allow_html=True)
        
        if check_already_finished(u_name, final_sub):
            st.error(f"Siz {final_sub} fanidan test topshirib bo'lgansiz!")
        else:
            st.session_state.selected_subject = final_sub
            st.info(f"Tayyorlaning! {final_sub} fanidan savollar yuklanmoqda...")
            time.sleep(2)
            # Testni boshlash mantiqi
            sub_qs = q_df[q_df['Fan'] == final_sub].sample(n=min(len(q_df[q_df['Fan']==final_sub]), 20))
            items = []
            for _, r in sub_qs.iterrows():
                opts = [str(r['A']), str(r['B']), str(r['C']), str(r['D'])]
                random.shuffle(opts)
                items.append({"q": r['Savol'], "o": opts, "c": str(r['Javob']), "t": 30})
            st.session_state.test_items = items
            st.session_state.total_time = len(items) * 30
            st.session_state.start_time = time.time()
            st.session_state.full_name = u_name
            st.session_state.test_run = True
            st.rerun()

def team_tug_of_war(q_df, subject, u_name):
    st.markdown(f"## ⚔️ Arqon Tortish: {subject}")
    if check_already_finished(u_name, subject):
        st.error("Siz bu fan bo'yicha o'yinda qatnashib bo'lgansiz!")
        return

    if 'tug_score' not in st.session_state:
        st.session_state.tug_score = 50
        st.session_state.current_q = q_df[q_df['Fan'] == subject].sample(1).iloc[0]

    # Online Vaqt va Progress
    st.progress(st.session_state.tug_score / 100)
    c1, c2, c3 = st.columns([1,2,1])
    c1.markdown("**🤖 Robot Jamoasi**")
    c3.markdown(f"**👨‍🎓 {u_name} Jamoasi**")

    q = st.session_state.current_q
    st.write(f"### Savol: {q['Savol']}")
    ans = st.radio("Javobingizni tanlang:", [str(q['A']), str(q['B']), str(q['C']), str(q['D'])], index=None)
    
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
                st.success("Sertifikatni yuklab olish uchun kanalimizga o'ting!")
                del st.session_state.tug_score
            elif st.session_state.tug_score <= 0:
                st.error("Robotlar yutdi!")
                del st.session_state.tug_score
            else:
                st.session_state.current_q = q_df[q_df['Fan'] == subject].sample(1).iloc[0]
                st.rerun()

# --- ASOSIY MANTIQ ---
q_df = load_questions()

st.sidebar.title("💎 Testmasters Menyu")
menu = st.sidebar.selectbox("Bo'lim:", ["Bosh sahifa", "Yakka Test 📝", "Jamoaviy Arqon ⚔️", "Omad G'ildiragi 🎡"])

if menu == "Bosh sahifa":
    apply_styles("Default")
    st.title("🎓 Testmasters Online")
    st.image("https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000")
    st.markdown('<div class="info-box">Ism-familiyangizni kiriting va o\'yinni boshlang!</div>', unsafe_allow_html=True)

elif menu == "Yakka Test 📝":
    if st.session_state.get('test_run'):
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
            
            submit = st.form_submit_button("🏁 TESTNI YAKUNLASH")
            if submit:
                if any(v is None for v in user_answers.values()):
                    st.error("Hamma savollarni belgilang!")
                else:
                    corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                    ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                    send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                    save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                    st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball, "corrects": corrects, "total": len(st.session_state.test_items)}
                    st.session_state.test_run = False
                    st.rerun()
                    
    elif st.session_state.get('final_score'):
        apply_styles("Default")
        res = st.session_state.final_score
        st.balloons()
        st.markdown(f"""<div style="background:rgba(0,0,0,0.8); padding:40px; border-radius:25px; text-align:center; border:2px solid #92FE9D;">
            <h1 style="color:#92FE9D;">{res['ball']}%</h1>
            <p>To'g'ri javoblar: {res['corrects']} / {res['total']}</p>
            <p>Sertifikatni yuklab olish uchun @Testmasters_LC kanaliga kiring!</p>
            <a href="https://t.me/Testmasters_LC" target="_blank"><button style="width:100%; padding:10px; background:#00C9FF; border:none; border-radius:10px; font-weight:bold;">KANALGA O'TISH</button></a>
        </div>""", unsafe_allow_html=True)
        if st.button("Bosh sahifa"):
            st.session_state.final_score = None
            st.rerun()
    else:
        u_name = st.text_input("Ism-familiyangiz:")
        all_subs = q_df['Fan'].dropna().unique().tolist()
        sub = st.selectbox("Fanni tanlang:", all_subs)
        if st.button("🚀 TESTNI BOSHLASH"):
            if u_name and not check_already_finished(u_name, sub):
                sub_qs = q_df[q_df['Fan'] == sub].sample(n=min(len(q_df[q_df['Fan']==sub]), 20))
                items = [{"q": r['Savol'], "o": random.sample([str(r['A']), str(r['B']), str(r['C']), str(r['D'])], 4), "c": str(r['Javob']), "t": 30} for _, r in sub_qs.iterrows()]
                st.session_state.update({"test_items": items, "total_time": len(items)*30, "start_time": time.time(), "full_name": u_name, "selected_subject": sub, "test_run": True})
                st.rerun()
            elif check_already_finished(u_name, sub): st.error("Siz bu fandan o'tib bo'lgansiz!")
            else: st.warning("Ismingizni kiriting!")

elif menu == "Jamoaviy Arqon ⚔️":
    u_name = st.text_input("Ism-familiya (Jamoa sardori):")
    sub = st.selectbox("Fan:", q_df['Fan'].unique())
    if u_name: team_tug_of_war(q_df, sub, u_name)

elif menu == "Omad G'ildiragi 🎡":
    u_name = st.text_input("Ism-familiya:")
    if u_name: spin_the_wheel(q_df, u_name)
