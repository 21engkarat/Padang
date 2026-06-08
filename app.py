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
check_date = st.date_input("เลือกวันที่ต้องการให้ตรวจเช็คระบบ (💡 ลองเปลี่ยนเป็นเดือน ก.ย. เพื่อทดสอบแจ้งเตือน)", today)

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
    uploaded_file.seek(0)
    overdue_list = []
    total_records = 0
    
    with st.spinner("⏳ ระบบกำลังล็อกพิกัดตารางและสแกนข้อมูล กรุณารอสักครู่..."):
        records_data = []
        header_plate_x0 = 350 # ค่าพิกัดเริ่มต้นสำรอง
        
        with pdfplumber.open(uploaded_file) as pdf:
            # --- 🔥 ขั้นตอนใหม่: ค้นหาพิกัดแกน X ของคอลัมน์ "ทะเบียน" จากหัวกระดาษ ---
            for page in pdf.pages:
                for w in page.extract_words():
                    if "ทะเบียน" in w['text']:
                        header_plate_x0 = w['x0']
                        break
                if header_plate_x0 != 350:
                    break # เจอแล้วหยุดหาได้เลย
                    
            for page in pdf.pages:
                words = page.extract_words()
                
                current_rec_words = []
                for w in words:
                    text = w['text'].strip()
                    if re.match(r'^\d{4}-\d-\d{4}-\d{5}$', text):
                        if current_rec_words:
                            records_data.append(current_rec_words)
                        current_rec_words = [w]
                    elif current_rec_words:
                        current_rec_words.append(w)
                        
                if current_rec_words:
                    records_data.append(current_rec_words)
                    
        # ประมวลผลข้อมูลแต่ละคัน
        for rec_words in records_data:
            raw_text = " ".join([w['text'] for w in rec_words])
            dec_num = rec_words[0]['text']
            
            # --- แกะวันครบกำหนด (ขวาสุด) ---
            dates = []
            for w in rec_words:
                match = re.search(r'(\d{2}/\d{2}/\d{4})', w['text'])
                if match:
                    dates.append({'date_str': match.group(1), 'x0': w['x0']})
            
            due_date = ""
            if dates:
                rightmost_date = max(dates, key=lambda d: d['x0'])
                due_date = rightmost_date['date_str']
                
            # --- แกะชื่อผู้นำเข้า ---
            name = "ไม่ระบุ"
            name_match = re.search(r'\d{4}-\d-\d{4}-\d{5}\s+(.*?)\s+(MALAYSIAN|THAI|\d{6,})', raw_text)
            if name_match:
                name = name_match.group(1).strip()
                
            # --- 🔥 จุดแก้ไข: แกะทะเบียนรถด้วยเรดาร์ล็อกคอลัมน์ ---
            # ป้องกันชื่อรุ่นรถหลอกระบบ
            blacklist_models = ["E300", "E200", "E250", "C200", "C250", "C300", "X70", "X50", "CX5", "CX3", "CX8", "CRV", "HRV", "BRV", "320D", "520D", "A200", "A250"]
            
            potential_plates = []
            for w in rec_words:
                clean_text = w['text'].replace('-', '').replace(' ', '').strip().upper()
                
                if any(clean_text == model for model in blacklist_models):
                    continue
                    
                # เช็คแพทเทิร์นป้ายทะเบียน
                if re.match(r'^([A-Z]{1,3}\d{1,4}[A-Z]?|[ก-ฮ]{1,2}\d{1,4}|\d[ก-ฮ]{1,2}\d{1,4})$', clean_text):
                    if len(clean_text) >= 2 and not clean_text.isdigit():
                        potential_plates.append(w)
            
            plate = ""
            if potential_plates:
                # เลือกคำที่มีพิกัด X ตรงกับคอลัมน์ "ทะเบียน" มากที่สุด
                best_w = min(potential_plates, key=lambda w: abs(w['x0'] - header_plate_x0))
                plate = best_w['text']
            
            # แผนสำรองกรณีหาไม่เจอ
            if not plate:
                plate_match = re.search(r'\b([A-Z]{2,3}\s*\d{1,4}[A-Z]?)\b', raw_text)
                if plate_match:
                    plate = plate_match.group(1)
                else:
                    plate_match_th = re.search(r'([ก-ฮ]{1,2}\s*\d{1,4})', raw_text)
                    plate = plate_match_th.group(1) if plate_match_th else "มีในเอกสาร"
                    
            # --- เช็คสถานะวันครบกำหนด ---
            if due_date:
                try:
                    total_records += 1
                    day_part, month_part, year_part = due_date.split('/')
                    expiry_year_ce = int(year_part) - 543
                    expiry_date_object = datetime(expiry_year_ce, int(month_part), int(day_part))
                    
                    icon = "🚗"
                    if "YAMAHA" in raw_text.upper() or "WAVE" in raw_text.upper() or "รถจักรยานยน" in raw_text.replace(' ', ''):
                        icon = "🏍️"
                        
                    if expiry_date_object < current_date_core:
                        overdue_list.append({
                            "ลำดับ": str(total_records), # เริ่มนับ 1, 2, 3 แน่นอน
                            "ประเภท": icon,
                            "เลขที่ใบขน": dec_num,
                            "ชื่อผู้นำเข้า": name[:30],
                            "ทะเบียน": plate,
                            "วันครบกำหนด": due_date
                        })
                except Exception:
                    continue

    # 4. แสดงผลลัพธ์
    st.markdown("---")
    if total_records == 0:
        st.error("❌ ระบบไม่สามารถอ่านข้อมูลได้ กรุณากดปุ่ม Clear และอัปโหลดไฟล์ใหม่อีกครั้ง")
    else:
        st.subheader(f"📊 ผลการตรวจสอบข้อมูล (แกะข้อความและพิกัดสำเร็จทั้งหมด {total_records} คัน)")
        
        if overdue_list:
            df_overdue = pd.DataFrame(overdue_list)
            st.error(f"⚠️ พบรายการเกินกำหนดเวลาทั้งหมด {len(df_overdue)} รายการ (วันครบกำหนด มาก่อนวันที่ตรวจสอบ)")
            
            # จัดเรียงคอลัมน์
            df_overdue = df_overdue[["ลำดับ", "ประเภท", "เลขที่ใบขน", "ชื่อผู้นำเข้า", "ทะเบียน", "วันครบกำหนด"]]
            
            # 🔥 ลบ Index 0, 1, 2 ของ Streamlit ออก โดยตั้งคอลัมน์ "ลำดับ" เป็นหลักแทน
            df_overdue.set_index("ลำดับ", inplace=True)
            
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
