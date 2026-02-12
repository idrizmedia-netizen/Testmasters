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

# Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNKSIYALAR ---

@st.cache_data(ttl=60)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

def check_already_finished(name, subject):
    try:
        # Results varag'ini tekshirish
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        if df.empty: return False
        
        # Ism va Fanni kichik harflarda solishtirish (aniqlik uchun)
        exists = df[(df['Ism-familiya'].str.strip().str.lower() == name.strip().lower()) & 
                    (df['Fan'].str.strip().str.lower() == subject.strip().lower())]
        return not exists.empty
    except: return False

def save_result_to_sheets(name, subject, corrects, total, ball):
    try:
        # Yangi ma'lumotlar qatori
        new_data = pd.DataFrame([{
            "Sana": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ism-familiya": name,
            "Fan": subject,
            "To'g'ri": corrects,
            "Xato": total - corrects,
            "Ball (%)": f"{ball}%"
        }])
        
        # Mavjud natijalarni o'qish
        existing_results = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        
        # Yangi ma'lumotni qo'shish
        updated_df = pd.concat([existing_results, new_data], ignore_index=True)
        
        # Google Sheets'ga qayta yozish
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_df)
        return True
    except Exception as e:
        st.error(f"Xatolik yuz berdi: {e}")
        return False

def send_to_telegram(name, subject, corrects, total, ball):
    text = (f"🏆 **YANGI NATIJA!**\n\n"
            f"👤 O'quvchi: {name}\n"
            f"📚 Fan: {subject}\n"
            f"✅ To'g'ri: {corrects}\n"
            f"❌ Xato: {total-corrects}\n"
            f"📊 Natija: {ball}%")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except: pass

# --- DIZAYN (apply_styles funksiyasi o'zgarishsiz qoladi) ---
def apply_styles(subject="Default"):
    # (Sizning stil kodingiz shu yerda...)
    st.markdown("""<style>...</style>""", unsafe_allow_html=True) # Qisqartirildi

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "HOME"

# --- ASOSIY MANTIQ ---

if st.session_state.page == "RESULT":
    apply_styles()
    res = st.session_state.final_score
    st.balloons()
    st.markdown(f"""
        <div class="main-card" style="text-align:center;">
            <h1 style="color:#92FE9D; font-size:100px; margin:0;">{res['ball']}%</h1>
            <h2>{res['name']}</h2>
            <p>Sizning natijangiz muvaffaqiyatli saqlandi va guruhga yuborildi!</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 CHIQISH"):
        st.session_state.page = "HOME"
        st.rerun()

elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    elapsed = time.time() - st.session_state.start_time
    rem = max(0, int(st.session_state.total_time - elapsed))
    
    if rem <= 0:
        st.session_state.page = "RESULT"
        st.rerun()

    st.sidebar.markdown(f"⏱ **Vaqt: {rem//60:02d}:{rem%60:02d}**")
    
    with st.form("quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.write(f"**{i+1}. {item['q']}**")
            user_answers[i] = st.radio("Tanlang:", item['o'], key=f"q_{i}", index=None)
        
        if st.form_submit_button("🏁 TESTNI TUGATISH"):
            if None in user_answers.values():
                st.warning("Iltimos, hamma savollarga javob bering!")
            else:
                corrects = sum(1 for i, item in enumerate(st.session_state.test_items) if str(user_answers[i]) == str(item['c']))
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                
                # 1. Google Sheets'ga saqlash
                save_success = save_result_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                
                # 2. Telegramga yuborish
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                
                st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball}
                st.session_state.page = "RESULT"
                st.rerun()
    time.sleep(1)
    st.rerun()

elif st.session_state.page == "HOME":
    apply_styles()
    st.title("🎓 Testmasters Online")
    u_name = st.text_input("Ism-familiyangizni kiriting:")
    
    q_df = load_questions()
    if q_df is not None:
        all_subs = sorted(q_df['Fan'].dropna().unique().tolist())
        selected_subject = st.selectbox("Fanni tanlang:", all_subs)

        if st.button("🚀 TESTNI BOSHLASH"):
            if not u_name:
                st.error("Ismingizni kiriting!")
            # BU YERDA TEKSHIRAMIZ:
            elif check_already_finished(u_name, selected_subject):
                st.error(f"❌ Kechirasiz, {u_name}. Siz {selected_subject} fanidan test topshirib bo'lgansiz!")
            else:
                # Testni tayyorlash (sample questions)
                sub_qs = q_df[q_df['Fan'] == selected_subject].copy()
                selected_qs = sub_qs.sample(n=min(len(sub_qs), 20))
                
                test_items = []
                for _, row in selected_qs.iterrows():
                    opts = [str(row['A']), str(row['B']), str(row['C']), str(row['D'])]
                    random.shuffle(opts)
                    test_items.append({"q": row['Savol'], "o": opts, "c": str(row['Javob'])})
                
                st.session_state.full_name = u_name
                st.session_state.selected_subject = selected_subject
                st.session_state.test_items = test_items
                st.session_state.total_time = len(test_items) * 45
                st.session_state.start_time = time.time()
                st.session_state.page = "TEST"
                st.rerun()
