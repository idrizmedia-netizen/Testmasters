import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmasters_LC" 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- TELEGRAMGA NATIJANI YUBORISH FUNKSIYASI ---
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
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# --- FONLAR VA TUGMA STILLARI (TINIQLASHTIRILDI) ---
bg_styles = {
    "Kimyo": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1532187878418-9f1100188665?auto=format&fit=crop&w=1600&q=80')",
    "Biologiya": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&w=1600&q=80')",
    "Ingliz tili": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&w=1600&q=80')",
    "Geografiya": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1521295121683-bc014fe1003e?auto=format&fit=crop&w=1600&q=80')",
    "Huquq": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1600&q=80')",
    "Rus tili": "linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?auto=format&fit=crop&w=1600&q=80')",
    "Default": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
}

def apply_styles(subject):
    bg = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
    <style>
    .stApp {{ 
        background: {bg}; 
        background-size: cover; 
        background-attachment: fixed; 
        background-position: center;
    }}
    .stMarkdown, p, h1, h2, h3, span, label {{ 
        color: white !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }}
    
    button[kind="primaryFormSubmit"], .stButton > button {{
        width: 100% !important;
        background: linear-gradient(90deg, #FF512F 0%, #DD2476 100%) !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 15px !important;
        border-radius: 15px !important;
        border: none !important;
        box-shadow: 0px 5px 20px rgba(0,0,0,0.4) !important;
    }}
    
    div[data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        padding: 30px;
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- SAVOLLAR MANTIQI ---
def get_balanced_questions(df, subject, n_total=30):
    sub_qs = df[df['Fan'] == subject].copy()
    if len(sub_qs) <= n_total: return sub_qs.sample(frac=1)
    sub_qs['Vaqt'] = pd.to_numeric(sub_qs['Vaqt'], errors='coerce').fillna(30)
    oson = sub_qs[(sub_qs['Vaqt'] >= 30) & (sub_qs['Vaqt'] <= 40)]
    orta = sub_qs[(sub_qs['Vaqt'] >= 41) & (sub_qs['Vaqt'] <= 70)]
    qiyin = sub_qs[sub_qs['Vaqt'] >= 71]
    selected = []
    for group in [oson, orta, qiyin]:
        if not group.empty: selected.append(group.sample(n=min(len(group), 10)))
    final_qs = pd.concat(selected) if selected else pd.DataFrame()
    if len(final_qs) < n_total:
        remaining = sub_qs.drop(final_qs.index)
        final_qs = pd.concat([final_qs, remaining.sample(n=min(len(remaining), n_total - len(final_qs)))])
    return final_qs.sample(frac=1)

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
            st.error("⚠️ Siz testni topshirib bo'lgansiz. Bir marta topshirishga ruxsat berilgan.")
        else:
            u_name = st.text_input("Ism-familiyangizni kiriting:", placeholder="Ali Valiyev").strip()
            if u_name:
                selected_subject = st.selectbox("Fanni tanlang:", available_subjects)
                apply_styles(selected_subject)
                if st.button(f"🚀 {selected_subject} fanidan boshlash"):
                    qs = get_balanced_questions(q_df, selected_subject)
                    st.session_state.questions = qs
                    v_data = pd.to_numeric(qs['Vaqt'], errors='coerce').fillna(0)
                    st.session_state.total_time = int(v_data.sum())
                    st.session_state.start_time = time.time()
                    st.session_state.full_name = u_name
                    st.session_state.selected_subject = selected_subject
                    st.session_state.test_run = True
                    st.rerun()

    # --- 2. TEST JARAYONI ---
    if st.session_state.test_run:
        apply_styles(st.session_state.selected_subject)
        st.markdown(f"### 👤 O'quvchi: {st.session_state.full_name}")
        
        rem = max(0, st.session_state.total_time - int(time.time() - st.session_state.start_time))
        st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 20px; background: rgba(0,0,0,0.7); border-radius: 15px; border: 2px solid #92FE9D;">
            <h2 style="margin:0; color: #92FE9D;">⏳ {rem//60:02d}:{rem%60:02d}</h2>
            <p style="color: white; margin:0;">QOLGAN VAQT</p>
        </div>""", unsafe_allow_html=True)
        
        if rem <= 0:
            st.session_state.test_run = False
            st.session_state.completed = True
            st.rerun()

        with st.form("quiz_form"):
            u_ans = {}
            for i, (idx, row) in enumerate(st.session_state.questions.iterrows()):
                st.write(f"**{i+1}. {row['Savol']}**")
                u_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], index=None, key=f"q_{idx}")
            
            if st.form_submit_button("🏁 TESTNI YAKUNLASH"):
                corrects = sum(1 for idx, row in st.session_state.questions.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                total = len(st.session_state.questions)
                ball = round((corrects / total) * 100, 1)
                
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, total, ball)
                
                st.session_state.final_score = {
                    "name": st.session_state.full_name,
                    "subject": st.session_state.selected_subject,
                    "score": corrects, "total": total, "ball": ball
                }
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
        st.success(f"### 🎉 Natijangiz, {res['name']}!")
        
        # Natija oynasi tiniq va aniq ko'rinishi uchun alohida blok
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.6); padding: 25px; border-radius: 20px; border: 1px solid #92FE9D; text-align: center;">
            <h2 style="color: white;">Fan: {res['subject']}</h2>
            <h1 style="color: #92FE9D;">Ball: {res['ball']}%</h1>
            <p style="font-size: 20px;">To'g'ri javoblar: {res['score']} / {res['total']}</p>
            <hr>
            <p style="color: #ff4b4b;">⚠️ Test yakunlandi. Sizga muvaffaqiyat tilaymiz!</p>
        </div>
        """, unsafe_allow_html=True)
        # "Qaytish" tugmasi olib tashlandi, shunda o'quvchi qayta ishlay olmaydi.
