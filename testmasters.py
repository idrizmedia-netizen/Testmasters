import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="Smart Test Masters Pro", layout="centered")

# 1. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit"

# --- 2. PROFESSIONAL SERTIFIKAT FUNKSIYASI ---
def create_certificate(name, score_text, subject):
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), color=(10, 30, 60))
    draw = ImageDraw.Draw(img)
    
    # Oltin ramkalar
    draw.rectangle([30, 30, 1170, 820], outline=(212, 175, 55), width=15)
    draw.rectangle([55, 55, 1145, 795], outline=(212, 175, 55), width=2)

    try:
        font_path = "Montserrat-Bold.ttf"
        f_large = ImageFont.truetype(font_path, 100)
        f_name = ImageFont.truetype(font_path, 80)
        f_text = ImageFont.truetype(font_path, 35)
        f_quote = ImageFont.truetype(font_path, 28)
        f_dir = ImageFont.truetype(font_path, 30)
    except:
        f_large = f_name = f_text = f_quote = f_dir = ImageFont.load_default()

    # Logotip
    try:
        logo = Image.open("logo.png").convert("RGBA").resize((150, 150))
        img.paste(logo, (100, 100), logo)
    except: pass

    # Matnlar
    draw.text((W/2, 180), "SERTIFIKAT", fill=(212, 175, 55), font=f_large, anchor="mm")
    draw.text((W/2, 280), "BILIM VA MAHORAT UCHUN MUNOSIB TAQDIRLANADI", fill="white", font=f_text, anchor="mm")
    draw.text((W/2, 400), name.upper(), fill=(212, 175, 55), font=f_name, anchor="mm")
    
    motivation = f"Ushbu o'quvchi '{subject}' fani bo'yicha o'tkazilgan\nsinovlarda o'zining yuksak bilimini namoyon etdi."
    draw.multiline_text((W/2, 530), motivation, fill="white", font=f_text, anchor="mm", align="center")
    draw.text((W/2, 630), f"NATIJA: {score_text}", fill=(100, 255, 100), font=f_text, anchor="mm")
    
    quote = "Bilim - eng qudratli quroldir, unga ega bo'ling!"
    draw.text((W/2, 690), quote, fill=(200, 200, 200), font=f_quote, anchor="mm")

    # Imzo va Direktor
    try:
        sig = Image.open("signature.png").convert("RGBA").resize((220, 110))
        img.paste(sig, (850, 680), sig)
    except: pass
    
    draw.text((850, 780), "Direktor: Normurodov I.", fill="white", font=f_dir)
    draw.text((100, 780), f"Sana: {time.strftime('%d.%m.%Y')}", fill="gray", font=f_dir)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. MA'LUMOTLAR VA TEST MANTIQI ---
if 'start_test' not in st.session_state: st.session_state.start_test = False
if 'cert_file' not in st.session_state: st.session_state.cert_file = None

# Ma'lumotlarni o'qish
try:
    questions_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    settings_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    users_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    active_subject = settings_df.loc[settings_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]
except:
    st.error("Google Sheets varaqlari (Questions, Settings, Users) to'g'ri sozlanganiga ishonch hosil qiling!")
    st.stop()

st.title("🎓 Smart Test Masters Pro")

# Sidebar - Admin
st.sidebar.title("🔐 Admin")
admin_pass = st.sidebar.text_input("Parol:", type="password")

user_name = st.text_input("Ism-familiyangizni kiriting:").strip()

if user_name:
    if user_name in users_df['Ism'].values:
        st.warning(f"⚠️ {user_name}, siz bu testni topshirib bo'lgansiz.")
    else:
        st.success(f"Fan: {active_subject}. Sertifikat olish uchun 20 tadan ko'p topishingiz kerak.")
        if st.button("Testni boshlash"):
            st.session_state.start_test = True

        if st.session_state.start_test:
            with st.form("test_form"):
                subject_questions = questions_df[questions_df['Fan'] == active_subject]
                q_count = min(30, len(subject_questions))
                q_df = subject_questions.sample(n=q_count)
                
                user_ans = {}
                for i, (idx, row) in enumerate(q_df.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    user_ans[idx] = st.radio("Javob:", [row['A'], row['B'], row['C'], row['D']], key=f"q_{idx}")
                
                if st.form_submit_button("Testni yakunlash"):
                    score = sum(1 for idx, row in q_df.iterrows() if str(user_ans[idx]) == str(row['Javob']))
                    
                    # Natijani saqlash
                    new_user = pd.DataFrame([{"Ism": user_name}])
                    updated_users = pd.concat([users_df, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_users, worksheet="Users")
                    
                    # --- SERTIFIKAT SHARTI (20+ ball) ---
                    if score > 20:
                        st.session_state.cert_file = create_certificate(user_name, f"{score}/{q_count}", active_subject)
                        st.balloons()
                    else:
                        st.error(f"Natijangiz: {score}/{q_count}. Sertifikat uchun ball yetarli emas (Kamida 21 ta kerak).")
                    
                    st.session_state.start_test = False

# Natijani ko'rsatish
if st.session_state.cert_file:
    st.image(st.session_state.cert_file)
    if admin_pass == "Izzat06":
        st.download_button("📥 Yuklab olish", st.session_state.cert_file, "Sertifikat.png")
