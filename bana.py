# # bana.py
# import cv2
# import numpy as np
# import os
# import gc
 
# def detect_banana(image_path):
#     """
#     ระบบตรวจจับและจำแนกระดับความสุกของกล้วยหอมทอง
#     ใช้ 2 เทคนิคร่วมกัน:
#       1. YOLO  → ตรวจจับตำแหน่งกล้วยใน bounding box
#       2. HSV   → วิเคราะห์สีเปลือกกล้วยเพื่อจำแนกระดับความสุก
#     คืนค่า: (labels_info, output_path)
#     """
#     from ultralytics import YOLO
 
#     current_model = None
#     try:
#         model_path = os.path.join(os.path.dirname(__file__), "best.pt")
#         current_model = YOLO(model_path)
#         current_model.to('cpu')
#         print("Model loaded for analysis.")
#     except Exception as e:
#         print(f"Error loading model: {e}")
#         return [], os.path.join("static", "error_processing.jpg")
 
#     img = cv2.imread(image_path)
#     if img is None:
#         _cleanup(current_model)
#         return [], os.path.join("static", "error_processing.jpg")
 
#     output_path = os.path.join("static", "result.jpg")
#     labels_info = []
 
#     try:
#         # ── ขั้นที่ 1: YOLO ตรวจจับตำแหน่งกล้วย ──────────────────────────
#         results_list = current_model.predict(
#             source=image_path,
#             imgsz=640,
#             conf=0.5,
#             iou=0.40,
#             verbose=False
#         )
#         results = results_list[0]
 
#         if len(results.boxes) == 0:
#             cv2.imwrite(output_path, img)
#             _cleanup(current_model)
#             return [], output_path
 
#         H_img, W_img = img.shape[:2]
 
#         # กรอง box ซ้อน
#         best_boxes = _filter_best_boxes(results.boxes.data)
 
#         for i, box in enumerate(best_boxes):
#             x1, y1, x2, y2 = map(int, box[:4])
#             conf = float(box[4])
 
#             # Bounding box + padding สำหรับวาดรูป
#             pad = 5
#             x1_show = max(0, x1 - pad)
#             y1_show = max(0, y1 - pad)
#             x2_show = min(W_img, x2 + pad)
#             y2_show = min(H_img, y2 + pad)
 
#             # ── ขั้นที่ 2: Crop กล้วยแล้วส่งให้ HSV วิเคราะห์สี ──────────
#             # Center Crop 20% เพื่อตัดขอบที่อาจปนสีพื้นหลัง
#             w_box, h_box = x2 - x1, y2 - y1
#             cx1 = int(x1 + w_box * 0.20)
#             cy1 = int(y1 + h_box * 0.20)
#             cx2 = int(x2 - w_box * 0.20)
#             cy2 = int(y2 - h_box * 0.20)
 
#             if cx2 <= cx1 or cy2 <= cy1:
#                 crop_analyze = img[y1:y2, x1:x2]
#             else:
#                 crop_analyze = img[cy1:cy2, cx1:cx2]
 
#             if crop_analyze.size == 0:
#                 continue
 
#             # ── ขั้นที่ 3: HSV จำแนกระดับความสุก ─────────────────────────
#             label = _classify_ripeness_hsv(crop_analyze)
 
#             # วาด bounding box + label
#             color = _get_color(label)
#             cv2.rectangle(img, (x1_show, y1_show), (x2_show, y2_show), color, 2)
 
#             label_text = f"{label} ({conf:.2f})"
#             (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
#             cv2.rectangle(img, (x1_show, y1_show - 25), (x1_show + tw, y1_show), color, -1)
#             cv2.putText(img, label_text, (x1_show, y1_show - 8),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2)
 
#             labels_info.append({
#                 "index": i + 1,
#                 "label": label,
#                 "confidence": round(conf, 2)
#             })
 
#         cv2.imwrite(output_path, img)
#         return labels_info, output_path
 
#     except Exception as e:
#         print(f"Error during detection: {e}")
#         return [], os.path.join("static", "error_processing.jpg")
 
#     finally:
#         _cleanup(current_model)
 
 
# # ─────────────────────────────────────────────────────────────────────
# # HSV Color Analysis
# # ─────────────────────────────────────────────────────────────────────
 
# def _classify_ripeness_hsv(crop_bgr: np.ndarray) -> str:
#     """
#     จำแนกระดับความสุกของกล้วยหอมทองด้วยการวิเคราะห์สี HSV
    
#     หลักการ:
#     - แปลง BGR → HSV เพื่อแยกสีออกจากความสว่าง
#     - สร้าง mask เนื้อกล้วย (ตัดพื้นหลัง)
#     - วัดสัดส่วนสีเขียว / จุดน้ำตาล / สีดำ
#     - ตัดสินใจระดับความสุกจาก fraction เหล่านั้น
 
