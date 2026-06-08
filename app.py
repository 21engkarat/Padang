import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้างและใส่ไอคอนหน้าแท็บ
st.set_page_config(page_title="ระบบตรวจสอบวันครบกำหนด", layout="wide", page_icon="🚗")

# ตกแต่งส่วนหัวด้วยอิโมจิยานพาหนะต่างๆ 🚗🏍️
st.title("🚗🏍️ ตรวจสอบวันครบกำหนด")
st.write("ระบบตรวจเช็ครายงานยานพาหนะต่างประเทศกลับออกจากราชอาณาจักรเกินกำหนดเวลา")

# --- ระบบปุ่ม Clear (ล้างข้อมูล) ---
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

def clear_data():
    st.session_state["file_uploader_key"] += 1
    st.success("🧹 ล้างข้อมูลเรียบร้อยแล้ว!")

# รายชื่อเดือนภาษาไทยสำหรับแปลงการแสดงผล
thai_months = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

# 1. จัดตำแหน่งป้อนวันที่ตรวจสอบ
today = datetime.now()
check_date = st.date_input("เลือกวันที่ต้องการใช้ตรวจเช็คระบบ", today)

# แปลงวันที่เลือกให้แสดงผลเป็นรูปแบบ "8 มิถุนายน 2569" บนหน้าเว็บ
th_day = check_date.day
th_month = thai_months[check_date.month - 1]
th_year = check_date.year + 543
st.info(f"📅 วันที่ใช้ตรวจสอบปัจจุบันคือ: **{th_day} {th_month} {th_year}**")

# ส่งค่าวันที่แปลงเป็น พ.ศ. ไปคำนวณหลังบ้าน
today_th = datetime(th_year, check_date.month, check_date.day)

# 2. ส่วนของปุ่มควบคุมการอัปโหลดและการล้างข้อมูล
col1, col2 = st.columns([6, 1])
with col1:
    uploaded_file = st.file_uploader(
        "ลากและวางไฟล์ PDF ที่นี่", 
        type=["pdf"], 
        key=f"uploader_{st.session_state['file_uploader_key']}"
    )
with col2:
    st.write(" ") # สร้างช่องว่างให้ปุ่มอยู่ระดับเดียวกับช่องอัปโหลด
    st.write(" ") 
    st.button("🧹 Clear", on_click=clear_data, use_container_width=True)

# 3. เริ่มประมวลผลไฟล์ PDF เมื่อมีการอัปโหลดเข้าสู่ระบบ
if uploaded_file is not None:
    overdue_list = []
    total_records = 0
    
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
                        
                        # แยกประเภทรถตามแบรนด์หรือประเภทเพื่อใส่ไอคอนตกแต่งในตาราง
                        vehicle_brand = row[3].upper() if row[3] else ""
                        icon = "🚗"
                        if "WAVE" in vehicle_brand or "YAMAHA" in vehicle_brand or "รถจักรยานยน" in str(row):
                            icon = "🏍️"
                        
                        # เงื่อนไข: วันครบกำหนด < วันที่รันระบบ (ผ่านมาแล้ว) = เกินกำหนดจริง
                        if expiry_date < today_th:
                            overdue_list.append({
                                "ประเภท": icon,
                                "ลำดับ": row[0].replace('\n', ' '),
                                "เลขที่ใบขน": row[1].replace('\n', ' '),
                                "ชื่อผู้นำเข้า": row[2].replace('\n', ' '),
                                "ทะเบียน": row[3].replace('\n', ' '),
                                "วันครบกำหนด": expiry_date_str
                            })
                    except Exception as e:
                        continue

    # 4. ส่วนการแสดงผลลัพธ์ (แก้ไขจุดบั๊กข้อความซ้อนเรียบร้อยครับ)
    st.markdown("---")
    header_text = f"📊 ผลการตรวจสอบข้อมูล (ตรวจพบพาหนะทั้งหมด {total_records} คัน)"
    st.subheader(header_text)
    
    if overdue_list:
        df_overdue = pd.DataFrame(overdue_list)
        st.error(f"⚠️ พบรายการเกินกำหนดเวลาทั้งหมด {len(df_overdue)} รายการ (วันครบกำหนดมาก่อนวันที่รันระบบ)")
        
        # แสดงตารางข้อมูลบนหน้าเว็บ
        st.dataframe(df_overdue, use_container_width=True)
        
        # ปุ่มดาวน์โหลดไฟล์รายงานออกเป็น Excel/CSV
        csv = df_overdue.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลดรายชื่อผู้เกินกำหนดเป็น CSV",
            data=csv,
            file_name=f"overdue_report_{th_day}_{th_month}_{th_year}.csv",
            mime="text/csv",
        )
    else:
        st.success("🟢 ไม่พบรายการที่เกินกำหนดเวลา (ทุกรายการยังอยู่ในกำหนด หรือเป็นวันปัจจุบัน)")
