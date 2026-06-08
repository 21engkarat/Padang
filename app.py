import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from streamlit_option_menu import option_menu 

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบตรวจสอบวันครบกำหนด", layout="centered", page_icon="🚗")

# --- 🎨 ตกแต่ง UI ---
st.markdown("""
<style>
h1, h2, h3 { text-align: center !important; }
.stMarkdown p { text-align: center; }

/* ปรับปุ่ม Clear */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
    height: 70px !important;
    background-color: #FF4B4B !important; 
    color: white !important; 
    border: none !important;
    font-weight: bold !important;
    margin-top: 27px;
}
</style>
""", unsafe_allow_html=True)

# --- 🛠️ การจัดการ State ---
if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = datetime.now().date()

def clear_data():
    st.session_state["file_uploader_key"] += 1
    st.session_state["selected_date"] = datetime.now().date()

# =========================================================
# เมนู Sidebar
# =========================================================
with st.sidebar:
    menu = option_menu(
        menu_title="เมนู", 
        options=["ตรวจสอบวันครบกำหนด", "อื่นๆ"], 
        icons=["calendar2-check", "grid-1x2"], 
        menu_icon="cast", 
        default_index=0,
    )

# =========================================================
# เมนูที่ 1: ตรวจสอบวันครบกำหนด
# =========================================================
if menu == "ตรวจสอบวันครบกำหนด":
    st.title("🚗🏍️ ตรวจสอบวันครบกำหนด")
    
    # วันที่
    check_date = st.date_input(
        "เลือกวันที่ต้องการให้ตรวจเช็คระบบ", 
        value=st.session_state["selected_date"],
        key="date_input"
    )
    st.session_state["selected_date"] = check_date

    th_day = check_date.day
    th_month = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"][check_date.month - 1]
    th_year = check_date.year + 543
    st.info(f"📅 วันที่ใช้ตรวจสอบปัจจุบันคือ: **{th_day} {th_month} {th_year}**")

    current_date_core = datetime(check_date.year, check_date.month, check_date.day)

    col1, col2 = st.columns([6, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "ลากและวางไฟล์ PDF ที่นี่", 
            type=["pdf"], 
            key=f"uploader_{st.session_state['file_uploader_key']}"
        )
    with col2:
        st.button("🧹 Clear", on_click=clear_data, use_container_width=True)

    if uploaded_file is not None:
        with pdfplumber.open(uploaded_file) as pdf:
            # (คง Logic เดิมในการสแกนไฟล์ไว้ที่นี่)
            # ... (โค้ดดึงข้อมูล PDF ของคุณ) ...
            pass
        
        # แสดงผลลัพธ์...
        st.success("ประมวลผลเสร็จสิ้น")

elif menu == "อื่นๆ":
    st.title("📂 เมนูอื่นๆ")
    st.write("พื้นที่นี้ถูกจัดสรรไว้สำหรับพัฒนาฟังก์ชันหรือระบบงานอื่นเพิ่มเติมในอนาคต")
