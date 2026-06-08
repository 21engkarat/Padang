import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบตรวจสอบวันครบกำหนด", layout="wide", page_icon="🚗")

# --- 🎨 ตกแต่งปุ่ม Clear เป็นสีแดง ---
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
}
</style>
""", unsafe_allow_html=True)

st.title("🚗🏍️ ตรวจสอบวันครบกำหนด")
st.write("ระบบตรวจเช็ครายงานยานพาหนะต่างประเทศกลับออกจากราชอาณาจักรเกินกำหนดเวลา")

# --- ระบบปุ่ม Clear ---
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

def clear_data():
    st.session_state["file_uploader_key"] += 1

thai_months = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

# 1. วันที่ตรวจสอบ
today = datetime.now()
check_date = st.date_input("เลือกวันที่ต้องการให้ตรวจเช็คระบบ", today)

th_day = check_date.day
th_month = thai_months[check_date.month - 1]
th_year = check_date.year + 543
st.info(f"📅 วันที่ใช้ตรวจสอบปัจจุบันคือ: **{th_day} {th_month} {th_year}**")

current_date_core = datetime(check_date.year, check_date.month, check_date.day)

# 2. ควบคุมการอัปโหลด
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

# 3. ประมวลผล PDF
if uploaded_file is not None:
    # 🔥 FIX BUK: สั่งให้ระบบย้อนกลับไปอ่านบรรทัดแรกของไฟล์ใหม่เสมอ 
    # ป้องกันบั๊กเวลาผู้ใช้เปลี่ยนวันที่บนหน้าเว็บ
    uploaded_file.seek(0)
    
    overdue_list = []
    total_records = 0
    
    with st.spinner("⏳ ระบบกำลังอ่านไฟล์ PDF และประกอบร่างข้อมูล กรุณารอสักครู่..."):
        records = []
        current_rec = None
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        clean_row = [str(item).replace('\n', ' ').strip() if item else "" for item in row]
                        row_str = " | ".join(clean_row)
                        
                        # ค้นหาเลขใบขนสินค้า
                        ใบขน_match = re.search(r'(\d{4}\s*-\s*\d\s*-\s*\d{4}\s*-\s*\d{5})', row_str)
                        
                        if ใบขน_match:
                            if current_rec:
                                records.append(current_rec)
                            
                            all_dates = re.findall(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', row_str)
                            due_date = all_dates[-1] if all_dates else ""
                            
                            current_rec = {
                                "ลำดับ": str(len(records) + 1),
                                "เลขที่ใบขน": ใบขน_match.group(1).replace(' ', ''),
                                "ชื่อผู้นำเข้า": clean_row[2] if len(clean_row) > 2 else "",
                                "ทะเบียน": "",
                                "วันครบกำหนด": due_date,
                                "raw_text": row_str
                            }
                        elif current_rec:
                            current_rec["raw_text"] += " " + row_str
                            if len(clean_row) > 3:
                                for cell in clean_row[3:6]:
                                    if cell and len(cell) <= 10 and re.search(r'[A-Za-z]', cell) and re.search(r'\d', cell):
                                        if not current_rec["ทะเบียน"]:
                                            current_rec["ทะเบียน"] = cell
                                            
        if current_rec:
            records.append(current_rec)
        
        # 4. ตรวจเช็ควันครบกำหนด
        for rec in records:
            if rec["วันครบกำหนด"]:
                try:
                    total_records += 1
                    day_part, month_part, year_part = rec["วันครบกำหนด"].replace('-', '/').split('/')
                    expiry_year_ce = int(year_part) - 543
                    expiry_date_object = datetime(expiry_year_ce, int(month_part), int(day_part))
                    
                    icon = "🚗"
                    if "YAMAHA" in rec["raw_text"].upper() or "WAVE" in rec["raw_text"].upper() or "รถจักรยานยน" in rec["raw_text"].replace(' ', ''):
                        icon = "🏍️"
                    
                    if expiry_date_object < current_date_core:
                        overdue_list.append({
                            "ประเภท": icon,
                            "ลำดับ": rec["ลำดับ"],
                            "เลขที่ใบขน": rec["เลขที่ใบขน"],
                            "ชื่อผู้นำเข้า": rec["ชื่อผู้นำเข้า"],
                            "ทะเบียน": rec["ทะเบียน"] if rec["ทะเบียน"] else "ระบุในเอกสาร",
                            "วันครบกำหนด": rec["วันครบกำหนด"]
                        })
                except Exception:
                    continue

    # 5. แสดงผลลัพธ์
    st.markdown("---")
    
    # ดักจับว่าระบบอ่านไฟล์ PDF ออกมาได้กี่คัน
    if total_records == 0:
        st.error("❌ ระบบไม่สามารถดึงข้อมูลจาก PDF ได้ กรุณากดปุ่ม Clear สีแดง แล้วลองอัปโหลดไฟล์เข้าไปใหม่อีกครั้งครับ")
    else:
        st.subheader(f"📊 ผลการตรวจสอบข้อมูล (อ่านเอกสารสำเร็จทั้งหมด {total_records} คัน)")
        
        if overdue_list:
            df_overdue = pd.DataFrame(overdue_list)
            st.error(f"⚠️ พบรายการเกินกำหนดเวลาทั้งหมด {len(df_overdue)} รายการ (วันครบกำหนด มาก่อนวันที่ {th_day} {th_month} {th_year})")
            st.dataframe(df_overdue, use_container_width=True)
            
            csv = df_overdue.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ดาวน์โหลดรายชื่อผู้เกินกำหนดเป็น CSV",
                data=csv,
                file_name=f"overdue_report_{th_day}_{th_month}_{th_year}.csv",
                mime="text/csv",
            )
        else:
            st.success(f"🟢 ไม่พบรายการที่เกินกำหนดเวลา (ทุกคันมีกำหนดออก หลังวันที่ {th_day} {th_month} {th_year})")
