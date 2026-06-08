import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบตรวจเช็ควันครบกำหนด PDF", layout="wide")
st.title("📋 ระบบตรวจสอบวันครบกำหนดจากไฟล์ PDF (ปาดังเบซาร์)")
st.write("อัปโหลดไฟล์ PDF เพื่อตรวจสอบรายการที่เกินกำหนดเวลาออกนอกราชอาณาจักร")

# 1. ป้อนวันที่ต้องการรันตรวจสอบ (ค่าเริ่มต้นเป็นวันปัจจุบัน)
check_date = st.date_input("เลือกวันที่ต้องการใช้ตรวจเช็คระบบ", datetime.now())

# แปลงวันที่เลือกเป็น พ.ศ. เพื่อเทียบกับข้อมูลใน PDF
current_year_th = check_date.year + 543
today_th = datetime(current_year_th, check_date.month, check_date.day)

# ตัวอัปโหลดไฟล์หน้าเว็บ
uploaded_file = st.file_uploader("ลากและวางไฟล์ PDF ที่นี่", type=["pdf"])

if uploaded_file is not None:
    overdue_list = []
    total_records = 0
    
    # 2. อ่านไฟล์ PDF ตรงๆ จากหน้าเว็บ
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or "ลำดับ" in row[0] or "ครบกำหนด" in row[-1]:
                        continue
                    
                    try:
                        total_records += 1
                        # ดึงวันที่ครบกำหนดจากคอลัมน์สุดท้าย
                        expiry_date_str = row[-1].strip().split('\n')[0]
                        expiry_date = datetime.strptime(expiry_date_str, "%d/%m/%Y")
                        
                        # เงื่อนไขแก้ไขใหม่: ถ้าวันครบกำหนด น้อยกว่า วันที่รัน (ผ่านมาแล้ว) = เกินกำหนด
                        # ถ้าเท่ากับ หรือ มากกว่า = ยังไม่เกินกำหนด (วันปัจจุบันจะไม่แจ้งเตือน)
                        if expiry_date < today_th:
                            overdue_list.append({
                                "ลำดับ": row[0].replace('\n', ' '),
                                "เลขที่ใบขน": row[1].replace('\n', ' '),
                                "ชื่อผู้นำเข้า": row[2].replace('\n', ' '),
                                "ทะเบียน": row[3].replace('\n', ' '),
                                "วันครบกำหนด": expiry_date_str
                            })
                    except Exception as e:
                        continue

    # 3. แสดงผลลัพธ์บนหน้าเว็บ
    st.markdown("---")
    st.subheader(True and f"📊 ผลการตรวจสอบข้อมูล (ตรวจพบทั้งหมด {total_records} รายการ)")
    
    if overdue_list:
        df_overdue = pd.DataFrame(overdue_list)
        st.error(f"⚠️ พบรายการเกินกำหนดเวลาทั้งหมด {len(df_overdue)} รายการ (วันครบกำหนดมาก่อนวันที่รันระบบ)")
        st.dataframe(df_overdue, use_container_width=True)
        
        # ปุ่มดาวน์โหลดไฟล์ผลลัพธ์ออกเป็น Excel/CSV
        csv = df_overdue.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลดรายชื่อผู้เกินกำหนดเป็น CSV",
            data=csv,
            file_name=f"overdue_report_{check_date}.csv",
            mime="text/csv",
        )
    else:
        st.success("🟢 ไม่พบรายการที่เกินกำหนดเวลา (ทุกรายการยังอยู่ในกำหนด หรือเป็นวันปัจจุบัน)")
