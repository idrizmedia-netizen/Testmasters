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

# --- DIZAYN VA STIL ---
def apply_styles(subject="Default"):
    bg_images = {
        "Matematika": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2000",
        "Fizika": "https://images.unsplash.com/photo-1636466484292-78351adcb72e?q=80&w=2000",
        "Informatika": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2000",
        "Default": "https://images.unsplash.com/photo-1510070112810-d4e9a46d9e91?q=80&w=2000"
    }
    bg_url = bg_images.get(subject, bg_images["Default"])
    
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{bg_url}") no-repeat center center fixed !important;
        background-size: cover !important;
        font-family: 'Inter', sans-serif;
    }}
    .main-card {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    div.stButton > button {{
        width: 100%;
        background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #001f3f !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        border: none !important;
        padding: 18px !important;
        text-transform: uppercase;
        transition: 0.4s;
    }}
    .stRadio div[role="radiogroup"] {{
        background: rgba(255, 255, 255, 0.08);
        padding: 15px;
        border-radius: 12px;
    }}
    .timer-card {{
        background: rgba(0, 0, 0, 0.8);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border-bottom: 4px solid #00C9FF;
    }}
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: rgba(255,255,255,0.1) !important;
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNKSIYALAR ---
@st.cache_data(ttl=60)
def load_questions():
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['Fan', 'Savol'], how='all')
        return df
    except Exception as e:
        st.error(f"Xatolik: {e}")
        return None

def check_already_finished(name, subject):
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        df.columns = [str(c).strip() for c in df.columns]
        if df.empty: return False
        exists = df[(df['Ism-familiya'].astype(str).str.strip().str.lower() == name.strip().lower()) & 
                    (df['Fan'].astype(str).str.strip().str.lower() == subject.strip().lower())]
        return not exists.empty
    except: return False

def save_result_to_sheets(name, subject, corrects, total, ball):
    try:
        new_row = pd.DataFrame([{
            "Sana": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ism-familiya": name,
            "Fan": subject,
            "To'g'ri": corrects,
            "Xato": total - corrects,
            "Ball (%)": f"{ball}%"
        }])
        existing_df = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Results", data=updated_df)
    except Exception as e:
        st.error(f"Saqlashda xatolik: {e}")

def send_to_telegram(name, subject, corrects, total, ball):
    text = f"🏆 YANGI NATIJA!\n👤: {name}\n📚: {subject}\n✅: {corrects}\n❌: {total-corrects}\n📊: {ball}%"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except: pass

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "HOME"

main_container = st.empty()

