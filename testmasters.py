import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
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
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# --- GOOGLE SHEETS-GA SAQLASH ---
def save_to_sheets(name, subject, corrects, total, ball):
    try:
        # Yangi natijani tayyorlash
        new_data = pd.DataFrame([{
            "Sana": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ism-familiya": name,
            "Fan": subject,
            "To'g'ri javoblar": corrects,
            "Umumiy savollar": total,
            "Ball (%)": ball
        }])
        
        # Google Sheets-ning "Results" varag'iga yozish
        # Eslatma: Sheets-da "Results" nomli varaq ochilgan bo'lishi kerak
        existing_res = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        updated_res = pd.concat([existing_res, new_data], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_res)
    except Exception as e:
        st.error(f"Sheetga saqlashda xatolik: {e}")

# --- STILLAR ---
bg_styles = {
    "Kimyo": "url('https://images.unsplash.com/photo-1532187878418-9f1100188665?q=80&w=2000&auto=format')",
    "Biologiya": "url('https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=2000&auto=format')",
    "Ingliz tili": "url('https://images.unsplash.com/photo-1543167664-c92155e96916?q=80&w=2000&auto=format')",
    "Geografiya": "url('https://images.unsplash.com/photo-1524661135-423995f22d0b?q=80&w=2000&auto=format')",
    "Huquq": "url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=2000&auto=format')",
    "Rus tili": "url('https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000&auto=format')",
    "Default": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
}

def apply_styles(subject):
    bg = bg_styles.get(subject, bg_styles["Default"])
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg}; background-size: cover !important; background-attachment: fixed !important; background-position: center !important; }}
    .stMarkdown, p, h1, h2, h3, span, label {{ color: white !important; font-family: 'Segoe UI', sans-serif; text-shadow: 2px 2px 4px rgba(0,0,0,0.9); }}
    button[kind="primaryFormSubmit"], .stButton > button {{
        width: 100% !important; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: black !important; font-size: 22px !important; font-weight: bold !important; padding: 15px !important;
        border-radius: 15px !important; border: none !important; box-shadow: 0px 4px 15px rgba(0,0,0,0.5) !important;
    }}
    div[data-testid="stForm"] {{ background: rgba(0, 0, 0, 0.7) !important; backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2); }}
    .info-box {{ background: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 15px; border-left: 5px solid #92FE9D; margin-bottom: 20px; }}
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
            # YO'RIQNOMA (SOZLAMALAR)
            st.markdown("""
            <div class="info-box">
                <h4>📝 O'quvchilar diqqatiga:</h4>
                <ul>
                    <li>Ism-familiyangizni to'liq kiriting.</li>
                    <li>Fan tanlangach, vaqt avtomatik hisoblanadi.</li>
                    <li>Testni faqat <b>bir marta</b> topshirish mumkin.</li>
                    <li>Natijangiz avtomatik ravishda bazaga saqlanadi.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            u_name = st.text_input("Ism-familiyangizni kiriting:", placeholder="Masalan: Ali Valiyev").strip()
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
        <div style="text-align: center; padding: 20px; background: rgba(0,0,0,0.8); border-radius: 15px; border: 2px solid #92FE9D;">
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
                
                # Natijalarni yuborish va saqlash
                send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, total, ball)
                save_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, total, ball)
                
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
        
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.8); padding: 40px; border-radius: 25px; border: 2px solid #92FE9D; text-align: center; margin-top: 20px;">
            <h2 style="color: white; margin-bottom: 10px;">📚 Fan: {res['subject']}</h2>
            <h1 style="color: #92FE9D; font-size: 50px; margin: 20px 0;">{res['ball']}%</h1>
            <p style="font-size: 24px; color: white;">To'g'ri javoblar: <b>{res['score']} / {res['total']}</b></p>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2); margin: 30px 0;">
            <p style="color: #FFD700; font-size: 18px;">✅ Natijangiz saqlandi va ustozga yuborildi.</p>
        </div>
        """, unsafe_allow_html=True)