#     ระดับความสุก:
#       raw      → เขียวมาก       (green_frac > 0.75)
#       unripe   → เขียวอมเหลือง  (green_frac > 0.20)
#       ripe     → เหลืองสวย      (default)
#       overripe → มีจุดน้ำตาล    (spot_frac > 0.12 หรือ dark_frac > 0.12)
#       rotten   → ดำเป็นส่วนใหญ่ (dark_frac > 0.40)
#     """
#     hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
 
#     # Mask เนื้อกล้วย — ตัดพื้นหลังขาว/เทา/ไม่มีสี
#     mask_skin = cv2.inRange(hsv,
#                             np.array([0,  25,  45]),
#                             np.array([110, 255, 255]))
#     skin_pixels = cv2.countNonZero(mask_skin)
 
#     if skin_pixels < 50:
#         return "ripe"  # ภาพสว่างจัด/ขาว → default
 
#     # สีเขียว: Hue 32-100
#     mask_green = cv2.bitwise_and(
#         cv2.inRange(hsv, np.array([32, 20, 20]), np.array([100, 255, 255])),
#         mask_skin
#     )
 
#     # สีดำ/มืด: Val < 85 (ช้ำรุนแรง/เน่า)
#     mask_dark = cv2.bitwise_and(
#         cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 85])),
#         mask_skin
#     )
 
#     # จุดน้ำตาล (overripe): Hue 0-25, Val 80-180
#     mask_spots = cv2.bitwise_and(
#         cv2.inRange(hsv, np.array([0, 40, 80]), np.array([25, 255, 180])),
#         mask_skin
#     )
 
#     green_frac = cv2.countNonZero(mask_green) / skin_pixels
#     dark_frac  = cv2.countNonZero(mask_dark)  / skin_pixels
#     spot_frac  = cv2.countNonZero(mask_spots) / skin_pixels
 
#     # Decision Tree
#     if dark_frac > 0.40:
#         return "rotten"
#     elif green_frac > 0.75:
#         return "raw"
#     elif green_frac > 0.20:
#         return "unripe"
#     elif spot_frac > 0.12 or dark_frac > 0.12:
#         return "overripe"
#     else:
#         return "ripe"
 
 
# # ─────────────────────────────────────────────────────────────────────
# # Helper Functions
# # ─────────────────────────────────────────────────────────────────────
 
# def _filter_best_boxes(boxes_data):
#     """
#     กรอง bounding box ซ้อนกันออก โดยใช้ IoU-based NMS
#     ถ้า box ซ้อนกันเกิน 50% เก็บแค่อันที่ confidence สูงสุด
#     """
#     if len(boxes_data) == 0:
#         return []
 
#     boxes = []
#     for box in boxes_data:
#         x1, y1, x2, y2 = map(int, box[:4])
#         conf = float(box[4])
#         cls  = int(box[5])
#         boxes.append((x1, y1, x2, y2, conf, cls))
 
#     boxes.sort(key=lambda b: b[4], reverse=True)
 
#     kept = []
#     for box in boxes:
#         x1, y1, x2, y2, conf, cls = box
#         overlap = False
#         for kept_box in kept:
#             kx1, ky1, kx2, ky2, _, _ = kept_box
#             ix1 = max(x1, kx1); iy1 = max(y1, ky1)
#             ix2 = min(x2, kx2); iy2 = min(y2, ky2)
#             inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
#             area1 = (x2 - x1) * (y2 - y1)
#             area2 = (kx2 - kx1) * (ky2 - ky1)
#             union = area1 + area2 - inter
#             if union > 0 and inter / union > 0.50:
#                 overlap = True
#                 break
#         if not overlap:
#             kept.append(box)
 
#     return [[b[0], b[1], b[2], b[3], b[4], b[5]] for b in kept]
 
 
# def _get_color(label: str) -> tuple:
#     """คืนสี BGR สำหรับแต่ละระดับความสุก"""
#     color_map = {
#         "raw":      (0, 255, 255),  # เหลือง
#         "unripe":   (0, 165, 255),  # ส้ม
#         "ripe":     (0, 200, 0),    # เขียว
#         "overripe": (0, 100, 255),  # ส้มแดง
#         "rotten":   (0, 0, 220),    # แดง
#     }
#     return color_map.get(label, (200, 200, 200))
 
 
# def _cleanup(model) -> None:
#     """คืน RAM หลังใช้งานเสร็จ"""
#     if model is not None:
#         del model
#     gc.collect()
import cv2
import numpy as np
import os
import gc
import onnxruntime as ort

