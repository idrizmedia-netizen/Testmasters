import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR
TELEGRAM_TOKEN = "8541792718:AAF4SNckR8rTqB1WwPJrc3HzF-KpTv5mWd0"
CHAT_ID = "@Testmasters_LC"  # To'g'rilangan username
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- TELEGRAMGA NATIJANI YUBORISH FUNKSIYASI ---
def send_to_telegram(name, subject, corrects, total, ball):
    text = (
        f"🏆 **YANGI NATIJA!**\n\n"
        f"👤 **O'quvchi:** {name}\n"
        f"📚 **Fan:** {subject}\n"
        f"✅ **To'g'ri javob:** {corrects} ta\n"
        f"❌ **Xato javob:** {total - corrects} ta\n"
        f"📊 **Umumiy ball:** {ball} %\n\n"
        f"🤖 @Testmasters1_bot orqali yuborildi."
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Telegramga yuborishda xato: {e}")

# --- FONLAR VA TUGMA STILLARI ---
bg_styles = {
    "Kimyo": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1603126731702-5094e430ba31?auto=format&fit=crop&w=1600&q=80')",
    "Biologiya": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1530026405186-ed1f139313f8?auto=format&fit=crop&w=1600&q=80')",
    "Ingliz tili": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1543167664-c92155e96916?auto=format&fit=crop&w=1600&q=80')",
    "Geografiya": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1521295121683-bc014fe1003e?auto=format&fit=crop&w=1600&q=80')",
    "Huquq": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1600&q=80')",
    "Rus tili": "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?auto=format&fit=crop&w=1600&q=80')",
    "Default": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)"
}

def set_background(subject):
    bg = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg}; background-size: cover; background-attachment: fixed; }}
    .stMarkdown, p, h1, h2, h3, span, label {{ color: white !important; }}
    .stButton > button {{
        width: 100%;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #000 !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 12px !important;
        border-radius: 12px !important;
        border: 2px solid white !important;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5) !important;
    }}
    div[data-testid="stForm"] {{
        background: rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- SAVOLLARNI DARAGALARGA AJRATIB TANLASH ---
def get_balanced_questions(df, subject, n_total=30):
    sub_qs = df[df['Fan'] == subject].copy()
    if len(sub_qs) <= n_total:
        return sub_qs.sample(frac=1)
    oson = sub_qs[(sub_qs['Vaqt'] >= 30) & (sub_qs['Vaqt'] <= 40)]
    orta = sub_qs[(sub_qs['Vaqt'] >= 41) & (sub_qs['Vaqt'] <= 70)]
    qiyin = sub_qs[sub_qs['Vaqt'] >= 71]
    selected = []
    for group in [oson, orta, qiyin]:
        if not group.empty:
            selected.append(group.sample(n=min(len(group), 10)))
    final_qs = pd.concat(selected)
    if len(final_qs) < n_total:
        needed = n_total - len(final_qs)
        remaining = sub_qs.drop(final_qs.index)
        final_qs = pd.concat([final_qs, remaining.sample(n=min(len(remaining), needed))])
    return final_qs.sample(frac=1)

@st.cache_data(ttl=600)
def load_questions_cached():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Xato: {e}")
        return None

# --- SESSION STATE ---
if 'test_run' not in st.session_state: st.session_state.test_run = False
if 'final_score' not in st.session_state: st.session_state.final_score = None

# --- ASOSIY QISM ---
q_df = load_questions_cached()

if q_df is not None:
    available_subjects = q_df['Fan'].dropna().unique().tolist()
    st.title("🚀 Testmasters Online")

    if not st.session_state.test_run and st.session_state.final_score is None:
        set_background("Default")
        u_name = st.text_input("Ism-familiyangizni kiriting:").strip()
        if u_name:
            selected_subject = st.selectbox("Fanni tanlang:", available_subjects)
            set_background(selected_subject)
            if st.button(f"🚀 {selected_subject} fanidan boshlash"):
                st.session_state.questions = get_balanced_questions(q_df, selected_subject)
                st.session_state.total_time = int(st.session_state.questions['Vaqt'].sum())
                st.session_state.start_time = time.time()
                st.session_state.full_name = u_name
                st.session_state.selected_subject = selected_subject
                st.session_state.test_run = True
                st.rerun()

    if st.session_state.test_run:
        set_background(st.session_state.selected_subject)
        rem = max(0, st.session_state.total_time - int(time.time() - st.session_state.start_time))
        st.sidebar.markdown(f"# ⏳ Vaqt: {rem//60:02d}:{rem%60:02d}")
        if rem <= 0:
            st.session_state.test_run = False
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
                
                # --- TELEGRAMGA NATIJANI YUBORISH ---
                send_to_telegram(
                    st.session_state.full_name, 
                    st.session_state.selected_subject, 
                    corrects, 
                    total, 
                    ball
                )
                
                st.session_state.final_score = {"score": corrects, "total": total, "ball": ball}
                st.session_state.test_run = False
                st.rerun()
        time.sleep(1)
        st.rerun()

    if st.session_state.final_score:
        set_background("Default")
        st.success(f"### 🎉 Yakunlandi! Ball: {st.session_state.final_score['ball']}%")
        st.write(f"To'g'ri javoblar: {st.session_state.final_score['score']} ta")
        if st.button("🔄 Qayta boshlash"):
            st.session_state.final_score = None
            st.rerun()
