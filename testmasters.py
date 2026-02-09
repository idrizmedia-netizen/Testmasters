import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from PIL import Image, ImageDraw, ImageFont
import io

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Smart Test Masters Pro", layout="centered")

# 2. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

# --- 3. SERTIFIKAT YARATISH FUNKSIYASI ---
def create_certificate(name, score_text, subject):
    W, H = 1200, 850
    img = Image.new('RGB', (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    gold_color = (197, 160, 82) 
    draw.rectangle([60, 60, 1140, 790], outline=gold_color, width=2)
    offset, length = 60, 100
    for i in [(offset, offset, 1, 1), (W-offset, offset, -1, 1), (offset, H-offset, 1, -1), (W-offset, H-offset, -1, -1)]:
        draw.line([(i[0], i[1]), (i[0] + length*i[2], i[1])], fill=gold_color, width=12)
        draw.line([(i[0], i[1]), (i[0], i[1] + length*i[3])], fill=gold_color, width=12)

    try:
        font_path = "Montserrat-Bold.ttf"
        f_title = ImageFont.truetype(font_path, 100)
        f_sub = ImageFont.truetype(font_path, 30)
        f_name = ImageFont.truetype(font_path, 95)
        f_text = ImageFont.truetype(font_path, 35)
        f_dir = ImageFont.truetype(font_path, 32)
    except:
        f_title = f_sub = f_name = f_text = f_dir = ImageFont.load_default()

    try:
        logo = Image.open("logo.jpg").convert("RGBA").resize((150, 150))
        img.paste(logo, (int(W/2 - 75), 90), logo)
    except: pass

    draw.text((W/2, 290), "SERTIFIKAT", fill=(30, 30, 30), font=f_title, anchor="mm")
    draw.text((W/2, 460), name.upper(), fill=(30, 30, 30), font=f_name, anchor="mm")
    info_text = f"'{subject}' fani bo'yicha o'tkazilgan test sinovlarida\nyuqori natija ko'rsatgani uchun taqdirlanadi."
    draw.multiline_text((W/2, 580), info_text, fill=(60, 60, 60), font=f_text, anchor="mm", align="center")
    draw.text((W/2, 670), f"NATIJA: {score_text}", fill=(46, 125, 50), font=f_sub, anchor="mm")

    line_y = 760
    draw.line([(W/2 - 180, line_y), (W/2 + 180, line_y)], fill=gold_color, width=2)
    draw.text((W/2, line_y + 35), "Direktor: Normurodov Izzatillo", fill=(30, 30, 30), font=f_dir, anchor="mm")

    try:
        sig = Image.open("signature.jpg").convert("RGBA")
        sig = sig.resize((260, 130))
        img.paste(sig, (int(W/2 - 130), line_y - 110), sig)
    except: pass

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 4. ASOSIY MANTIQ ---
try:
    q_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    u_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    active_sub = s_df.loc[s_df['Parameter'] == 'ActiveSubject', 'Value'].values[0]
except:
    st.error("Ma'lumotlar bazasiga ulanishda xato!")
    st.stop()

if 'cert_file' not in st.session_state: st.session_state.cert_file = None
if 'test_run' not in st.session_state: st.session_state.test_run = False

u_name = st.text_input("Ism-familiyangiz:").strip()

if u_name:
    if u_name in u_df['Ism'].values:
        st.warning("Siz test topshirib bo'lgansiz!")
    else:
        if not st.session_state.test_run:
            if st.button("Testni boshlash"):
                st.session_state.test_run = True
                st.rerun()

        if st.session_state.test_run:
            with st.form("quiz_form"):
                f_qs = q_df[q_df['Fan'] == active_sub].sample(n=30)
                u_ans = {}
                
                for i, (idx, row) in enumerate(f_qs.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    # index=None qilib qo'yildi - bu doimiy bitta variant tanlanib qolishini oldini oladi
                    u_ans[idx] = st.radio(
                        "Javobni tanlang:", 
                        [row['A'], row['B'], row['C'], row['D']], 
                        index=None, 
                        key=f"q_{idx}"
                    )
                
                if st.form_submit_button("Testni yakunlash"):
                    # Javob berilmagan savollarni tekshirish
                    unanswered = [v for v in u_ans.values() if v is None]
                    if unanswered:
                        st.error("Iltimos, barcha savollarga javob bering!")
                    else:
                        corrects = sum(1 for idx, row in f_qs.iterrows() if str(u_ans[idx]) == str(row['Javob']))
                        new_u = pd.concat([u_df, pd.DataFrame([{"Ism": u_name}])], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=new_u, worksheet="Users")
                        
                        if corrects > 20:
                            st.session_state.cert_file = create_certificate(u_name, f"{corrects}/30", active_sub)
                            st.balloons()
                        else:
                            st.error(f"Natija: {corrects}/30. Sertifikat uchun 21 ball kerak.")
                        st.session_state.test_run = False
                        st.rerun()

if st.session_state.cert_file:
    st.image(st.session_state.cert_file)
    if st.sidebar.text_input("Parol:", type="password") == "Izzat06":
        st.download_button("📥 Yuklab olish", st.session_state.cert_file, "Sertifikat.png")
