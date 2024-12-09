import cv2
import pytesseract
from datetime import datetime
import mysql.connector
import re
import tkinter as tk
from tkinter import scrolledtext, StringVar, OptionMenu
from threading import Thread
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Path ke executable Tesseract di sistem Anda
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Variabel untuk melacak buku yang sudah tersimpan
buku_terdeteksi_total = set()

# Fungsi untuk mengambil daftar paket dari database
def ambil_daftar_paket():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="pkl"
        )
        cursor = db.cursor()

        # Query untuk mengambil daftar paket
        query = "SELECT DISTINCT paket FROM paket"
        cursor.execute(query)
        hasil = cursor.fetchall()

        cursor.close()
        db.close()

        return [row[0] for row in hasil]
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    
# Fungsi untuk menyimpan transaksi ke database
def simpan_transaksi(waktu, gambar_path, buku_yang_terdeteksi, buku_yang_tidak_terdeteksi, paket_terdeteksi):
    try:
        db = mysql.connector.connect(
            host=os.getenv("host", "localhost"),
            user="root",
            password="",
            database="pkl"
        )
        cursor = db.cursor()

        # Masukkan data ke tabel transaksi
        insert_query = """
        INSERT INTO transaksi (waktu, image_path, buku_yang_terdeteksi, buku_yang_tidak_terdeteksi, paket_terdeteksi)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (waktu, gambar_path, buku_yang_terdeteksi, buku_yang_tidak_terdeteksi, paket_terdeteksi))
        db.commit()

        print("Transaksi berhasil disimpan ke database.")

        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Fungsi untuk cek kode buku dari database berdasarkan teks yang diambil dari kamera
def cek_teks_di_database(teks, paket_terpilih):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="pkl"
        )
        cursor = db.cursor()

        # Pisahkan teks yang terdeteksi menjadi kata-kata individual
        kata_kata = teks.split()

        # Query untuk mengambil kode_buku dan paket sesuai pilihan
        query = "SELECT kode_buku, paket FROM paket WHERE paket = %s"
        cursor.execute(query, (paket_terpilih,))
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
    paket_terpilih = paket_var.get()  # Ambil paket yang dipilih
    if not paket_terpilih or paket_terpilih == "Pilih Paket":
        print("Error: Paket belum dipilih.")
        return

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
                buku_ditemukan_di_db, kode_buku_keys = cek_teks_di_database(teks, paket_terpilih)
                if buku_ditemukan_di_db:
                    baru_terdeteksi = [b[0] for b in buku_ditemukan_di_db if b[0] not in buku_terdeteksi_total]
                    buku_terdeteksi_total.update(baru_terdeteksi)

                    if baru_terdeteksi:
                        # Simpan frame sebagai file gambar
                        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        image_path = f"captured_{timestamp}.png"
                        cv2.imwrite(image_path, frame1)

                        # Hitung buku yang tidak terdeteksi
                        buku_tidak_terdeteksi = [kode_buku for kode_buku in kode_buku_keys if kode_buku not in buku_terdeteksi_total]
                        buku_tidak_terdeteksi_str = ', '.join(buku_tidak_terdeteksi)

                        # Simpan ke database
                        waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        buku_terdeteksi_str = ', '.join([f"{b[0]} (Paket: {b[1]})" for b in buku_ditemukan_di_db])
                        simpan_transaksi(waktu, image_path, buku_terdeteksi_str, buku_tidak_terdeteksi_str, paket_terpilih)

                        # Perbarui GUI
                        output_text.delete(1.0, tk.END)
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

# Dropdown untuk memilih paket
paket_var = StringVar()
paket_var.set("Pilih Paket")  # Default pilihan
daftar_paket = ambil_daftar_paket()
paket_dropdown = OptionMenu(root, paket_var, "Pilih Paket", *daftar_paket)
paket_dropdown.pack(pady=10)

capture_button = tk.Button(root, text="Capture", command=lambda: Thread(target=deteksi_gerakan_dan_tangkap_teks).start())
capture_button.pack(pady=10)

output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(pady=10)

root.mainloop()
