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

# --- TELEGRAMGA NATIJANI YUBORISH ---
def send_to_telegram(name, subject, corrects, total, ball):
    text = (
        f"🏆 YANGI NATIJA!\n\n"
        f"👤 O'quvchi: {name}\n"
        f"📚 Fan: {subject}\n"
        f"✅ To'g'ri javob: {corrects} ta\n"
        f"❌ Xato javob: {total - corrects} ta\n"
        f"📊 Umumiy ball: {ball} %\n\n"
        f"🤖 @Testmasters1_bot orqali yuborildi."
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except: pass

# --- GOOGLE SHEETS-GA SAQLASH ---
def save_to_sheets(name, subject, corrects, total, ball):
    try:
        new_data = pd.DataFrame([{
            "Sana": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ism-familiya": name,
            "Fan": subject,
            "To'g'ri javoblar": corrects,
            "Umumiy savollar": total,
            "Ball (%)": ball
        }])
        existing_res = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        updated_res = pd.concat([existing_res, new_data], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_res)
    except: pass

# --- FONLAR (TINIQ HD) ---
bg_styles = {
    "Kimyo": "url('https://images.unsplash.com/photo-1603126738550-9d32775f9032?q=80&w=2000&auto=format')",
    "Biologiya": "url('https://images.unsplash.com/photo-1576086213369-97a306dca664?q=80&w=2000&auto=format')",
    "Ingliz tili": "url('https://images.unsplash.com/photo-1543167664-c92155e96916?q=80&w=2000&auto=format')",
    "Geografiya": "url('https://images.unsplash.com/photo-1521295121683-bc014fe1003e?q=80&w=2000&auto=format')",
    "Huquq": "url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=2000&auto=format')",
    "Rus tili": "url('https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000&auto=format')",
    "Default": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
}

def apply_styles(subject):
    bg = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg}; background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
    .stMarkdown, p, h1, h2, h3, span, label {{ color: white !important; font-family: 'Segoe UI', sans-serif; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
    
    /* VARIANTLARNI OPTIMALLASHTIRISH */
    div[data-testid="stMarkdownContainer"] p {{ font-size: 18px !important; font-weight: 500; }}
    
    /* TUGMA STILLARI */
    button[kind="primaryFormSubmit"], .stButton > button {{
        width: 100% !important; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: black !important; font-size: 22px !important; font-weight: bold !important; padding: 15px !important;
        border-radius: 15px !important; border: none !important; box-shadow: 0px 5px 15px rgba(0,0,0,0.4) !important;
    }}
    
    /* TEST OYNASI (BLURSIZ TINIQ) */
    div[data-testid="stForm"] {{
        background: rgba(0, 0, 0, 0.75) !important;
        padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- SAVOLLARNI VA VARIANTLARNI TAYYORLASH ---
def prepare_test_data(df, subject):
    sub_qs = df[df['Fan'] == subject].copy()
    # 30 ta savolni tanlash (muvozanatli)
    selected_qs = sub_qs.sample(n=min(len(sub_qs), 30))
    
    test_items = []
    for _, row in selected_qs.iterrows():
        # Variantlarni ro'yxatga olish va aralashtirish
        options = [row['A'], row['B'], row['C'], row['D']]
        random.shuffle(options)
        test_items.append({
            "question": row['Savol'],
            "options": options,
            "correct": row['Javob'],
            "time": pd.to_numeric(row['Vaqt'], errors='coerce') or 30
        })
    return test_items

@st.cache_data(ttl=600)
def load_questions_cached():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- SESSION STATE ---
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None
if 'completed' not in st.session_state: st.session_state.completed = False

q_df = load_questions_cached()

if q_df is not None:
    available_subjects = q_df['Fan'].dropna().unique().tolist()
    
    # --- 1. BOSHLANG'ICH SAHIFA ---
    if not st.session_state.test_run and st.session_state.final_score is None:
        apply_styles("Default")
        st.title("🚀 Testmasters Online")
        
        if st.session_state.completed:
            st.error("⚠️ Siz testni topshirib bo'lgansiz.")
        else:
            st.markdown('<div style="background:rgba(255,255,255,0.1);padding:15px;border-radius:10px;border-left:5px solid #92FE9D;">📍 <b>DIQQAT:</b> Savollar va javob variantlari har safar tasodifiy tartibda chiqadi.</div>', unsafe_allow_html=True)
            u_name = st.text_input("Ism-familiyangizni kiriting:", placeholder="Masalan: Ali Valiyev").strip()
            if u_name:
                selected_subject = st.selectbox("Fanni tanlang:", available_subjects)
                apply_styles(selected_subject)
                if st.button(f"🚀 {selected_subject} fanidan boshlash"):
                    test_data = prepare_test_data(q_df, selected_subject)
                    st.session_state.test_items = test_data
                    st.session_state.total_time = sum(item['time'] for item in test_data)
                    st.session_state.start_time = time.time()
                    st.session_state.full_name = u_name
                    st.session_state.selected_subject = selected_subject
                    st.session_state.test_run = True
                    st.rerun()

    # --- 2. TEST JARAYONI ---
    if st.session_state.test_run:
        apply_styles(st.session_state.selected_subject)
        st.markdown(f"### 👤 O'quvchi: {st.session_state.full_name}")
        
        rem = max(0, int(st.session_state.total_time - (time.time() - st.session_state.start_time)))
        st.sidebar.markdown(f'<div style="text-align:center;padding:20px;background:rgba(0,0,0,0.8);border-radius:15px;border:2px solid #92FE9D;"><h2 style="color:#92FE9D;margin:0;">⏳ {rem//60:02d}:{rem%60:02d}</h2><p style="margin:0;">QOLGAN VAQT</p></div>', unsafe_allow_html=True)
        
        if rem <= 0:
            st.session_state.test_run = False
            st.session_state.completed = True
            st.rerun()

        with st.form("quiz_form"):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.write(f"**{i+1}. {item['question']}**")
                user_answers[i] = st.radio("Javobingiz:", item['options'], index=None, key=f"q_{i}")
            
            if st.form_submit_button("🏁 TESTNI YAKUNLASH"):
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['correct']))
                total = len(st.session_state.test_items)
                ball = round((corrects / total) * 100, 1)
                
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, total, ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, total, ball)
                
                st.session_state.final_score = {"name": st.session_state.full_name, "subject": st.session_state.selected_subject, "score": corrects, "total": total, "ball": ball}
                st.session_state.test_run = False
                st.session_state.completed = True
                st.rerun()
        
        time.sleep(1)
        st.rerun()

    # --- 3. NATIJA SAHIFASI ---
    if st.session_state.final_score:
        apply_styles("Default")
        res = st.session_state.final_score
        st.balloons()
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.85); padding: 40px; border-radius: 25px; border: 2px solid #92FE9D; text-align: center; margin-top: 20px;">
            <h2 style="color: white;">🎉 Natija: {res['name']}</h2>
            <h1 style="color: #92FE9D; font-size: 60px; margin: 20px 0;">{res['ball']}%</h1>
            <p style="font-size: 22px;">To'g'ri javoblar: {res['score']} ta / {res['total']} ta</p>
            <p style="color: #FFD700;">Natijangiz saqlandi va ustozga yuborildi.</p>
        </div>
        """, unsafe_allow_html=True)
