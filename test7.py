import streamlit as st
import pandas as pd
from firebase import firebase
import cv2
from pyzbar.pyzbar import decode
import numpy as np

# Firebase connection
firebase = firebase.FirebaseApplication(
    'https://check-4c4c4-default-rtdb.asia-southeast1.firebasedatabase.app/',
    None
)

# ดึงข้อมูลจาก Firebase
result_pass = firebase.get('/Pass/MAC ID', None)
result_ng = firebase.get('/NG/MAC ID', None)

# ฟังก์ชันแปลงข้อมูลเป็น DataFrame
def convert_to_dataframe(result, status):
    if result:
        data_list = []
        for key, value in result.items():
            if isinstance(value, dict):
                value['ID'] = key
                value['Status'] = status
                # เพิ่ม Location เป็น 'N/A' สำหรับข้อมูล NG
                if status == 'NG' and 'Localtion' not in value:
                    value['Localtion'] = 'N/A'
                data_list.append(value)
            else:
                data_dict = {'ID': key, 'Value': value, 'Status': status}
                if status == 'NG':
                    data_dict['Localtion'] = 'N/A'
                data_list.append(data_dict)
        return pd.DataFrame(data_list)
    return pd.DataFrame()

# สร้าง DataFrame สำหรับแต่ละประเภท
df_pass = convert_to_dataframe(result_pass, 'Pass')
df_ng = convert_to_dataframe(result_ng, 'NG')

# รวม DataFrame
df = pd.concat([df_pass, df_ng], ignore_index=True)

# ตรวจสอบว่า df มีข้อมูลหรือไม่
if not df.empty:
    selected_columns = [
        'ID', 'Status', 'Localtion', 'Modbus_RTU', 'Modbus_TCP', 'Volt_judge',
        'cpu_judge', 'RSSI_judge', 'User', 'date_regis',
    ]

def search(MAC):
    if MAC:
        df_mac_filtered = df[df['ID'] == MAC]
        if not df_mac_filtered.empty:
            columns_to_show = [col for col in df_mac_filtered.columns if col not in selected_columns]
            df_mac_filtered = df_mac_filtered[columns_to_show]
            df_topic_value = df_mac_filtered.T.reset_index()
            df_topic_value.columns = ["Topic", "Value"]
            st.dataframe(df_topic_value, use_container_width=True)
        else:
            st.warning(f"⚠️ ไม่พบข้อมูลสำหรับ MAC ID: `{MAC}`")

# ฟังก์ชันแสกน QR code
def scan_qr_code(image):
    decoded_objects = decode(image)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None

# ฟังก์ชันการแสดงภาพจากกล้องและแสกน QR code แบบ real-time
def real_time_qr_scanning():
    camera_input = st.camera_input("🎥 ใช้กล้องมือถือถ่ายภาพ")
    if camera_input:
        # แปลงภาพที่ได้จาก camera_input เป็น NumPy array
        img = np.array(bytearray(camera_input.getvalue()), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        # แสดงภาพจากกล้อง
        st.image(img, channels="BGR", use_column_width=True)

        # แสกน QR code
        qr_code_data = scan_qr_code(img)
        if qr_code_data:
            return qr_code_data
    return None

# เรียกใช้ฟังก์ชันแสกน QR code
if st.button("🎥 เริ่มแสกน QR Code แบบอัตโนมัติ"):
    qr_code_data = real_time_qr_scanning()
    if qr_code_data:
        st.write(f"📱 พบ QR Code: {qr_code_data}")
        search(qr_code_data)
    else:
        st.warning("⚠️ ไม่พบ QR Code ในภาพที่ถ่าย")
