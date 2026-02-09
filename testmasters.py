import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from PIL import Image, ImageDraw, ImageFont
import io

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Smart Test Masters Pro", layout="centered")

# 2. Google Sheets ulanishi (Siz yuborgan havola)
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s_Q6s_To2pI63gqqXWmGfkN_H2yIO42KIBA8G5b0B4U/edit?usp=sharing"

# --- 3. CANVA USLUBIDAGI SERTIFIKAT FUNKSIYASI ---
def create_certificate(name, score_text, subject):
    W, H = 1200, 850
    img = Image.new('RGB', (255, 255, 255), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Oltinrang bezaklar
    gold_color = (197, 160, 82) 
    draw.rectangle([60, 60, 1140, 790], outline=gold_color, width=2)
    
    # Burchaklardagi nafis hoshiyalar
    offset, length = 60, 100
    for i in [(offset, offset, 1, 1), (W-offset, offset, -1, 1), 
              (offset, H-offset, 1, -1), (W-offset, H-offset, -1, -1)]:
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

    # --- ELEMENTLARNI MARKAZLASHTIRISH ---
    
    # 1. LOGOTIP
    try:
        logo = Image.open("logo.jpg").convert("RGBA").resize((150, 150))
        img.paste(logo, (int(W/2 - 75), 90), logo)
    except: pass

    # 2. SARLAVHA
    draw.text((W/2, 290), "SERTIFIKAT", fill=(30, 30, 30), font=f_title, anchor="mm")
    draw.text((W/2, 365), "USHBU HUJJAT QUYIDAGI SHAXSGA TOPSHIRILADI:", fill=gold_color, font=f_sub, anchor="mm")

    # 3. ISM
    draw.text((W/2, 460), name.upper(), fill=(30, 30, 30), font=f_name, anchor="mm")
    
    # 4. TAVSIF
    info_text = f"'{subject}' fani bo'yicha o'tkazilgan test sinovlarida\nmuvaffaqiyatli ishtirok etib, yuqori natija ko'rsatgani uchun."
    draw.multiline_text((W/2, 580), info_text, fill=(60, 60, 60), font=f_text, anchor="mm", align="center")
    
    # 5. NATIJA
    draw.text((W/2, 670), f"NATIJA: {score_text}", fill=(46, 125, 50), font=f_sub, anchor="mm")

    # 6. IMZO VA DIREKTOR (MARKAZDA)
    line_y = 760
    draw.line([(W/2 - 180, line_y), (W/2 + 180, line_y)], fill=gold_color, width=2)
    draw.text((W/2, line_y + 35), "Direktor: Normurodov Izzatillo", fill=(30, 30, 30), font=f_dir, anchor="mm")

    try:
        sig = Image.open("signature.jpg").convert("RGBA")
        datas = sig.getdata()
        newData = []
        for item in datas:
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        sig.putdata(newData)
        sig = sig.resize((260, 130))
        img.paste(sig, (int(W/2 - 130), line_y - 110), sig)
    except: pass

    # 7. SANA (O'NGDA)
    draw.text((1100, 780), f"Sana: {time.strftime('%d.%m.%Y')}", fill="gray", font=f_dir, anchor="rs")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 4. ASOSIY MANTIQ ---
try:
    q_df = conn.read(spreadsheet=SHEET_URL, worksheet="Questions")
    s_df = conn.read(spreadsheet=SHEET_URL, worksheet="Settings")
    u_df = conn.read(spreadsheet=SHEET_URL, worksheet="Users")
    
    # Aktiv fanni aniqlash
    active_sub_list = s_df.loc[s_df['Parameter'] == 'ActiveSubject', 'Value'].values
    active_sub = active_sub_list[0] if len(active_sub_list) > 0 else "Noma'lum"
except Exception as e:
    st.error(f"Ma'lumotlar bazasiga ulanishda xato: {e}")
    st.stop()

st.title(f"🎓 {active_sub} fanidan onlayn test")

if 'cert_file' not in st.session_state: st.session_state.cert_file = None
if 'test_started' not in st.session_state: st.session_state.test_started = False

user_name = st.text_input("Ism-familiyangizni kiriting:").strip()

if user_name:
    if user_name in u_df['Ism'].values:
        st.warning("Siz avval test topshirgansiz. Natija bitta foydalanuvchi uchun bir marta qabul qilinadi.")
    else:
        if not st.session_state.test_started:
            if st.button("Testni boshlash"):
                st.session_state.test_started = True
                st.rerun()

        if st.session_state.test_started:
            with st.form("test_form"):
                subject_qs = q_df[q_df['Fan'] == active_sub]
                if len(subject_qs) < 30:
                    questions = subject_qs
                else:
                    questions = subject_qs.sample(n=30)
                
                user_answers = {}
                for i, (idx, row) in enumerate(questions.iterrows()):
                    st.markdown(f"**{i+1}. {row['Savol']}**")
                    user_answers[idx] = st.radio(f"Javobni tanlang ({i+1}):", [row['A'], row['B'], row['C'], row['D']], key=f"q_{idx}")
                
                if st.form_submit_button("Testni yakunlash"):
                    score = sum(1 for idx, row in questions.iterrows() if str(user_answers[idx]) == str(row['Javob']))
                    
                    # Foydalanuvchini ro'yxatga qo'shish
                    new_user = pd.DataFrame([{"Ism": user_name}])
                    updated_users = pd.concat([u_df, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=updated_users, worksheet="Users")
                    
                    # Sertifikat sharti: 20 tadan ko'p (21 va undan yuqori)
                    if score > 20:
                        st.success(f"Tabriklaymiz! Natijangiz: {score}/30")
                        st.session_state.cert_file = create_certificate(user_name, f"{score}/{len(questions)}", active_sub)
                        st.balloons()
                    else:
                        st.error(f"Siz {score} ball to'pladingiz. Sertifikat olish uchun kamida 21 ball kerak.")
                    
                    st.session_state.test_started = False
                    st.rerun()

if st.session_state.cert_file:
    st.image(st.session_state.cert_file, caption="Sizning sertifikatingiz")
    admin_pass = st.sidebar.text_input("Yuklab olish uchun parolni kiriting:", type="password")
    if admin_pass == "Izzat06":
        st.download_button("📥 Sertifikatni yuklab olish", st.session_state.cert_file, file_name=f"{user_name}_sertifikat.png", mime="image/png")
    elif admin_pass:
        st.sidebar.error("Parol noto'g'ri!")