# 1. NATIJA EKRANI
if st.session_state.page == "RESULT":
    with main_container.container():
        apply_styles()
        res = st.session_state.final_score
        st.balloons()
        st.markdown(f"""
            <div class="main-card" style="text-align:center;">
                <h1 style="color:#92FE9D; font-size:100px; margin:0;">{res['ball']}%</h1>
                <h2 style="margin-bottom:5px;">{res['name']}</h2>
                <p style="font-size:20px; opacity:0.8;">Natijangiz tizimga muvaffaqiyatli saqlandi!</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"):
            st.session_state.page = "HOME"
            st.rerun()

# 2. TEST TOPSHIRISH EKRANI
elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    
    with main_container.container():
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, int(st.session_state.total_time - elapsed))
        
        st.sidebar.markdown(f'''
            <div class="timer-card">
                <h1 style="color:#00C9FF; margin:0; font-size:45px;">{rem//60:02d}:{rem%60:02d}</h1>
                <p style="margin:0; font-weight:bold; letter-spacing:2px;">VAQT QOLDI</p>
            </div>
        ''', unsafe_allow_html=True)
        st.sidebar.markdown(f"**👤 Foydalanuvchi:** {st.session_state.full_name}")
        st.sidebar.markdown(f"**📚 Fan:** {st.session_state.selected_subject}")

        if rem <= 0:
            st.error("⌛ Vaqt tugadi!")
            st.session_state.page = "HOME"
            st.rerun()

        with st.form("quiz_form", clear_on_submit=True):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.markdown(f"""<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:10px;">
                    <h4 style="margin:0;">{i+1}. {item['q']}</h4>
                </div>""", unsafe_allow_html=True)
                user_answers[i] = st.radio("Javob:", item['o'], index=None, key=f"q_{i}", label_visibility="collapsed")
            
            submit = st.form_submit_button("🏁 TESTNI TUGATISH")
            
            if submit:
                if None in user_answers.values():
                    st.error("⚠️ Iltimos, barcha savollarni belgilang!")
                else:
                    corrects = 0
                    for i, item in enumerate(st.session_state.test_items):
                        u_ans = str(user_answers[i]).strip().lower()
                        db_ans = str(item['c']).strip().lower() # Jadvaldagi Javob ustuni
                        
                        # TEKSHIRISH MANTIG'I:
                        # 1. Matnli moslik (Masalan: "4" == "4")
                        # 2. Harfli moslik (Masalan: "A" deb yozilgan bo'lsa, A variantdagi matnni olib tekshiradi)
                        if u_ans == db_ans:
                            corrects += 1
                        elif db_ans.upper() in item['map'] and u_ans == str(item['map'][db_ans.upper()]).lower():
                            corrects += 1

                    ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                    save_result_to_sheets(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                    send_to_telegram(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)
                    st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball}
                    st.session_state.page = "RESULT"
                    st.rerun()
        
        time.sleep(1)
        st.rerun()

# 3. KIRISH EKRANI
elif st.session_state.page == "HOME":
    apply_styles()
    with main_container.container():
        st.markdown("<h1 style='text-align:center; font-size:50px;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
        st.markdown('''<div class="main-card">
            <h3 style="margin-top:0; color:#00C9FF;">📝 Yo'riqnoma:</h3>
            <p style="font-size:17px; line-height:1.6;">
                1️⃣ Ism-familiyangizni kiriting va fanni tanlang.<br>
                2️⃣ <b>"Testni boshlash"</b> tugmasini bosing.<br>
                3️⃣ Tizim harfli (A, B) yoki matnli javoblarni avtomat aniqlaydi.
            </p>
        </div>''', unsafe_allow_html=True)
        
        u_name = st.text_input("Ism-familiyangiz:", placeholder="Masalan: Ali Valiyev")
        q_df = load_questions()
        
        if q_df is not None and 'Fan' in q_df.columns:
            all_subs = sorted(q_df['Fan'].dropna().unique().tolist())
            selected_subject = st.selectbox("Fanni tanlang:", all_subs)

            if st.button("🚀 TESTNI BOSHLASH"):
                if not u_name:
                    st.error("⚠️ Ism-familiyangizni yozing!")
                elif check_already_finished(u_name, selected_subject):
                    st.error(f"❌ {u_name}, siz bu fandan test topshirib bo'lgansiz!")
                else:
                    sub_qs = q_df[q_df['Fan'] == selected_subject].copy()
                    if not sub_qs.empty:
                        selected_qs = sub_qs.sample(n=min(len(sub_qs), 30))
                        test_items = []
                        for _, row in selected_qs.iterrows():
                            # Variantlarni xaritaga yuklash (A, B, C, D)
                            mapping = {
                                'A': str(row.get('A','')),
                                'B': str(row.get('B','')),
                                'C': str(row.get('C','')),
                                'D': str(row.get('D',''))
                            }
                            opts = [v for v in mapping.values() if v != 'nan' and v != '']
                            random.shuffle(opts)
                            test_items.append({
                                "q": row['Savol'], 
                                "o": opts, 
                                "c": str(row['Javob']),
                                "map": mapping
                            })
                        
                        st.session_state.update({
                            "full_name": u_name,
                            "selected_subject": selected_subject,
                            "test_items": test_items,
                            "total_time": len(test_items) * 30,
                            "start_time": time.time(),
                            "page": "TEST"
                        })
                        st.rerun()
