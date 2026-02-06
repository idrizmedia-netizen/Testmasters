if name:
    st.divider()
    st.subheader(f"Yo'nalish: {subject}")
    
    score = 0
    # Testlarni ko'rsatish
    for i, item in enumerate(questions[subject]):
        st.write(f"{i+1}. {item['q']}")
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
