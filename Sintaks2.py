import cv2
import pytesseract
from datetime import datetime
import mysql.connector

# Path ke executable Tesseract di sistem Anda
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Ubah sesuai path di sistem Anda

# Fungsi untuk cek kode buku dari database
def cek_kode_buku(kode_buku):
    db = mysql.connector.connect(
        host="localhost",
        user="root",  # Ganti dengan username MySQL Anda
        password="",  # Ganti dengan password MySQL Anda
        database="databases"
    )
    cursor = db.cursor()

    cursor.callproc('CekKodeBuku', [kode_buku])

    for result in cursor.stored_results():
        print(result.fetchall())

    cursor.close()
    db.close()

# Fungsi untuk mendeteksi gerakan dan menangkap teks
def deteksi_gerakan_dan_tangkap_teks():
    cap = cv2.VideoCapture(0)
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

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
            teks = pytesseract.image_to_string(roi)
            print("Teks yang terdeteksi:", teks)

            # Cek kode buku di database
            cek_kode_buku(teks.strip())

            # Simpan frame sebagai file gambar
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            image_path = f"captured_{timestamp}.png"
            cv2.imwrite(image_path, frame1)

        cv2.imshow("Feed", frame1)
        frame1 = frame2
        ret, frame2 = cap.read()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    deteksi_gerakan_dan_tangkap_teks()
