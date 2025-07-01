from flask import Flask, render_template, request, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import cv2
import easyocr
import re
import math

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# โหลด EasyOCR ภาษาอังกฤษ (ใช้ครั้งเดียว)
reader = easyocr.Reader(["en"])


def truncate_one_decimal(x: float) -> float:
    """ตัด (truncate) ทศนิยมเหลือ 1 ตำแหน่ง"""
    return math.floor(x * 10) / 10.0


@app.route("/", methods=["GET", "POST"])
def index():
    result_numbers = []
    image_url = None

    if request.method == "POST":
        if "image" not in request.files:
            return "No file part"

        file = request.files["image"]
        if file.filename == "":
            return "No selected file"

        # เซฟไฟล์ภาพ
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # สร้าง URL ให้ <img> โหลด
        image_url = url_for("uploaded_file", filename=filename)

        # โหลดภาพ
        image = cv2.imread(filepath)
        if image is None:
            return "Error loading image"

        # ลดขนาดภาพ (ถ้ากว้างเกิน 800 px)
        max_width = 800
        h, w = image.shape[:2]
        if w > max_width:
            ratio = max_width / w
            new_dim = (max_width, int(h * ratio))
            image = cv2.resize(image, new_dim, interpolation=cv2.INTER_AREA)

        # OCR แบบคืนเฉพาะข้อความ (detail=0)
        texts = reader.readtext(image, detail=0)

        # กรองเฉพาะเลขทศนิยม (pattern: อย่างน้อย 1 ตำแหน่งหลังจุด)
        number_pattern = r"^\d+\.\d+$"
        for t in texts:
            if re.match(number_pattern, t):
                val = float(t)
                trunc = truncate_one_decimal(val)
                result_numbers.append(f"{trunc:.1f}°C")

    return render_template("index.html",
                           numbers=result_numbers,
                           image_url=image_url)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/manual", methods=["POST"])
def manual():
    value = request.form.get("manual_input")
    # ตรวจรูปแบบเลขทศนิยม
    if not value or not re.match(r"^\d+(\.\d+)?$", value):
        return "ข้อมูลไม่ถูกต้อง ต้องเป็นตัวเลขทศนิยมเท่านั้น เช่น 36.58"

    val = float(value)
    trunc = truncate_one_decimal(val)
    return render_template("index.html",
                           numbers=[f"{trunc:.1f}°C"],
                           image_url=None)


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, threaded=True)
