import cv2
import pytesseract
from datetime import datetime
import mysql.connector
import re
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 
 
# Path ke executable Tesseract di sistem Anda
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Ubah sesuai path di sistem Anda

# Fungsi untuk menyimpan transaksi ke database
def simpan_transaksi(waktu, gambar_path, buku_yang_terdeteksi, buku_yang_tidak_terdeteksi):
    try:
        db = mysql.connector.connect(
            host=os.getenv("host"),
            user="root",  
            password="",  
            database="pkl"
        )
        cursor = db.cursor()

        # Baca gambar sebagai BLOB
        with open(gambar_path, 'rb') as file:
            blob_data = file.read()

        # Masukkan data ke tabel transaksi
        insert_query = """
        INSERT INTO transaksi (waktu, hasil_capture, buku_yang_terdeteksi, buku_yang_tidak_terdeteksi)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (waktu, blob_data, buku_yang_terdeteksi, buku_yang_tidak_terdeteksi))
        db.commit()

        print("Transaksi berhasil disimpan ke database.")

        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Fungsi untuk cek kode buku dari database berdasarkan teks yang diambil dari kamera
def cek_teks_di_database(teks):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="pkl",
            get_warnings=True
        )
        cursor = db.cursor()

        # Pisahkan teks yang terdeteksi menjadi kata-kata individual
        kata_kata = teks.split()

        # Query untuk mengambil kode_buku dan paket
        cursor.execute("SELECT kode_buku, paket FROM paket")
        hasil = cursor.fetchall()

        # Buat dictionary untuk memetakan kode_buku ke paket
        kode_buku_ke_paket = {item[0]: item[1] for item in hasil}

        buku_ditemukan = []
        for kata in kata_kata:
            if kata in kode_buku_ke_paket:
                buku_ditemukan.append((kata, kode_buku_ke_paket[kata]))

        cursor.close()
        db.close()

        return buku_ditemukan, kode_buku_ke_paket.keys()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None, None

# Fungsi untuk deteksi gerakan dan menangkap teks
def deteksi_gerakan_dan_tangkap_teks():
    buku_ditemukan = []  # Inisialisasi ulang variabel setiap kali fungsi dijalankan
    buku_terdeteksi_set = set()  # Set untuk buku yang terdeteksi

    for cam_index in range(3):
        cap = cv2.VideoCapture(cam_index)
        ret, frame1 = cap.read()
        if not ret:
            print(f"Error: Tidak dapat membaca dari kamera dengan indeks {cam_index}.")
            cap.release()
            continue
        else:
            print(f"Menggunakan kamera dengan indeks {cam_index}")
            break
    else:
        print("Error: Tidak dapat membaca dari semua kamera yang tersedia.")
        return

    ret, frame2 = cap.read()
    if not ret:
        print("Error: Tidak dapat membaca dari kamera.")
        cap.release()
        return

    while cap.isOpened():
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
            roi = frame1[y:y + h, x:x + w]
            teks = pytesseract.image_to_string(roi).strip()

            teks = re.sub(r'\W+', ' ', teks)

            if teks:
                buku_ditemukan_di_db, kode_buku_keys = cek_teks_di_database(teks)
                if buku_ditemukan_di_db:
                    buku_ditemukan.extend(buku_ditemukan_di_db)
                    buku_terdeteksi_set.update([b[0] for b in buku_ditemukan_di_db])

                # Simpan frame sebagai file gambar
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                image_path = f"captured_{timestamp}.png"
                cv2.imwrite(image_path, frame1)

                # Hitung buku yang tidak terdeteksi
                buku_tidak_terdeteksi = [kode_buku for kode_buku in kode_buku_keys if kode_buku not in buku_terdeteksi_set]
                buku_tidak_terdeteksi_str = ', '.join(buku_tidak_terdeteksi)

                # Simpan ke database
                waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                buku_terdeteksi_str = ', '.join([f"{b[0]} (Paket: {b[1]})" for b in buku_ditemukan])
                simpan_transaksi(waktu, image_path, buku_terdeteksi_str, buku_tidak_terdeteksi_str)

                # Perbarui GUI
                output_text.delete(1.0, tk.END)  # Hapus konten lama
                output_text.insert(tk.END, f"Buku yang terdeteksi:\n{buku_terdeteksi_str}\n")
                output_text.insert(tk.END, f"Buku yang tidak terdeteksi:\n{buku_tidak_terdeteksi_str}\n")

        cv2.imshow("Feed", frame1)
        frame1 = frame2.copy()
        ret, frame2 = cap.read()

        if not ret:
            print("Error: Tidak dapat membaca frame berikutnya dari kamera.")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Setup GUI
root = tk.Tk()
root.title("Deteksi Teks dari Kamera")

capture_button = tk.Button(root, text="Capture", command=lambda: Thread(target=deteksi_gerakan_dan_tangkap_teks).start())
capture_button.pack(pady=10)

output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(pady=10)

root.mainloop()
