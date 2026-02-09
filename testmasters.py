import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="Smart Test Masters Pro", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

# --- SERTIFIKAT FUNKSIYASI ---
def create_certificate(name, score, subject):
    W, H = 1000, 700
    img = Image.new('RGB', (W, H), color=(10, 30, 60))
    draw = ImageDraw.Draw(img)
    # (Avvalgi vizual dizayn kodlari shu yerda qoladi...)
    draw.rectangle([25, 25, 975, 675], outline=(212, 175, 55), width=3)
    try:
        font_path = "Montserrat-Bold.ttf"
        f_title = ImageFont.truetype(font_path, 80)
        f_name = ImageFont.truetype(font_path, 75)
        f_info = ImageFont.truetype(font_path, 35)
    except:
        f_title = f_name = f_info = ImageFont.load_default()
    
    draw.text((W/2, 180), "SERTIFIKAT", fill=(212, 175, 55), font=f_title, anchor="mm")
    draw.text((W/2, 380), name.upper(), fill=(212, 175, 55), font=f_name, anchor="mm")
    draw.text((W/2, 500), f"FAN: {subject.upper()} | NATIJA: {score}", fill="white", font=f_info, anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- MA'LUMOTLARNI YUKLASH ---
@st.cache_data(ttl=5)
def get_data():
    questions = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    settings = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    users = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    return questions, settings, users

questions_df, settings_df, users_df = get_data()

st.title("🎓 Smart Test Masters Pro")

# Sidebar - Admin
st.sidebar.title("🔐 Admin")
admin_pass = st.sidebar.text_input("Parol:", type="password")

# 1. Ruxsat berilgan fanni aniqlash
active_subject = settings_df.loc[settings_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]

# 2. Foydalanuvchi tekshiruvi
user_name = st.text_input("Ism-familiyangizni kiriting:").strip()

if user_name:
    # Avval topshirganmi?
    if user_name in users_df['Ism'].values:
        st.error(f"Hurmatli {user_name}, siz bu testni topshirib bo'lgansiz! Qayta kirish taqiqlangan.")
    else:
        st.info(f"Hozirgi faol fan: **{active_subject}**")
        
        if st.button("Testni boshlash"):
            st.session_state.start_test = True

        if st.session_state.get('start_test'):
            with st.form("test_form"):
                # 30 ta tasodifiy savol tanlash
                subject_questions = questions_df[questions_df['Fan'] == active_subject]
                q_count = min(30, len(subject_questions))
                q_df = subject_questions.sample(n=q_count)
                
                user_ans = {}
                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    user_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], key=f"q_{idx}")
                
                if st.form_submit_button("Yakunlash"):
                    score = sum(1 for idx, row in q_df.iterrows() if str(user_ans[idx]) == str(row['Javob']))
                    
                    # Natijani saqlash va foydalanuvchini bloklash
                    new_user = pd.DataFrame([{"Ism": user_name}])
                    updated_users = pd.concat([users_df, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_users, worksheet="Users")
                    
                    st.session_state.cert_file = create_certificate(user_name, f"{score}/{q_count}", active_subject)
                    st.success("Test yakunlandi!")

# Natijani ko'rsatish
if st.session_state.get('cert_file'):
    st.image(st.session_state.cert_file)
    if admin_pass == "Izzat06":
        st.download_button("📥 Yuklab olish", st.session_state.cert_file, "Sertifikat.png")
