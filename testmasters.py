if name:
    st.divider()
    score = 0
    for i, item in enumerate(questions[subject]):
        st.write(f"{i+1}. {item['q']}")
        ans = st.radio(f"Javobni tanlang:", item['options'], key=f"q_{subject}_{i}")
        if ans == item['a']:
            score += 1
    
    if st.button("Natijani bazaga yuborish"):
        try:
            # Yangi natija qatori
            new_row = pd.DataFrame([{"Ism": name, "Fan": subject, "Ball": f"{score}/10"}])
            
            # Ma'lumotlarni o'qish (ttl=0 keshni o'chiradi)
            df = conn.read(spreadsheet=SHEET_URL, ttl=0)
            
            # Yangi qatorni qo'shish
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # Google Sheets'ga yangilangan jadvalni yozish
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            
            st.success(f"Rahmat {name}! Natijangiz ({score}/10) saqlandi.")
            st.balloons()
            
        except Exception as e:
            st.error(f"Xatolik yuz berdi: {e}")
            st.info("Eslatma: Jadvalingizdagi varaq nomi 'Sheet1' bo'lishi va servis emailiga 'Editor' ruxsati berilgan bo'lishi shart.")
else:
    st.warning("Iltimos, ismingizni yozing.")
