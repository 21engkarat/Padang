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
check_date = st.date_input("เลือกวันที่ต้องการให้ตรวจเช็คระบบ (💡 ทดลองเปลี่ยนเป็น ก.ย. 2569 เพื่อทดสอบแจ้งเตือน)", today)

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

# 3. ประมวลผล PDF ด้วย Text Scanner (แก้อาการหาข้อมูลไม่เจอ)
if uploaded_file is not None:
    uploaded_file.seek(0)
    overdue_list = []
    total_records = 0
    
    with st.spinner("⏳ ระบบกำลังอ่านไฟล์ PDF ด้วยโหมดสแกนข้อความขั้นสูง กรุณารอสักครู่..."):
        raw_text_all = ""
        
        # กวาดตัวหนังสือทั้งหมดออกมาจาก PDF
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # ตัดข้อความหัวกระดาษและท้ายกระดาษทิ้ง เพื่อไม่ให้ระบบดึงวันที่พิมพ์เอกสารมาปน
                    text = re.sub(r'กรมศุลกากร.*?\n', '', text)
                    text = re.sub(r'รายงานยานพาหนะ.*?\n', '', text)
                    text = re.sub(r'ด่านศุลกากร.*?\n', '', text)
                    text = re.sub(r'ตั้งแต่วันที่.*?\n', '', text)
                    text = re.sub(r'หน้าที่.*?\n', '', text)
                    text = re.sub(r'วันที่ \d{2}/\d{2}/\d{4}.*?\n', '', text)
                    text = re.sub(r'เวลา \d{2}:\d{2}:\d{2} น\..*?\n', '', text)
                    raw_text_all += text + "\n"
        
        # ใช้ Regex ค้นหา "เลขที่ใบขนสินค้า" เพื่อใช้เป็นจุดตัดแยกข้อมูลรถแต่ละคัน
        matches = list(re.finditer(r'(\d{4}-\d-\d{4}-\d{5})', raw_text_all))
        
        records = []
        for i, match in enumerate(matches):
            dec_num = match.group(1)
            start_idx = match.end()
            # ตัดข้อความเฉพาะช่วงของรถคันนั้นๆ (ถึงคันถัดไป)
            end_idx = matches[i+1].start() if i+1 < len(matches) else len(raw_text_all)
            
            chunk = raw_text_all[start_idx:end_idx]
            
            # ดึงวันที่ทั้งหมดออกมาจากบล็อกข้อมูล วันที่อันสุดท้ายคือ "วันครบกำหนด" เสมอ
            dates = re.findall(r'(\d{2}/\d{2}/\d{4})', chunk)
            due_date = dates[-1] if dates else ""
            
            # สแกนหาป้ายทะเบียนรถ (ตัวอักษรภาษาอังกฤษ/ไทย ตามด้วยตัวเลข)
            plate_match = re.search(r'\b([A-Z]{1,3}\s*\d{1,4})\b', chunk)
            plate = plate_match.group(1) if plate_match else ""
            if not plate:
                plate_match_th = re.search(r'([ก-ฮ]{1,2}\s*\d{1,4})', chunk)
                plate = plate_match_th.group(1) if plate_match_th else "มีในเอกสาร"
            
            # สแกนหาชื่อผู้นำเข้า
            lines = [l.strip() for l in chunk.split('\n') if l.strip()]
            name = lines[0] if lines else "ไม่ระบุ"
            name = re.sub(r'^\d+\s*', '', name)
            
            records.append({
                "ลำดับ": str(i + 1),
                "เลขที่ใบขน": dec_num,
                "ชื่อผู้นำเข้า": name[:30],
                "ทะเบียน": plate,
                "วันครบกำหนด": due_date,
                "raw_text": chunk
            })
        
        # 4. ตรวจเช็ควันครบกำหนดเปรียบเทียบกับวันที่เลือกรันระบบ
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
                            "ทะเบียน": rec["ทะเบียน"],
                            "วันครบกำหนด": rec["วันครบกำหนด"]
                        })
                except Exception:
                    continue

    # 5. แสดงผลลัพธ์
    st.markdown("---")
    
    if total_records == 0:
        st.error("❌ ระบบยังคงอ่านไฟล์ไม่ได้ โปรดตรวจสอบว่าไฟล์ PDF มีการเข้ารหัสผ่านไว้หรือไม่")
    else:
        st.subheader(f"📊 ผลการตรวจสอบข้อมูล (แกะข้อความสำเร็จทั้งหมด {total_records} คัน)")
        
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
