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

# --- 2. VIZUAL SERTIFIKAT FUNKSIYASI ---
def create_certificate(name, score, subject):
    # Sertifikat o'lchami va foni (To'q ko'k)
    W, H = 1000, 700
    img = Image.new('RGB', (W, H), color=(10, 30, 60))
    draw = ImageDraw.Draw(img)
    
    # DIZAYN ELEMENTLARI: Oltin hoshiyalar
    # Tashqi qalin chiziq
    draw.rectangle([25, 25, 975, 675], outline=(212, 175, 55), width=3)
    # Ichki burchak bezaklari (ikki qavatli ramka)
    draw.rectangle([45, 45, 955, 655], outline=(212, 175, 55), width=1)
    
    # Burchaklardagi geometrik bezaklar (Vizualdagi kabi)
    margin = 45
    length = 100
    # To'rt burchakda oltin burchakliklar
    draw.line([(margin, margin), (margin + length, margin)], fill=(212, 175, 55), width=8)
    draw.line([(margin, margin), (margin, margin + length)], fill=(212, 175, 55), width=8)
    
    draw.line([(W-margin, margin), (W-margin-length, margin)], fill=(212, 175, 55), width=8)
    draw.line([(W-margin, margin), (W-margin, margin+length)], fill=(212, 175, 55), width=8)
    
    draw.line([(margin, H-margin), (margin+length, H-margin)], fill=(212, 175, 55), width=8)
    draw.line([(margin, H-margin), (margin, H-margin-length)], fill=(212, 175, 55), width=8)
    
    draw.line([(W-margin, H-margin), (W-margin-length, H-margin)], fill=(212, 175, 55), width=8)
    draw.line([(W-margin, H-margin), (W-margin, H-margin-length)], fill=(212, 175, 55), width=8)

    try:
        font_path = "Montserrat-Bold.ttf"
        f_title = ImageFont.truetype(font_path, 80)
        f_name = ImageFont.truetype(font_path, 75)
        f_info = ImageFont.truetype(font_path, 35)
        f_small = ImageFont.truetype(font_path, 25)
    except:
        f_title = f_name = f_info = f_small = ImageFont.load_default()

    # 1. LOGOTIPNI JOYLASHTIRISH
    try:
        logo = Image.open("logo.png").convert("RGBA")
        logo = logo.resize((130, 130))
        img.paste(logo, (100, 80), logo)
    except:
        draw.rectangle([100, 80, 230, 210], outline="white")
        draw.text((115, 130), "LOGO", fill="white", font=f_small)

    # 2. MATNLAR (Oltin va oq ranglar uyg'unligi)
    draw.text((W/2, 180), "SERTIFIKAT", fill=(212, 175, 55), font=f_title, anchor="mm")
    draw.text((W/2, 280), "Ushbu hujjat egasi:", fill="white", font=f_info, anchor="mm")
    
    # Ism ostiga chiziq
    draw.text((W/2, 380), name.upper(), fill=(212, 175, 55), font=f_name, anchor="mm")
    draw.line([(300, 430), (700, 430)], fill=(212, 175, 55), width=2)
    
    draw.text((W/2, 500), f"FAN: {subject.upper()}", fill="white", font=f_info, anchor="mm")
    draw.text((W/2, 560), f"NATIJA: {score}", fill=(100, 255, 100), font=f_info, anchor="mm")

    # 3. IMZO VA DIREKTOR
    try:
        sig = Image.open("signature.png").convert("RGBA")
        sig = sig.resize((220, 110))
        # Imzoni ism ustiga biroz tushirib joylashtiramiz
        img.paste(sig, (650, 520), sig)
    except:
        draw.line((650, 610, 900, 610), fill="white", width=1)

    draw.text((650, 620), "Direktor: Normurodov Izzatillo", fill="white", font=f_small)
    draw.text((100, 620), f"Sana: {time.strftime('%d.%m.%Y')}", fill="gray", font=f_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 3. ILOVA MANTIQI ---
if 'cert_file' not in st.session_state:
    st.session_state.cert_file = None

st.title("🎓 Smart Test Masters Pro")

# Sidebar
st.sidebar.title("🔐 Nazorat")
admin_pass = st.sidebar.text_input("Admin paroli:", type="password")

df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
if not df.empty:
    user_name = st.text_input("Ism-familiyangizni kiriting:")
    subject = st.selectbox("Fanni tanlang:", df['Fan'].unique())

    if user_name and subject:
        with st.form("test_form"):
            q_df = df[df['Fan'] == subject].sample(n=min(10, len(df[df['Fan']==subject])))
            user_ans = {}
            for i, (idx, row) in enumerate(q_df.iterrows()):
                st.markdown(f"**{i+1}. {row['Savol']}**")
                user_ans[idx] = st.radio("Javobingiz:", [row['A'], row['B'], row['C'], row['D']], key=f"q_{idx}")
            
            if st.form_submit_button("Testni yakunlash"):
                score_count = sum(1 for idx, row in q_df.iterrows() if str(user_ans[idx]) == str(row['Javob']))
                # Sertifikat yaratish va saqlash
                st.session_state.cert_file = create_certificate(user_name, f"{score_count}/{len(q_df)}", subject)
                st.balloons()

# --- 4. NATIJANI KO'RSATISH ---
if st.session_state.cert_file:
    st.image(st.session_state.cert_file, use_container_width=True)
    
    if admin_pass == "Izzat06":
        st.sidebar.success("Xush kelibsiz, Izzatillo!")
        st.download_button(
            label="📥 Sertifikatni yuklab olish",
            data=st.session_state.cert_file,
            file_name=f"Sertifikat_{user_name}.png",
            mime="image/png"
        )
    else:
        st.sidebar.info("Yuklab olish tugmasi uchun parolni kiriting.")
