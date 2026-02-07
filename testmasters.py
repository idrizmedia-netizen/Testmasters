import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Test Masters - Onlayn Imtihon", layout="centered")

# 2. Google Sheets ulanishi
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Savollar bazasi (Fizika, Matematika, Informatika)
questions = {
    "Matematika": [
        {"q": "5 + 7 = ?", "options": ["10", "11", "12", "13"], "a": "12"},
        {"q": "25 ning ildizi nechchi?", "options": ["4", "5", "6", "10"], "a": "5"},
        {"q": "3 ning kubi nechchi?", "options": ["9", "27", "18", "81"], "a": "27"},
        {"q": "To'g'ri to'rtburchak yuzi formulasi?", "options": ["a+b", "a*b", "2(a+b)", "a^2"], "a": "a*b"},
        {"q": "100 / 4 = ?", "options": ["20", "25", "30", "50"], "a": "25"},
        {"q": "X + 5 = 15 bo'lsa, X=?", "options": ["5", "10", "15", "20"], "a": "10"},
        {"q": "Doira yuzi formulasi?", "options": ["2πr", "πr^2", "πd", "2π"], "a": "πr^2"},
        {"q": "15 * 3 = ?", "options": ["35", "40", "45", "50"], "a": "45"},
        {"q": "Eng kichik tub son?", "options": ["1", "2", "3", "5"], "a": "2"},
        {"q": "90 gradusli burchak qanday ataladi?", "options": ["O'tkir", "O'tmas", "To'g'ri", "Yoyiq"], "a": "To'g'ri"}
    ],
    "Fizika": [
        {"q": "Tezlik formulasi qaysi?", "options": ["v=s/t", "v=m*a", "v=F/s", "v=m/v"], "a": "v=s/t"},
        {"q": "Kuch birligi nima?", "options": ["Joul", "Vatt", "Nyuton", "Paskal"], "a": "Nyuton"},
        {"q": "Suvning qaynash temperaturasi?", "options": ["80°C", "90°C", "100°C", "120°C"], "a": "100°C"},
        {"q": "Zichlik belgisi?", "options": ["m", "p (ro)", "v", "F"], "a": "p (ro)"},
        {"q": "Tok kuchi birligi?", "options": ["Volt", "Om", "Amper", "Vatt"], "a": "Amper"},
        {"q": "Erkin tushish tezlanishi (g)?", "options": ["8.9", "9.8", "10.5", "12"], "a": "9.8"},
        {"q": "Energiyaning saqlanish qonunini kim ochgan?", "options": ["Nyuton", "Eynshteyn", "Lomonosov", "Paskal"], "a": "Lomonosov"},
        {"q": "Yorug'lik tezligi qancha (km/s)?", "options": ["200,000", "300,000", "400,000", "150,000"], "a": "300,000"},
        {"q": "Bosim birligi?", "options": ["Nyuton", "Paskal", "Joul", "Amper"], "a": "Paskal"},
        {"q": "Ohm qonuni formulasi?", "options": ["I=U/R", "F=ma", "E=mc^2", "P=UI"], "a": "I=U/R"}
    ],
    "Informatika": [
        {"q": "Eng kichik axborot birligi?", "options": ["Bayt", "Bit", "Kbayt", "Mbayt"], "a": "Bit"},
        {"q": "Python-da ekranga chiqarish buyrug'i?", "options": ["input()", "print()", "write()", "echo"], "a": "print()"},
        {"q": "1 Kilobayt necha bayt?", "options": ["1000", "1024", "512", "2048"], "a": "1024"},
        {"q": "Kompyuterning 'miyasi' qaysi?", "options": ["RAM", "Monitor", "Protsessor", "HDD"], "a": "Protsessor"},
        {"q": "Fayl nomini o'zgartirish tugmasi?", "options": ["F1", "F2", "F5", "Delete"], "a": "F2"},
        {"q": "Google qidiruv tizimi asoschilaridan biri?", "options": ["Bill Geyts", "Stiv Jobs", "Larri Peyj", "Mark Sukerberg"], "a": "Larri Peyj"},
        {"q": "Saytlar qaysi tilda yoziladi?", "options": ["HTML", "CSS", "Python", "Hammasi"], "a": "Hammasi"},
        {"q": "O'zgaruvchi nomi qaysi belgidan boshlanmaydi?", "options": ["Harf", "Raqam", "_", "Katta harf"], "a": "Raqam"},
        {"q": "Operatsion tizimni toping?", "options": ["Telegram", "Windows", "Python", "Google"], "a": "Windows"},
        {"q": "Dasturdagi xatolik nima deyiladi?", "options": ["Virus", "Bag (Bug)", "Log", "Setup"], "a": "Bag (Bug)"}
    ]
}

# 4. Foydalanuvchi interfeysi
st.title("🎓 Test Masters - Onlayn Olimpiada")
st.info("Iltimos, ismingizni kiriting va fanni tanlang.")

name = st.text_input("F.I.SH:")
subject = st.selectbox("Imtihon topshiradigan faningizni tanlang:", list(questions.keys()))

if name:
    st.divider()
    st.subheader(f"Yo'nalish: {subject}")
    
    score = 0
    # Testlarni ko'rsatish
    for i, item in enumerate(questions[subject]):
        st.write(f"**{i+1}. {item['q']}**")
        ans = st.radio(f"Javobni tanlang:", item['options'], key=f"q_{subject}_{i}")
        if ans == item['a']:
            score += 1
    
    st.divider()
    
    # Natijani yuborish tugmasi
    if st.button("Natijani bazaga yuborish"):
        try:
            # Yangi natija qatori
            new_row = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/10"}])
            
            # Google Sheets'dan eski ma'lumotlarni o'qish
            # URL qismini o'zingizning Google Sheets IDingiz bilan almashtirishni unutmang
            sheet_url = "https://docs.google.com/spreadsheets/d/1zNTrtJwVzR0X07v6oKqf7324..." 
            
            df = conn.read(spreadsheet=sheet_url)
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # Yangilangan jadvalni qayta yozish
            conn.update(spreadsheet=sheet_url, data=updated_df)
            
            st.success(f"Rahmat, {name}! Natijangiz ({score}/10) muvaffaqiyatli saqlandi.")
            st.balloons()
            
        except Exception as e:
            st.error(f"Xatolik yuz berdi: {e}")
            st.warning("Eslatma: Google Sheets 'Public' bo'lishi va Streamlit Secrets sozlangan bo'lishi kerak.")
else:
    st.warning("Davom etish uchun ismingizni yozing.")
