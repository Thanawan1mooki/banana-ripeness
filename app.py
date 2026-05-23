

# from flask import Flask, render_template, request, url_for, redirect
# import os
# # ตรวจสอบให้แน่ใจว่า bana.py อยู่ในไดเรกทอรีเดียวกัน หรืออยู่ใน PYTHONPATH
# # และมีการ import 'model as bana_model' เพื่อเข้าถึงโมเดลที่โหลดใน bana.py
# # from bana import detect_banana, model as bana_model 

# from bana import detect_banana

# app = Flask(__name__)

# # กำหนดโฟลเดอร์สำหรับอัปโหลดไฟล์ชั่วคราว
# UPLOAD_FOLDER = "uploads"
# # กำหนดโฟลเดอร์สำหรับไฟล์ static (เช่น รูปภาพผลลัพธ์)
# STATIC_FOLDER = "static"

# # สร้างโฟลเดอร์ถ้ายังไม่มี
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(STATIC_FOLDER, exist_ok=True)


# # ---------- Nutrition & Benefits mapping ----------
# RIPENESS_INFO = {
#     "raw": {
#         "nutrition": "แป้งดิบสูง ย่อยยากกว่า มีแป้งทนย่อย (resistant starch) สูง",
#         "benefit": "อิ่มนาน ช่วยควบคุมระดับน้ำตาล แต่ท้องอืดได้"
#     },
#     "unripe": {
#         "nutrition": "คาร์บฯเชิงซ้อนมากกว่า กลูโคสยังไม่สูง ไฟเบอร์ปานกลาง",
#         "benefit": "ดีต่อการคุมน้ำตาล มีพรีไบโอติกพอควร"
#     },
#     "ripe": {
#         "nutrition": "พลังงาน ~89 kcal/100g คาร์บฯ ~23g โพแทสเซียมและวิตามิน B6 สูง",
#         "benefit": "ให้พลังงานเร็ว เหมาะก่อน/หลังออกกำลังกาย ช่วยระบบขับถ่าย"
#     },
#     "overripe": {
#         "nutrition": "น้ำตาลเดี่ยวสูง ย่อยเร็ว สารต้านอนุมูลอิสระเพิ่มขึ้น",
#         "benefit": "ดีต่อการทำเบเกอรี่/สมูทตี้ แต่ควรกินพอดีหากคุมน้ำตาล"
#     },
#     "rotten": {
#         "nutrition": "โภชนาการเสื่อม สีดำ/มีกลิ่น เป็นไปได้ว่ามีจุลินทรีย์ปนเปื้อน",
#         "benefit": "ไม่แนะนำให้บริโภค"
#     }
# }


# #app.py
# @app.route("/", methods=["GET", "POST"])
# def index():
#     image_url = None
#     results = None
#     nutrition = ""
#     benefit = ""
#     message = "" # ✅ ตัวแปรสำหรับข้อความแจ้งเตือน

#     if request.method == "POST":
#         if "image" not in request.files:
#             return render_template("index.html", error_message="ไม่พบไฟล์ภาพ")
        
#         image = request.files["image"]
#         if image.filename == "":
#             return render_template("index.html", error_message="ไม่ได้เลือกไฟล์")

#         if image:
#             upload_path = os.path.join(UPLOAD_FOLDER, os.path.basename(image.filename))
#             try:
#                 image.save(upload_path)

#                 # if bana_model is None:
#                 #      return render_template("index.html", error_message="Model Error")

#                 # ส่งเข้า AI
#                 results, output_file_name = detect_banana(upload_path)
                
#                 # เตรียม URL รูป
#                 if output_file_name:
#                     image_url = url_for("static", filename=os.path.basename(output_file_name))
                
#                 # ลบไฟล์ต้นฉบับ
#                 if os.path.exists(upload_path):
#                     os.remove(upload_path)

#                 # ✅ เช็คว่าเจอกล้วยไหม?
#                 if not results:
#                     # ถ้า results เป็นค่าว่าง (AI หาไม่เจอ)
#                     message = "ไม่พบรูปกล้วยในภาพ (No banana detected)(Confidence: {{ r.confidence }})"
#                 else:
#                     # ถ้าเจอ ก็ดึงข้อมูลโภชนาการปกติ
#                     main_label = results[0]["label"]
#                     if main_label in RIPENESS_INFO:
#                         nutrition = RIPENESS_INFO[main_label]["nutrition"]
#                         benefit = RIPENESS_INFO[main_label]["benefit"]

#                 # ส่งค่าไปหน้า result
#                 return render_template("result.html", 
#                                        results=results, 
#                                        image_path=image_url, 
#                                        nutrition=nutrition, 
#                                        benefit=benefit,
#                                        message=message) # ✅ ส่ง message ไปด้วย

