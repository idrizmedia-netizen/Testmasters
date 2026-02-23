import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
import random
from datetime import datetime
import threading  # Asinxron yuborish uchun
import plotly.express as px  # Interaktiv grafiklar uchun

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SOZLAMALAR
try:
    TELEGRAM_TOKEN = st.secrets["general"]["telegram_token"]
    CHAT_ID = st.secrets["general"]["chat_id"]
    SHEET_URL = st.secrets["general"]["sheet_url"]
    ADMIN_PASS = st.secrets["general"]["admin_password"]
except KeyError:
    st.error("Secrets.toml fayli noto'g'ri sozlangan yoki topilmadi!")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)

# --- ASINXRON FUNKSIYA (FONDA ISHLAYDI) ---
def background_tasks(name, subject, corrects, total, ball):
    # 1. Sheetsga saqlash
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
    except: pass

    # 2. Telegramga yuborish
    text = f"🏆 YANGI NATIJA!\n👤: {name}\n📚: {subject}\n✅: {corrects}\n❌: {total-corrects}\n📊: {ball}%"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except: pass

# --- AUDIO FUNKSIYALAR ---
def play_audio(sound_type="success"):
    urls = {
        "success": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
        "fail": "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    }
    st.markdown(f'<audio src="{urls[sound_type]}" autoplay></audio>', unsafe_allow_html=True)

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
    .analysis-card {{
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid;
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
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; }}
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

def show_admin_panel():
    st.markdown("<h2 style='text-align:center;'>📊 Boshqaruv va Statistika</h2>", unsafe_allow_html=True)
    try:
        res_df = conn.read(spreadsheet=SHEET_URL, worksheet="Results")
        res_df.columns = [str(c).strip() for c in res_df.columns]
        if res_df.empty:
            st.info("Hozircha hech qanday natija yo'q.")
        else:
            # Ma'lumotlarni tayyorlash
            res_df['BallNum'] = res_df['Ball (%)'].str.replace('%', '').astype(float)
            
            # 1. Metrikalar
            m1, m2, m3 = st.columns(3)
            m1.metric("Jami urinishlar", len(res_df))
            m2.metric("O'rtacha natija", f"{res_df['BallNum'].mean():.1f}%")
            m3.metric("Eng yuqori ball", f"{res_df['BallNum'].max()}%")
            
            st.markdown("---")
            
            # 2. Plotly Grafiklari
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🥧 Fanlar ulushi")
                fan_counts = res_df['Fan'].value_counts().reset_index()
                fan_counts.columns = ['Fan', 'Soni']
                fig1 = px.pie(fan_counts, values='Soni', names='Fan', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig1.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', 
                                 plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.markdown("### 📈 Ballar taqsimoti")
                fig2 = px.histogram(res_df, x="BallNum", nbins=10, 
                                   color_discrete_sequence=['#92FE9D'])
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                 font=dict(color="white"), xaxis_title="Ball", yaxis_title="Soni")
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### 📋 To'liq natijalar")
            st.dataframe(res_df.drop(columns=['BallNum']), use_container_width=True)
    except Exception as e:
        st.error(f"Admin panel yuklashda xatolik: {e}")

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "HOME"
if 'user_logs' not in st.session_state: st.session_state.user_logs = []

main_container = st.empty()

# --- SIDEBAR ADMIN LOGIN ---
st.sidebar.markdown("---")
with st.sidebar.expander("🔐 Admin Panel"):
    password = st.text_input("Parol:", type="password")
    if password == ADMIN_PASS:
        if st.button("Kirish"):
            st.session_state.page = "ADMIN"
            st.rerun()

# 1. ADMIN SAHIFASI
if st.session_state.page == "ADMIN":
    apply_styles()
    with main_container.container():
        if st.button("⬅️ ASOSIY SAHIFAGA QAYTISH"):
            st.session_state.page = "HOME"
            st.rerun()
        show_admin_panel()

# 2. NATIJA EKRANI + TAHLIL
elif st.session_state.page == "RESULT":
    with main_container.container():
        apply_styles()
        res = st.session_state.final_score
        
        if res['ball'] >= 60:
            st.balloons()
            play_audio("success")
        else:
            play_audio("fail")

        st.markdown(f"""
            <div class="main-card" style="text-align:center;">
                <h1 style="color:#92FE9D; font-size:100px; margin:0;">{res['ball']}%</h1>
                <h2 style="margin-bottom:5px;">{res['name']}</h2>
                <p style="font-size:20px; opacity:0.8;">Natijangiz tizimga saqlandi!</p>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Xatolar ustida ishlash (Batafsil tahlil)"):
            for log in st.session_state.user_logs:
                border_color = "#92FE9D" if log['correct'] else "#FF4B4B"
                st.markdown(f"""
                    <div class="analysis-card" style="border-left-color: {border_color};">
                        <p style="margin:0;"><b>Savol:</b> {log['question']}</p>
                        <p style="margin:0; color:{border_color};"><b>Sizning javobingiz:</b> {log['user_ans']}</p>
                        <p style="margin:0; color:#92FE9D;"><b>To'g'ri javob:</b> {log['correct_ans']}</p>
                    </div>
                """, unsafe_allow_html=True)

        if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"):
            st.session_state.page = "HOME"
            st.rerun()

# 3. TEST TOPSHIRISH EKRANI
elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    with main_container.container():
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, int(st.session_state.total_time - elapsed))
        total_qs = len(st.session_state.test_items)
        
        st.sidebar.markdown(f'''<div class="timer-card"><h1 style="color:#00C9FF; margin:0; font-size:45px;">{rem//60:02d}:{rem%60:02d}</h1><p style="margin:0; font-weight:bold;">VAQT QOLDI</p></div>''', unsafe_allow_html=True)
        
        if rem <= 0:
            st.error("⌛ Vaqt tugadi!")
            st.session_state.page = "HOME"
            st.rerun()

        with st.form("quiz_form", clear_on_submit=True):
            user_answers = {}
            for i, item in enumerate(st.session_state.test_items):
                st.markdown(f"**{i+1}. {item['q']}**")
                
                if item.get('image') and str(item['image']) != 'nan':
                    st.image(item['image'], use_container_width=True)
                
                user_answers[i] = st.radio("Javob:", item['o'], index=None, key=f"q_{i}", label_visibility="collapsed")
                st.markdown("---")
            
            submit = st.form_submit_button("🏁 TESTNI TUGATISH")
            
            if submit:
                if None in user_answers.values():
                    st.error("⚠️ Iltimos, barcha savollarni belgilang!")
                else:
                    corrects = 0
                    logs = []
                    for i, item in enumerate(st.session_state.test_items):
                        u_ans = str(user_answers[i]).strip().lower()
                        db_ans_key = str(item['c']).strip().upper()
                        correct_text = item['map'].get(db_ans_key, str(item['c']))
                        is_right = (u_ans == str(correct_text).lower()) or (u_ans == str(item['c']).lower())
                        if is_right: corrects += 1
                        logs.append({"question": item['q'], "user_ans": user_answers[i], "correct_ans": correct_text, "correct": is_right})

                    ball = round((corrects / total_qs) * 100, 1)
                    st.session_state.user_logs = logs
                    st.session_state.final_score = {"name": st.session_state.full_name, "ball": ball}

                    thread = threading.Thread(target=background_tasks, args=(
                        st.session_state.full_name, 
                        st.session_state.selected_subject, 
                        corrects, total_qs, ball
                    ))
                    thread.start()

                    st.session_state.page = "RESULT"
                    st.rerun()
        
        answered_count = sum(1 for v in user_answers.values() if v is not None)
        st.sidebar.write(f"To'ldirildi: {answered_count}/{total_qs}")
        st.sidebar.progress(answered_count / total_qs)
        
        time.sleep(1)
        st.rerun()

# 4. KIRISH EKRANI
elif st.session_state.page == "HOME":
    apply_styles()
    with main_container.container():
        st.markdown("<h1 style='text-align:center; font-size:50px;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
        st.markdown('''<div class="main-card"><h3 style="margin-top:0; color:#00C9FF;">📝 Yo'riqnoma:</h3><p style="font-size:17px;">1️⃣ Ism-familiyangizni kiriting.<br>2️⃣ Fanni tanlab testni boshlang.</p></div>''', unsafe_allow_html=True)
        u_name = st.text_input("Ism-familiyangiz:", placeholder="Masalan: Ali Valiyev")
        q_df = load_questions()
        if q_df is not None:
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
                            mapping = {'A': str(row.get('A','')), 'B': str(row.get('B','')), 'C': str(row.get('C','')), 'D': str(row.get('D',''))}
                            opts = [v for v in mapping.values() if v != 'nan' and v != '']
                            random.shuffle(opts)
                            test_items.append({
                                "q": row['Savol'], "o": opts, "c": str(row['Javob']), 
                                "map": mapping, "image": row.get('Rasm') 
                            })
                        st.session_state.update({"full_name": u_name, "selected_subject": selected_subject, "test_items": test_items, "total_time": len(test_items) * 45, "start_time": time.time(), "page": "TEST", "user_logs": []})
                        st.rerun()
