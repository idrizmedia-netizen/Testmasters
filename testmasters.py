import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import requests
import random
from datetime import datetime
import threading

# 1. SAHIFA SOZLAMALARI
st.set_page_config(page_title="Testmasters Online", page_icon="🎓", layout="centered")

# 2. SECRETS VA ULANISH
try:
    TELEGRAM_TOKEN = st.secrets["general"]["telegram_token"]
    CHAT_ID = st.secrets["general"]["chat_id"]
    ADMIN_PASS = st.secrets["general"]["admin_password"]
    # Ulanishni yaratish
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Sozlamalarda xatolik: {e}")
    st.stop()

# --- 3. YORDAMCHI FUNKSIYALAR ---

def check_already_finished(name, subject):
    """Foydalanuvchi avval topshirganini tekshirish"""
    try:
        df = conn.read(worksheet="Results", ttl=0)
        if df is not None and not df.empty:
            # Ustun nomlarini tozalash
            df.columns = [str(c).strip() for c in df.columns]
            exists = df[(df['Ism-familiya'] == name) & (df['Fan'] == subject)]
            return len(exists) > 0
    except: return False
    return False

def background_tasks(name, subject, corrects, total, ball):
    """Ma'lumotlarni yozish va Telegramga yuborish"""
    try:
        new_row = pd.DataFrame([{
            "Sana": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ism-familiya": name,
            "Fan": subject,
            "To'g'ri": corrects,
            "Xato": total - corrects,
            "Ball (%)": f"{ball}%"
        }])
        existing_df = conn.read(worksheet="Results", ttl=0)
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        conn.update(worksheet="Results", data=updated_df)
    except: pass

    text = f"🏆 YANGI NATIJA!\n👤: {name}\n📚: {subject}\n✅: {corrects}\n❌: {total-corrects}\n📊: {ball}%"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except: pass

