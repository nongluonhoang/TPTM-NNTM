import os
import time
import cv2
import numpy as np
import traceback
from ultralytics import YOLO
from flask import Flask, Response, render_template, request, jsonify
import pandas as pd

# Khởi tạo Flask app
app = Flask(__name__)

# Đường dẫn đến video
VIDEO_SOURCE = r'Smart_City-Case_study\hi2.mp4'

# Biến toàn cục
line_pts = []
track_history = {}
frame_count = 0
first_frame = None
processing_started = False
violations = []

# Kiểm tra video
cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    raise RuntimeError("Không thể mở video: " + VIDEO_SOURCE)
ret, first_frame = cap.read()
if not ret:
    raise RuntimeError("Không thể đọc khung hình đầu tiên từ video.")
cap.release()

# Tải mô hình
car_model = YOLO('yolov8n.pt')
tl_model = YOLO(r'C:\Users\Admin\Desktop\Smart-City-and-Smart-Agriculture-main\Smart_City-Case_study\best_traffic_nano_yolo.pt')
os.makedirs('vi_pham', exist_ok=True)

def side_of_line(pt, p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return (x2 - x1) * (pt[1] - y1) - (y2 - y1) * (pt[0] - x1)

def export_to_csv(violations_data, filename='bao_cao_vi_pham.csv'):
    try:
        df = pd.DataFrame(violations_data, columns=['ID Xe', 'Thời gian vi phạm', 'Đường dẫn ảnh'])
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"[THÔNG BÁO] Đã xuất báo cáo ra {filename}")
        return filename
    except Exception as e:
        print(f"[LỖI] Không thể xuất báo cáo CSV: {e}")
        return None

@app.route('/first_frame')
def get_first_frame():
    try:
        ret, buffer = cv2.imencode('.jpg', first_frame)
        if not ret:
            return jsonify({"status": "error", "message": "Không thể mã hóa khung hình đầu tiên."}), 500
        return Response(buffer.tobytes(), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"status": "error", "message": "Lỗi server khi lấy khung hình đầu tiên."}), 500

@app.route('/set_line_points', methods=['POST'])
def set_line_points():
    global line_pts, processing_started
    data = request.get_json()
    if not data or 'x1' not in data or 'x2' not in data:
        return jsonify({"status": "error", "message": "Dữ liệu tọa độ không hợp lệ."}), 400
    line_pts = [(int(data['x1']), int(data['y1'])), (int(data['x2']), int(data['y2']))]
    processing_started = True
    return jsonify({"status": "success", "message": "Đã thiết lập tọa độ đường thẳng thành công"})

@app.route('/violations', methods=['GET'])
def get_violations():
    return jsonify(violations)

def generate_frames():
    global frame_count, track_history, violations
    if not processing_started:
        print("[CẢNH BÁO] processing_started là False. Không thể bắt đầu luồng video.")
        return

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"[LỖI] Không thể mở video: {VIDEO_SOURCE}")
        return

    try:
        track_stream = car_model.track(
            source=VIDEO_SOURCE,
            conf=0.5,
            iou=0.5,
            persist=True,
            stream=True
        )
    except Exception as e:
        print(f"[LỖI] Không thể khởi tạo luồng video: {e}")
        cap.release()
        return

    for result in track_stream:
        try:
            frame_count += 1
            frame = result.orig_img.copy()

            if len(line_pts) == 2:
                cv2.line(frame, line_pts[0], line_pts[1], (0, 255, 0), 2)

            tl_res = tl_model(frame, conf=0.3)[0]
            tl_state = None
            for tl_box in tl_res.boxes:
                x1_l, y1_l, x2_l, y2_l = tl_box.xyxy.cpu().numpy().astype(int)[0]
                cls_id = int(tl_box.cls.cpu().item())
                conf_l = float(tl_box.conf.cpu().item())
                name = tl_model.model.names[cls_id]
                color = (0, 255, 0) if name == 'green' else (0, 0, 255)
                cv2.rectangle(frame, (x1_l, y1_l), (x2_l, y2_l), color, 2)
                cv2.putText(frame, f"{name}:{conf_l:.2f}", (x1_l, y1_l - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                if tl_state is None or conf_l > tl_state[1]:
                    tl_state = (name, conf_l)

            light_label = tl_state[0] if tl_state else "no-light"
            cv2.putText(frame, f"Đèn: {light_label}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0) if light_label == 'green' else (0, 0, 255), 2)

            for box in result.boxes:
                if box.id is None:
                    continue
                tid = int(box.id.cpu().item())
                x1, y1, x2, y2 = box.xyxy.cpu().numpy().astype(int)[0]
                cx = (x1 + x2) // 2
                cy = y2

                if tid not in track_history:
                    track_history[tid] = {
                        'pt': (cx, cy),
                        'crossed': False,
                        'violation': False,
                        'violation_time': None
                    }
                rec = track_history[tid]
                box_color = (0, 0, 255) if rec['violation'] else (255, 0, 0)

                if not rec['crossed'] and len(line_pts) == 2:
                    s_prev = side_of_line(rec['pt'], line_pts[0], line_pts[1])
                    s_curr = side_of_line((cx, cy), line_pts[0], line_pts[1])
                    if s_prev * s_curr < 0:
                        if light_label == 'red':
                            rec['violation'] = True
                            rec['violation_time'] = time.time()
                            crop = result.orig_img[y1:y2, x1:x2]
                            fname = os.path.join('vi_pham', f"car_{tid}_{frame_count}.jpg")
                            cv2.imwrite(fname, crop)
                            violation_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                            violations.append([tid, violation_time, fname])
                        rec['crossed'] = True

                rec['pt'] = (cx, cy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, f"ID:{tid}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                cv2.circle(frame, (cx, cy), 4, box_color, -1)

                if rec['violation'] and rec['violation_time'] is not None:
                    if time.time() - rec['violation_time'] <= 1.0:
                        cv2.putText(frame, "VI PHẠM", (x1, y1 - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            violation_count = sum(1 for v in track_history.values() if v['violation'])
            cv2.putText(frame, f"Số vi phạm: {violation_count}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except Exception as e:
            traceback.print_exc()
            continue

    if violations:
        export_to_csv(violations)

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except SystemExit as e:
        print(f"SystemExit with code: {e}")