#             except Exception as e:
#                 print(f"Error: {e}")
#                 return render_template("index.html", error_message=f"Error: {e}")

#     return render_template("index.html")

# if __name__ == "__main__":
#     # เปลี่ยน host เป็น '0.0.0.0' เพื่อรับการเชื่อมต่อจากทุก Network Interface
#     # เปลี่ยน port เป็น 8888 (หรือพอร์ตอื่นที่สูงๆ เช่น 9999)
#     port = int(os.environ.get("PORT", 10000))
#     app.run(host='0.0.0.0', port=port)

#     app.run(debug=True, host='0.0.0.0', port=8888)

# app.py
import os
from flask import Flask, render_template, request, url_for
from bana import detect_banana
 
app = Flask(__name__)
 
UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
 
# ---------- Nutrition & Benefits ----------
RIPENESS_INFO = {
    "raw": {
        "nutrition": "แป้งดิบสูง ย่อยยากกว่า มีแป้งทนย่อย (resistant starch) สูง",
        "benefit":   "อิ่มนาน ช่วยควบคุมระดับน้ำตาล แต่ท้องอืดได้"
    },
    "unripe": {
        "nutrition": "คาร์บฯเชิงซ้อนมากกว่า กลูโคสยังไม่สูง ไฟเบอร์ปานกลาง",
        "benefit":   "ดีต่อการคุมน้ำตาล มีพรีไบโอติกพอควร"
    },
    "ripe": {
        "nutrition": "พลังงาน ~89 kcal/100g คาร์บฯ ~23g โพแทสเซียมและวิตามิน B6 สูง",
        "benefit":   "ให้พลังงานเร็ว เหมาะก่อน/หลังออกกำลังกาย ช่วยระบบขับถ่าย"
    },
    "overripe": {
        "nutrition": "น้ำตาลเดี่ยวสูง ย่อยเร็ว สารต้านอนุมูลอิสระเพิ่มขึ้น",
        "benefit":   "ดีต่อการทำเบเกอรี่/สมูทตี้ แต่ควรกินพอดีหากคุมน้ำตาล"
    },
    "rotten": {
        "nutrition": "โภชนาการเสื่อม สีดำ/มีกลิ่น เป็นไปได้ว่ามีจุลินทรีย์ปนเปื้อน",
        "benefit":   "ไม่แนะนำให้บริโภค"
    },
}
 
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
 
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
 
 
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # ตรวจสอบไฟล์
        if "image" not in request.files:
            return render_template("index.html", error_message="ไม่พบไฟล์ภาพในคำขอ")
 
        image = request.files["image"]
 
        if image.filename == "":
            return render_template("index.html", error_message="กรุณาเลือกไฟล์ภาพ")
 
        if not allowed_file(image.filename):
            return render_template("index.html",
                                   error_message="รองรับเฉพาะไฟล์ .jpg .jpeg .png .webp เท่านั้น")
 
        upload_path = os.path.join(UPLOAD_FOLDER, os.path.basename(image.filename))
        try:
            image.save(upload_path)
 
            # วิเคราะห์ภาพด้วย AI
            results, output_file = detect_banana(upload_path)
 
            # เตรียม URL รูปผลลัพธ์
            image_url = None
            if output_file:
                image_url = url_for("static", filename=os.path.basename(output_file))
 
            # ลบไฟล์ต้นฉบับหลังประมวลผลเสร็จ
            if os.path.exists(upload_path):
                os.remove(upload_path)
 
            # กรณีไม่เจอกล้วยในภาพ
            if not results:
                return render_template(
                    "result.html",
                    results=[],
                    image_path=image_url,
                    nutrition="",
                    benefit="",
                    message="ไม่พบรูปกล้วยในภาพ กรุณาลองใช้ภาพที่ชัดเจนกว่านี้"
                )
 
            # ดึงข้อมูลโภชนาการจาก label แรก
            main_label = results[0]["label"]
            info = RIPENESS_INFO.get(main_label, {"nutrition": "", "benefit": ""})
 
            return render_template(
                "result.html",
                results=results,
                image_path=image_url,
                nutrition=info["nutrition"],
                benefit=info["benefit"],
                message=""
            )
 
        except Exception as e:
            print(f"[app.py] Error: {e}")
            if os.path.exists(upload_path):
                os.remove(upload_path)
            return render_template("index.html", error_message=f"เกิดข้อผิดพลาด: {e}")
 
    return render_template("index.html")
 
 
if __name__ == "__main__":
    # ✅ มี app.run() แค่อันเดียว — อันเก่ามีสองอัน อันที่สองไม่มีทางรันได้เลย
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)