@st.cache_data(ttl=0)
def load_questions():
    try:
        # worksheet nomini aniq ko'rsatamiz
        df = conn.read(worksheet="Questions", ttl=0) 
        
        if df is None or df.empty:
            return None
        
        # Ustun nomlaridagi bo'shliqlarni tozalash
        df.columns = [str(c).strip() for c in df.columns]
        
        # Kerakli ustunlar borligini tekshirish
        required = {"Fan", "Savol", "A", "B", "C", "D", "Javob"}
        if not required.issubset(set(df.columns)):
            st.error(f"Xato! Jadvalda mana bu ustunlar bo'lishi shart: {required}")
            return None
            
        return df.dropna(subset=["Fan", "Savol"])
    except Exception as e:
        # Agar bu yerda xato chiqsa, demak Secrets-dagi ID hali ham noto'g'ri
        st.error(f"Google Sheets bilan aloqa bog'lanmadi: {e}")
        return None
            
        return df.dropna(subset=["Fan", "Savol"], how="any")
    except Exception as e:
        st.error(f"Xatolik: {e}")
        return None
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
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{bg_url}") no-repeat center center fixed !important; background-size: cover !important; font-family: 'Inter', sans-serif; }}
    .main-card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 20px; }}
    .analysis-card {{ background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid; }}
    div.stButton > button {{ width: 100%; background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important; color: #001f3f !important; font-size: 20px !important; font-weight: 800 !important; border-radius: 15px !important; border: none !important; padding: 18px !important; text-transform: uppercase; }}
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. TAYMER ---
@st.fragment(run_every=1.0)
def timer_component():
    if st.session_state.get('page') == "TEST" and 'start_time' in st.session_state:
        elapsed = time.time() - st.session_state.start_time
        rem = max(0, int(st.session_state.total_time - elapsed))
        st.sidebar.markdown(f'''
            <div style="background: rgba(0,201,255,0.1); padding:15px; border-radius:15px; border: 1px solid #00C9FF; text-align:center;">
                <h1 style="color:#00C9FF; margin:0; font-size:40px;">{rem//60:02d}:{rem%60:02d}</h1>
                <p style="color:white; margin:0; font-weight:bold; font-size:12px;">VAQT QOLDI</p>
            </div>
        ''', unsafe_allow_html=True)
        if rem <= 0:
            st.session_state.page = "HOME"
            st.rerun()

# --- 5. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "HOME"
if 'user_logs' not in st.session_state: st.session_state.user_logs = []

# --- 6. SIDEBAR ADMIN ---
st.sidebar.markdown("---")
with st.sidebar.expander("🔐 Admin Panel"):
    password = st.text_input("Parol:", type="password", key="admin_pwd_input")
    if password == ADMIN_PASS and st.button("Kirish", key="admin_login_btn"):
        st.session_state.page = "ADMIN"
        st.rerun()

# --- 7. SAHIFALAR ---

# ADMIN SAHIFA
if st.session_state.page == "ADMIN":
    apply_styles()
    st.title("📊 Natijalar (Admin)")
    if st.button("⬅️ QAYTISH"):
        st.session_state.page = "HOME"; st.rerun()
    
    try:
        res_df = conn.read(worksheet="Results", ttl=0)
        st.dataframe(res_df, use_container_width=True)
    except: st.error("Natijalarni yuklab bo'lmadi.")

# NATIJA SAHIFA
elif st.session_state.page == "RESULT":
    apply_styles()
    res = st.session_state.final_score
    st.markdown(f'<div class="main-card" style="text-align:center;"><h1 style="color:#92FE9D; font-size:100px; margin:0;">{res["ball"]}%</h1><h2>{res["name"]}</h2></div>', unsafe_allow_html=True)
    
    with st.expander("🔍 Batafsil tahlil"):
        for log in st.session_state.user_logs:
            border_color = "#92FE9D" if log['correct'] else "#FF4B4B"
            st.markdown(f'<div class="analysis-card" style="border-left-color: {border_color};"><p><b>Savol:</b> {log["question"]}</p><p style="color:{border_color};">Javobingiz: {log["user_ans"]}</p></div>', unsafe_allow_html=True)
            
    if st.button("🔄 ASOSIY SAHIFAGA QAYTISH"):
        st.session_state.page = "HOME"; st.rerun()

# TEST SAHIFA
elif st.session_state.page == "TEST":
    apply_styles(st.session_state.selected_subject)
    timer_component()
    st.markdown(f"### 📚 Fan: {st.session_state.selected_subject}")
    
    with st.form(key="quiz_form"):
        user_answers = {}
        for i, item in enumerate(st.session_state.test_items):
            st.markdown(f"**{i+1}. {item['q']}**")
            if item.get('image') and str(item['image']) != 'nan':
                st.image(item['image'])
            
            user_answers[i] = st.radio("Tanlang:", item['o'], index=None, key=f"q_{i}")
            st.markdown("---")
            
        if st.form_submit_button("🏁 TESTNI TUGATISH"):
            if None in user_answers.values():
                st.error("⚠️ Barcha savollarni belgilang!")
            else:
                corrects = 0
                logs = []
                for i, item in enumerate(st.session_state.test_items):
                    db_ans_key = str(item['c']).strip().upper()
                    correct_text = item['map'].get(db_ans_key, str(item['c']))
                    is_right = str(user_answers[i]).lower() == str(correct_text).lower()
                    if is_right: corrects += 1
                    logs.append({"question": item['q'], "user_ans": user_answers[i], "correct": is_right})
                
                ball = round((corrects / len(st.session_state.test_items)) * 100, 1)
                st.session_state.update({"user_logs": logs, "final_score": {"name": st.session_state.full_name, "ball": ball}, "page": "RESULT"})
                threading.Thread(target=background_tasks, args=(st.session_state.full_name, st.session_state.selected_subject, corrects, len(st.session_state.test_items), ball)).start()
                st.rerun()

# ASOSIY SAHIFA
elif st.session_state.page == "HOME":
    apply_styles()
    st.markdown("<h1 style='text-align:center;'>🎓 Testmasters Online</h1>", unsafe_allow_html=True)
    u_name = st.text_input("Ism-familiyangiz:", key="user_name_input")
    
    q_df = load_questions()
    if q_df is not None and not q_df.empty:
        all_subs = sorted(q_df['Fan'].dropna().unique().tolist())
        selected_subject = st.selectbox("Fanni tanlang:", all_subs)
        
        if st.button("🚀 TESTNI BOSHLASH"):
            if not u_name: st.error("⚠️ Ism-familiyangizni yozing!")
            elif check_already_finished(u_name, selected_subject): st.error("❌ Siz topshirib bo'lgansiz!")
            else:
                sub_qs = q_df[q_df['Fan'] == selected_subject]
                if not sub_qs.empty:
                    sample_size = min(len(sub_qs), 30)
                    sampled_qs = sub_qs.sample(n=sample_size)
                    test_items = []
                    for _, row in sampled_qs.iterrows():
                        mapping = {'A': str(row.get('A','')), 'B': str(row.get('B','')), 'C': str(row.get('C','')), 'D': str(row.get('D',''))}
                        opts = [v for v in mapping.values() if v not in ['nan', '']]
                        random.shuffle(opts)
                        test_items.append({"q": row['Savol'], "o": opts, "c": row['Javob'], "map": mapping, "image": row.get('Rasm')})
                    
                    st.session_state.update({
                        "full_name": u_name, "selected_subject": selected_subject, 
                        "test_items": test_items, "total_time": len(test_items) * 45, 
                        "start_time": time.time(), "page": "TEST"
                    })
                    st.rerun()
    else:
        st.warning("⚠️ Fanlar yuklanmadi. Jadvalda 'Questions' varog'i va 'Fan' ustuni borligini tekshiring.")
