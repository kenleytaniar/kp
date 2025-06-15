import streamlit as st
from paddleocr import PaddleOCR
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import re
from openpyxl import Workbook, load_workbook

# Function for login page
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "admin" and password == "password":  
            st.session_state['logged_in'] = True
            st.query_params.update({"logged_in": "true"})
        else:
            st.error("Invalid username or password")
            
#function untuk logout
def logout():
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.query_params.update({"logged_in": "false"})



def extract_ktp_info(ocr_results):
    st.subheader("Debug: Semua Teks Hasil OCR")
    raw_texts = []  # List untuk menyimpan semua teks hasil OCR
    ktp_data = {
        "Nama": None,
        "NIK": None,
        "Alamat": None,
        "Tanggal Lahir": None,
        "Jenis Kelamin": None,
        "Agama": None,
        "Pekerjaan": None
    }

    # Regex patterns
    nik_pattern = r"\b\d{16}\b"  # NIK: 16 digit angka
    tanggal_lahir_pattern = r"\b\d{2}-\d{2}-\d{4}\b"  # Format tanggal: dd-mm-yyyy
    jenis_kelamin_keywords = ["LAKI-LAKI", "PEREMPUAN"]
    agama_keywords = ["ISLAM", "KRISTEN", "KATHOLIK", "HINDU", "BUDDHA", "KONGHUCU"]
    nama_keywords = ["NAMA"]  # Kata kunci untuk nama
    alamat_keywords = ["ALAMAT"]  # Kata kunci untuk alamat

    nama_next_line = False  # Flag untuk cek apakah teks berikutnya adalah nama
    alamat_next_line = False  # Flag untuk cek apakah teks berikutnya adalah alamat
    jenis_kelamin_next_line = False  # Flag untuk cek apakah teks berikutnya adalah jenis kelamin
    agama_next_line = False  # Flag untuk cek apakah teks berikutnya adalah agama
    pekerjaan_next_line = False  # Flag untuk cek apakah teks berikutnya adalah pekerjaan

    for line in ocr_results:
        for detection in line:
            text = detection[1][0]
            raw_texts.append(text)  # Simpan untuk debugging
            
            # Cari NIK
            if not ktp_data["NIK"]:
                nik_match = re.search(nik_pattern, text)
                if nik_match:
                    ktp_data["NIK"] = nik_match.group()
            
            # Cari Tanggal Lahir
            if not ktp_data["Tanggal Lahir"]:
                tanggal_match = re.search(tanggal_lahir_pattern, text)
                if tanggal_match:
                    ktp_data["Tanggal Lahir"] = tanggal_match.group()
            
            # Cari Nama dengan kata kunci "Nama"
            if nama_next_line:
                ktp_data["Nama"] = text.strip()
                nama_next_line = False  # Reset flag setelah menemukan nama

            if "NAMA" in text.upper():
                nama_next_line = True

            # Cari Alamat dengan kata kunci "Alamat"
            if alamat_next_line:
                ktp_data["Alamat"] = text.strip()
                alamat_next_line = False  # Reset flag setelah menemukan alamat

            if "ALAMAT" in text.upper():
                alamat_next_line = True

            # Cari Jenis Kelamin dengan kata kunci "Jenis Kelamin"
            if jenis_kelamin_next_line:
                if "LAKI" in text.upper():
                    ktp_data["Jenis Kelamin"] = "LAKI-LAKI"
                elif "PEREMPUAN" in text.upper():
                    ktp_data["Jenis Kelamin"] = "PEREMPUAN"
                jenis_kelamin_next_line = False  # Reset flag setelah menemukan jenis kelamin

            if "JENIS KELAMIN" in text.upper():
                jenis_kelamin_next_line = True

            # Cari Agama dengan kata kunci "Agama"
            if agama_next_line:
                if any(keyword in text.upper() for keyword in agama_keywords):
                    ktp_data["Agama"] = text.strip()
                agama_next_line = False  # Reset flag setelah menemukan agama

            if "AGAMA" in text.upper():
                agama_next_line = True

            # Cari Pekerjaan dengan kata kunci "Pekerjaan"
            if pekerjaan_next_line:
                ktp_data["Pekerjaan"] = text.strip()
                pekerjaan_next_line = False  # Reset flag setelah menemukan pekerjaan

            if "PEKERJAAN" in text.upper():
                pekerjaan_next_line = True

    # Debugging: Tampilkan semua teks hasil OCR
    for idx, raw_text in enumerate(raw_texts, 1):
        st.write(f"Teks {idx}: {raw_text}")
    
    return ktp_data

# Function for OCR page
def ocr_page():
    # Supported languages (add more languages as needed)
    languages = {
        "English": "en",
        "Arabic": "ar",
        "Hindi": "hi",
        "French":"fr",
        "Indonesian":"id"
    }

    # Default language
    selected_lang = st.sidebar.selectbox("Select Language", list(languages.keys()))
    lang_code = languages[selected_lang]

    # Initialize PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang=lang_code, use_gpu=False)

    # Streamlit app
    st.title('APLIKASI OCR UNTUK PENGENALAN TEKS PADA GAMBAR KTP')

    # Upload image
    uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        # Convert the uploaded file to an OpenCV image
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        
        # Display the uploaded image
        st.image(img, channels="BGR")

        # Save the uploaded image to a temporary file
        img_path = 'temp_img.jpg'
        cv2.imwrite(img_path, img)
        
        # Perform OCR
        result = ocr.ocr(img_path, cls=True)

        # Ekstrak data KTP
        ktp_data = extract_ktp_info(result)

        # Tampilkan hasil ekstraksi
        st.subheader("Hasil Ekstraksi Data KTP:")
        for key, value in ktp_data.items():
            st.write(f"{key}:** {value if value else 'Tidak Ditemukan'}")
        
        # Simpan hasil ke file Excel dan tumpuk data baru
        file_path = "ktp_data.xlsx"
        if st.button("Tambahkan Data Ke Excel"):
            df = pd.DataFrame([ktp_data])
            try:
                existing_data = pd.read_excel(file_path)
                new_data = pd.concat([existing_data, df], ignore_index=True)
            except FileNotFoundError:
                new_data = df

            new_data.to_excel(file_path, index=False)

            # Provide download link for the Excel file
            with open(file_path, "rb") as file:
                st.download_button(
                    label="Download Excel",
                    data=file,
                    file_name="ktp_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # Tambahkan tombol untuk menghapus seluruh data
        if st.button("Delete All Data in Excel"):
            wb = Workbook()
            wb.save(file_path)
            st.success("Semua data di file Excel telah dihapus.")
        
        # Tambahkan tombol logout di sidebar
        logout()

# Main function to control the flow
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    ocr_page()
else:
    login_page()