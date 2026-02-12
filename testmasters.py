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
    /* Radio buttonlarning xiralashishini oldini olish uchun */
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
        existing_res = conn.read(spreadsheet=SHEET_URL, worksheet="Results", ttl=0) # TTL 0 - real vaqtda o'qish
        updated_res = pd.concat([existing_res, new_data], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_res)
    except: pass

def check_already_finished(name, subject):
    try:
        # TTL=0 keshni o'chiradi va har safar yangi ma'lumot oladi
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

# --- SESSION STATE ---
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

q_df = load_questions()

# --- MANTIQ ---

# 1. TEST JARAYONI
if st.session_state.test_run:
    apply_styles(st.session_state.selected_subject)
    
    # Vaqtni hisoblash
    now = time.time()
    elapsed = now - st.session_state.start_time
    rem = max(0, int(st.session_state.total_time - elapsed))
    
    # Sidebar ma'lumotlari
    st.sidebar.markdown(f'<div class="timer-card"><h2>{rem//60:02d}:{rem%60:02d}</h2><small>VAQT QOLDI</small></div>', unsafe_allow_html=True)
    st.sidebar.info(f"👤 {st.session_state.full_name}\n\n📚 {st.session_state.selected_subject}")

    # Vaqt tugasa avtomatik yakunlash
    if rem <= 0:
        st.session_state.test_run = False
        st.session_state.final_score = {"name": st.session_state.full_name, "ball": 0, "score": 0, "total": len(st.session_state.test_items)}
        st.rerun()

    with st.form("quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"**{i+1}. {item['q']}**")
            # index=None - o'quvchi o'zi belgilashi shart
            user_answers[i] = st.radio(f"Javobni tanlang {i}:", item['o'], index=None, key=f"q_{i}", label_visibility="collapsed")
            st.write("---")
        
        submitted = st.form_submit_button("🏁 TESTNI YAKUNLASH")
        
        if submitted:
            # HAMMASI BELGILANGANINI TEKSHIRISH
            if any(ans is None for ans in user_answers.values()):
                st.error("⚠️ Iltimos, barcha savollarga javob bering! Ba'zi savollar belgilanmagan.")
            else:
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                
                st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball, "score": corrects, "total": len(st.session_state.test_items)}
                st.session_state.test_run = False
                st.rerun()

# 2. NATIJA OYNASI
elif st.session_state.final_score:
    apply_styles("Default")
    res = st.session_state.final_score
    st.balloons()
    st.markdown(f"""
        <div style="background:rgba(0,0,0,0.8); padding:40px; border-radius:25px; text-align:center; border:2px solid #92FE9D;">
            <h1 style="color:#92FE9D; font-size:70px; margin:0;">{res['ball']}%</h1>
            <h2 style="margin-top:10px; color:white;">{res['name']}</h2>
            <p style="color:white;">To'g'ri javoblar: {res['score']} / {res['total']}</p>
            <p style="color:#00C9FF;">Natijangiz muvaffaqiyatli saqlandi!</p>
            <br>
            <a href="/" target="_self">
                <button style="width:100%; background:#00C9FF; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">
                    🔄 BOSHQA FANLARNI TOPSHIRISH
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Bosh sahifaga qaytish"):
        st.session_state.final_score = None
        st.rerun()

# 3. KIRISH OYNASI
else:
    apply_styles("Default")
    st.title("🎓 Testmasters Online")
    st.markdown('''<div class="info-box"><h3>📝 Yo'riqnoma:</h3><ul>
        <li>Ism-familiyangizni to'liq va to'g'ri kiriting.</li>
        <li>Har bir fandan faqat 1 marta test topshirish mumkin.</li>
        <li><b>Sertifikatni yuklab olish uchun ism-familiyangizni to'liq kiriting.</b></li>
        </ul></div>''', unsafe_allow_html=True)
    
    u_name = st.text_input("Ism-familiyangizni kiriting:", placeholder="Masalan: Ali Valiyev")
    
    if q_df is not None:
        all_subs = q_df['Fan'].dropna().unique().tolist()
        selected_subject = st.selectbox("Fanni tanlang:", all_subs)

        if st.button("🚀 TESTNI BOSHLASH"):
            if not u_name or len(u_name) < 3:
                st.error("⚠️ Iltimos, ism-familiyangizni to'liq kiriting!")
            elif check_already_finished(u_name, selected_subject):
                st.error(f"❌ Kechirasiz, {u_name}. Siz {selected_subject} fanidan test topshirib bo'lgansiz!")
            else:
                sub_qs = q_df[q_df['Fan'] == selected_subject].copy()
                if sub_qs.empty:
                    st.error("Bu fan bo'yicha savollar topilmadi.")
                else:
                    selected_qs = sub_qs.sample(n=min(len(sub_qs), 30))
                    test_items = []
                    for _, row in selected_qs.iterrows():
                        opts = [str(row['A']), str(row['B']), str(row['C']), str(row['D'])]
                        random.shuffle(opts)
                        test_items.append({
                            "q": row['Savol'], 
                            "o": opts, 
                            "c": str(row['Javob']), 
                            "t": pd.to_numeric(row['Vaqt'], errors='coerce') or 30
                        })
                    
                    st.session_state.test_items = test_items
                    st.session_state.total_time = sum(item['t'] for item in test_items)
                    st.session_state.start_time = time.time()
                    st.session_state.full_name = u_name
                    st.session_state.selected_subject = selected_subject
                    st.session_state.test_run = True
                    st.rerun()
