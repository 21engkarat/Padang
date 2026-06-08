import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้างและใส่ไอคอนหน้าแท็บ
st.set_page_config(page_title="ตรวจสอบวันครบกำหนด", layout="wide", page_icon="🚗")

# --- 🎨 ตกแต่งปุ่ม Clear เป็นสีแดงด้วย CSS ---
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
    background-color: #FF4B4B !important; 
    color: white !important; 
    border: none !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {
    background-color: #FF6B6B !important; 
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

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

# แปลงวันที่เลือกให้แสดงผลเป็นรูปแบบไทยบนหน้าเว็บ
th_day = check_date.day
th_month = thai_months[check_date.month - 1]
th_year = check_date.year + 543
st.info(f"📅 วันที่ใช้ตรวจสอบปัจจุบันคือ: **{th_day} {th_month} {th_year}**")

# สร้างออบเจกต์วันที่ตรวจสอบเพื่อเอาไปเปรียบเทียบ (ใช้รูปแบบ ค.ศ. สากล)
# โดยดึงเฉพาะ วัน และ เดือน ของวันนี้มาคำนวณ
current_date_core = datetime(check_date.year, check_date.month, check_date.day)

# 2. ส่วนของปุ่มควบคุมการอัปโหลดและการล้างข้อมูล
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
    
    # 🔥 เพิ่มระบบ Pop-up กล่องสปินเนอร์หมุนตอนกำลังตรวจสอบข้อมูล
    with st.spinner("⏳ ระบบกำลังอ่านไฟล์ PDF และสแกนข้อมูลวันครบกำหนด กรุณารอสักครู่..."):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # คัดกรองแถวที่ไม่ใช่ข้อมูลทิ้งไป
                        if not row or row[0] is None or "ลำดับ" in str(row[0]) or "ครบกำหนด" in str(row[-1]):
                            continue
                        
                        try:
                            # ดึงข้อมูลจากคอลัมน์สุดท้าย (วันครบกำหนด)
                            expiry_date_str = str(row[-1]).strip().split('\n')[0]
                            
                            # แปลงข้อมูลสตริงวันที่จาก PDF (เช่น 13/06/2569) แยกส่วนออกมา
                            day_part, month_part, year_part = expiry_date_str.split('/')
                            
                            # แปลงปี พ.ศ. จาก PDF ให้กลายเป็น ค.ศ. เพื่อความแม่นยำในการคำนวณของคอมพิวเตอร์
                            expiry_year_ce = int(year_part) - 543
                            
                            # สร้างออบเจกต์วันที่ของวันครบกำหนดที่เป็น ค.ศ. สมบูรณ์แบบ
                            expiry_date_object = datetime(expiry_year_ce, int(month_part), int(day_part))
                            
                            total_records += 1
                            
                            # --- 🚗🏍️ ตกแต่งรูปภาพตามประเภทรถ ---
                            row_text_raw = " ".join([str(item) for item in row]).upper()
                            icon = "🚗"
                            if "YAMAHA" in row_text_raw or "WAVE" in row_text_raw or "รถจักรยานยน" in row_text_raw:
                                icon = "🏍️"
                            
                            # เงื่อนไข: ถ้าวันครบกำหนด น้อยกว่า วันที่ใช้ตรวจเช็คระบบ (แปลว่าผ่านมาแล้ว = เกินกำหนด)
                            if expiry_date_object < current_date_core:
                                overdue_list.append({
                                    "ประเภท": icon,
                                    "ลำดับ": str(row[0]).replace('\n', ' '),
                                    "เลขที่ใบขน": str(row[1]).replace('\n', ' '),
                                    "ชื่อผู้นำเข้า": str(row[2]).replace('\n', ' '),
                                    "ทะเบียน": str(row[3]).replace('\n', ' '),
                                    "วันครบกำหนด": expiry_date_str
                                })
                        except Exception as e:
                            continue

    # 4. ส่วนการแสดงผลลัพธ์หลังตรวจสอบเสร็จสิ้น
    st.markdown("---")
    st.subheader(f"📊 ผลการตรวจสอบข้อมูล (ตรวจพบพาหนะทั้งหมด {total_records} คัน)")
    
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