def detect_banana(image_path):
    current_session = None
    try:
        model_path = os.path.join(os.path.dirname(__file__), "best.onnx")
        current_session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        print("ONNX Model loaded.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return [], os.path.join("static", "error_processing.jpg")

    img = cv2.imread(image_path)
    if img is None:
        return [], os.path.join("static", "error_processing.jpg")

    output_path = os.path.join("static", "result.jpg")
    labels_info = []

    try:
        # Preprocess
        input_size = 640
        H_img, W_img = img.shape[:2]
        img_resized = cv2.resize(img, (input_size, input_size))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_input = img_rgb.astype(np.float32) / 255.0
        img_input = np.transpose(img_input, (2, 0, 1))
        img_input = np.expand_dims(img_input, axis=0)

        # Inference
        input_name = current_session.get_inputs()[0].name
        outputs = current_session.run(None, {input_name: img_input})
        predictions = outputs[0][0]  # shape: (num_detections, 6+)

        # Parse boxes (x1,y1,x2,y2,conf,cls) — YOLO format
        boxes_raw = []
        for pred in predictions.T:
            x_c, y_c, w, h = pred[0], pred[1], pred[2], pred[3]
            confs = pred[4:]
            conf = float(np.max(confs))
            if conf < 0.5:
                continue
            # scale back to original
            x1 = int((x_c - w/2) / input_size * W_img)
            y1 = int((y_c - h/2) / input_size * H_img)
            x2 = int((x_c + w/2) / input_size * W_img)
            y2 = int((y_c + h/2) / input_size * H_img)
            boxes_raw.append([x1, y1, x2, y2, conf, 0])

        if not boxes_raw:
            cv2.imwrite(output_path, img)
            return [], output_path

        best_boxes = _filter_best_boxes(boxes_raw)

        for i, box in enumerate(best_boxes):
            x1, y1, x2, y2 = map(int, box[:4])
            conf = float(box[4])

            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(W_img, x2); y2 = min(H_img, y2)

            w_box, h_box = x2 - x1, y2 - y1
            cx1 = int(x1 + w_box * 0.20)
            cy1 = int(y1 + h_box * 0.20)
            cx2 = int(x2 - w_box * 0.20)
            cy2 = int(y2 - h_box * 0.20)

            crop_analyze = img[cy1:cy2, cx1:cx2] if cx2 > cx1 and cy2 > cy1 else img[y1:y2, x1:x2]
            if crop_analyze.size == 0:
                continue

            label = _classify_ripeness_hsv(crop_analyze)
            color = _get_color(label)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label_text = f"{label} ({conf:.2f})"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x1, y1 - 25), (x1 + tw, y1), color, -1)
            cv2.putText(img, label_text, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2)

            labels_info.append({"index": i+1, "label": label, "confidence": round(conf, 2)})

        cv2.imwrite(output_path, img)
        return labels_info, output_path

    except Exception as e:
        print(f"Error during detection: {e}")
        return [], os.path.join("static", "error_processing.jpg")

    finally:
        del current_session
        gc.collect()


# ── ส่วนที่เหลือเหมือนเดิมทุกอย่าง ──
def _classify_ripeness_hsv(crop_bgr):
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    mask_skin = cv2.inRange(hsv, np.array([0,25,45]), np.array([110,255,255]))
    skin_pixels = cv2.countNonZero(mask_skin)
    if skin_pixels < 50:
        return "ripe"
    mask_green = cv2.bitwise_and(cv2.inRange(hsv, np.array([32,20,20]), np.array([100,255,255])), mask_skin)
    mask_dark  = cv2.bitwise_and(cv2.inRange(hsv, np.array([0,0,0]), np.array([180,255,85])), mask_skin)
    mask_spots = cv2.bitwise_and(cv2.inRange(hsv, np.array([0,40,80]), np.array([25,255,180])), mask_skin)
    green_frac = cv2.countNonZero(mask_green) / skin_pixels
    dark_frac  = cv2.countNonZero(mask_dark)  / skin_pixels
    spot_frac  = cv2.countNonZero(mask_spots) / skin_pixels
    if dark_frac > 0.40: return "rotten"
    elif green_frac > 0.75: return "raw"
    elif green_frac > 0.20: return "unripe"
    elif spot_frac > 0.12 or dark_frac > 0.12: return "overripe"
    else: return "ripe"

def _filter_best_boxes(boxes_data):
    if not boxes_data: return []
    boxes = sorted(boxes_data, key=lambda b: b[4], reverse=True)
    kept = []
    for box in boxes:
        x1,y1,x2,y2,conf,cls = box
        overlap = False
        for kb in kept:
            kx1,ky1,kx2,ky2,_,_ = kb
            ix1,iy1 = max(x1,kx1), max(y1,ky1)
            ix2,iy2 = min(x2,kx2), min(y2,ky2)
            inter = max(0,ix2-ix1)*max(0,iy2-iy1)
            union = (x2-x1)*(y2-y1)+(kx2-kx1)*(ky2-ky1)-inter
            if union > 0 and inter/union > 0.50:
                overlap = True; break
        if not overlap: kept.append(box)
    return kept

def _get_color(label):
    return {"raw":(0,255,255),"unripe":(0,165,255),"ripe":(0,200,0),"overripe":(0,100,255),"rotten":(0,0,220)}.get(label,(200,200,200))

def _cleanup(model):
    if model is not None: del model
    gc.collect()