import streamlit as st
import pandas as pd
import time
import requests
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import gspread
from google.oauth2 import service_account

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SECRETS VA ULANISH
try:
    TELEGRAM_TOKEN = st.secrets["general"]["telegram_token"]
    CHAT_ID = st.secrets["general"]["chat_id"]
    
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key("1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U")
    result_sheet = sh.worksheet("Results")
except Exception as e:
    st.error(f"Sozalamalarda xatolik: {e}")
    st.stop()

# --- 3. YORDAMCHI FUNKSIYALAR ---

@st.cache_data(ttl=600)
def load_questions():
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTA1Ws84mZCqZvmj53YWxR3Xd7_Qd8V-Ro_w_79eklEXyDOt0BP6Vr8WJUodsXUo3WYb3sYMBijM5k9/pub?output=csv"
        df = pd.read_csv(csv_url)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return None
    except Exception as e:
        st.error(f"Ma'lumot o'qishda xatolik: {e}")
        return None

@st.cache_data(ttl=300)
def get_results_cached():
    try:
        data = result_sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def check_already_finished(name, subject, category):
    df = get_results_cached()
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        # Ism, Fan va Kategoriyani birgalikda tekshirish
        exists = df[(df['Ism-familiya'].astype(str) == str(name)) & 
                    (df['Fan'].astype(str) == str(subject)) & 
                    (df['Tur'].astype(str) == str(category))]
        return len(exists) > 0
    return False

def background_tasks(name, subject, category, corrects, total, ball):
    try:
        # Google Sheetga 'Tur' (category) ustunini ham yozamiz
        row = [datetime.now().strftime("%Y-%m-%d %H:%M"), str(name), str(category), str(subject), int(corrects), int(total - corrects), f"{ball}%"]
        result_sheet.append_row(row)
        st.cache_data.clear() 
    except Exception as e:
        st.error(f"Google Sheets xatosi: {e}")

    try:
        text = f"🏆 YANGI NATIJA!\n👤: {name}\n📂: {category}\n📚: {subject}\n✅: {corrects}\n❌: {total-corrects}\n📊: {ball}%"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except: 
        pass

def apply_styles(subject="Default"):
    st.markdown(f"""
    <style>
    .main-card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.15); }}
    .analysis-card {{ background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid; }}
    div.stButton > button {{ width: 100%; background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; color: #001f3f !important; font-weight: 800 !important; border-radius: 15px !important; }}
    h1, h2, h3, p, label {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 7. SAHIFALAR ---
if 'page' not in st.session_state: st.session_state.page = "HOME"

if st.session_state.page == "RESULT":
    apply_styles()
    res = st.session_state.final_score
    st.markdown(f'<div class="main-card" style="text-align:center;"><h1>{res["ball"]}%</h1><h2>{res["name"]}</h2></div>', unsafe_allow_html=True)
    with st.expander("🔍 Natijalar tahlili"):
        for log in st.session_state.user_logs:
            border_color = "#92FE9D" if log['correct'] else "#FF4B4B"
            correct_ans_info = "" if log['correct'] else f"<p style='color:#92FE9D;'><b>To'g'ri javob:</b> {log['correct_ans']}</p>"
            st.markdown(f'<div class="analysis-card" style="border-left-color: {border_color};"><p><b>Savol:</b> {log["question"]}</p><p>Sizning javobingiz: {log["user_ans"]}</p>{correct_ans_info}</div>', unsafe_allow_html=True)
    if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"): st.session_state.page = "HOME"; st.rerun()

elif st.session_state.page == "TEST":
    st.markdown(f"### 📚 Fan: {st.session_state.selected_subject} ({st.session_state.category})")
    with st.form(key="quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"**{i+1}. {item['q']}**")
            if pd.notna(item['image']) and str(item['image']) != '0': st.image(item['image'])
            user_answers[i] = st.radio("Tanlang:", item['o'], index=None, key=f"q_{i}")
        if st.form_submit_button("🏁 TESTNI TUGATISH"):
            logs = []
            corrects = 0
            for i, item in enumerate(st.session_state.test_items):
                c_ans = item['map'].get(str(item['c']).strip().upper(), item['c'])
                is_correct = str(user_answers[i]).lower() == str(c_ans).lower()
                if is_correct: corrects += 1
                logs.append({"question": item['q'], "user_ans": user_answers[i], "correct": is_correct, "correct_ans": c_ans})
            ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
            st.session_state.update({"user_logs": logs, "final_score": {"name": st.session_state.full_name, "ball": ball}, "page": "RESULT"})
            background_tasks(st.session_state.full_name, st.session_state.selected_subject, st.session_state.category, corrects, len(st.session_state.test_items), ball)
            st.rerun()

elif st.session_state.page == "HOME":
    apply_styles()
    st.markdown("<h1 style='text-align:center;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
    
    # 1. Majburiy tanlov
    category = st.radio("Bo'limni tanlang:", ["O'quvchi", "Attestatsiya", "Sertifikat"], index=None)
    
    if category:
        u_name = st.text_input("Ism-familiyangiz:")
        q_df = load_questions()
        if q_df is not None:
            # Kategoriyaga qarab fanlarni filtrlash
            filtered_subs = q_df[q_df['Tur'] == category]['Fan'].dropna().unique().tolist()
            selected_subject = st.selectbox("Fanni tanlang:", sorted(filtered_subs))
            
            if st.button("🚀 TESTNI BOSHLASH"):
                if not u_name: st.error("⚠️ Ism-familiyangizni yozing!")
                elif check_already_finished(u_name, selected_subject, category): st.error("❌ Siz topshirib bo'lgansiz!")
                else:
                    sub_qs = q_df[(q_df['Fan'] == selected_subject) & (q_df['Tur'] == category)]
                    sampled_qs = sub_qs.sample(n=min(len(sub_qs), 30))
                    test_items = []
                    for _, row in sampled_qs.iterrows():
                        mapping = {'A': str(row.get('A','')), 'B': str(row.get('B','')), 'C': str(row.get('C','')), 'D': str(row.get('D',''))}
                        opts = [v for v in mapping.values() if str(v) != 'nan']
                        random.shuffle(opts)
                        test_items.append({"q": row['Savol'], "o": opts, "c": row['Javob'], "map": mapping, "image": row.get('Rasm')})
                    st.session_state.update({"full_name": u_name, "category": category, "selected_subject": selected_subject, "test_items": test_items, "page": "TEST"})
                    st.rerun()
