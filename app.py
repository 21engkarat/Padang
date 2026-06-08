import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้างและใส่ไอคอนหน้าแท็บ
st.set_page_config(page_title="ตรวจสอบวันครบกำหนด", layout="wide", page_icon="🚗")

# --- 🎨 ตกแต่งปุ่ม Clear เป็นสีแดงสด ---
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
    background-color: #FF4B4B !important; 
    color: white !important; 
    border: none !important;
    font-weight: bold !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {
    background-color: #FF6B6B !important; 
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# หัวข้อหลักของเว็บไซต์
st.title("🚗 ตรวจสอบวันครบกำหนด")
st.write("ระบบตรวจเช็ครายงานยานพาหนะต่างประเทศกลับออกจากราชอาณาจักรเกินกำหนดเวลา")

# --- ระบบปุ่ม Clear (ล้างข้อมูล) ---
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

def clear_data():
    st.session_state["file_uploader_key"] += 1

# รายชื่อเดือนภาษาไทยสำหรับแปลงการแสดงผล
thai_months = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

# 1. ป้อนวันที่ต้องการใช้ตรวจสอบ (Default เป็นวันปัจจุบัน)
today = datetime.now()
check_date = st.date_input("เลือกวันที่ต้องการให้ตรวจเช็คระบบ", today)

# จัดฟอร์แมตการแสดงผลภาษาไทย เช่น 8 มิถุนายน 2569
th_day = check_date.day
th_month = thai_months[check_date.month - 1]
th_year = check_date.year + 543
st.info(f"📅 วันที่ใช้ตรวจสอบปัจจุบันคือ: **{th_day} {th_month} {th_year}**")

# แปลงวันที่เลือกเป็นรูปแบบวัตถุเวลาสากล (ค.ศ.) เพื่อใช้คำนวณเปรียบเทียบ
current_date_core = datetime(check_date.year, check_date.month, check_date.day)

# 2. ส่วนโครงสร้างหน้าจอ ปุ่มควบคุมการอัปโหลดและการล้างข้อมูล
col1, col2 = st.columns([6, 1])
with col1:
    uploaded_file = st.file_uploader(
        "ลากและวางไฟล์ PDF ที่นี่", 
        type=["pdf"], 
        key=f"uploader_{st.session_state['file_uploader_key']}"
    )
with col2:
    st.write(" ") 
    st.write(" ") 
    st.button("🧹 Clear", on_click=clear_data, use_container_width=True)

# 3. เริ่มประมวลผลไฟล์ PDF เมื่อมีการอัปโหลดเข้าสู่ระบบ
if uploaded_file is not None:
    overdue_list = []
    total_records = 0
    
    # ⏳ แสดง Pop-up หมุนๆ ระหว่างประมวลผลอ่านไฟล์ PDF
    with st.spinner("⏳ ระบบกำลังอ่านไฟล์ PDF และสแกนข้อมูลวันครบกำหนด กรุณารอสักครู่..."):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # คัดกรองแถวที่ไม่ใช่ข้อมูลหลักทิ้งไป
                        if not row or row[0] is None or "ลำดับ" in str(row[0]) or "ครบกำหนด" in str(row[-1]):
                            continue
                        
                        # ทำความสะอาดข้อมูลดิบในแต่ละแถวเพื่อป้องกันปัญหาขึ้นบรรทัดใหม่ (\n)
                        clean_row = [str(item).replace('\n', ' ').strip() if item else "" for item in row]
                        
                        # มองหาข้อความที่มีรูปแบบวันที่ DD/MM/YYYY ในคอลัมน์สุดท้าย
                        date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', clean_row[-1])
                        
                        if date_match:
                            try:
                                total_records += 1
                                day_part, month_part, year_part = date_match.groups()
                                
                                # แปลงปี พ.ศ. ใน PDF ให้เป็น ค.ศ. สำหรับใช้เปรียบเทียบทางคอมพิวเตอร์
                                expiry_year_ce = int(year_part) - 543
                                expiry_date_object = datetime(expiry_year_ce, int(month_part), int(day_part))
                                
                                # ดึงข้อมูลสถานะในแถวมาเช็ค (เช่น ตัดบัญชี หรือ ยังไม่นำกลับ)
                                status_text = clean_row[4] if len(clean_row) > 4 else ""
                                
                                # 🚗 ตกแต่งรูปประเภทพาหนะ
                                row_text_combined = " ".join(clean_row).upper()
                                icon = "🚗"
                                if "YAMAHA" in row_text_combined or "WAVE" in row_text_combined or "รถจักรยานยน" in row_text_combined:
                                    icon = "🏍️"
                                
                                # เงื่อนไขการกรอง: 
                                # 1. วันครบกำหนด มาก่อน วันที่รันระบบจริง (Expired)
                                # 2. สถานะต้องไม่ใช่ "ตัดบัญชี" (คือรถยังไม่กลับออกไปจริงๆ)
                                if expiry_date_object < current_date_core and "ตัดบัญชี" not in status_text:
                                    overdue_list.append({
                                        "ประเภท": icon,
                                        "ลำดับ": clean_row[0],
                                        "เลขที่ใบขน": clean_row[1],
                                        "ชื่อผู้นำเข้า": clean_row[2],
                                        "ทะเบียน": clean_row[3],
                                        "วันครบกำหนด": f"{day_part}/{month_part}/{year_part}"
                                    })
                            except Exception as e:
                                continue

    # 4. ส่วนการแสดงผลลัพธ์
    st.markdown("---")
    st.subheader(f"📊 ผลการตรวจสอบข้อมูล (ตรวจพบพาหนะในรายงานทั้งหมด {total_records} คัน)")
    
    if overdue_list:
        df_overdue = pd.DataFrame(overdue_list)
        st.error(f"⚠️ พบรายการเกินกำหนดเวลาและยังไม่นำกลับทั้งหมด {len(df_overdue)} รายการ")
        st.dataframe(df_overdue, use_container_width=True)
        
        # ปุ่มดาวน์โหลดไฟล์รายงาน
        csv = df_overdue.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลดรายชื่อผู้เกินกำหนดเป็น CSV",
            data=csv,
            file_name=f"overdue_report_{th_day}_{th_month}_{th_year}.csv",
            mime="text/csv",
        )
    else:
        st.success("🟢 ไม่พบรายการที่เกินกำหนดเวลา (ทุกรายการยังไม่หมดอายุ หรือทำการตัดบัญชีออกไปตามกำหนดแล้ว)")
