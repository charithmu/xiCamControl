from flask import Flask, send_file, request, render_template
import cv2
import io
import time
import threading
from flask import jsonify

# Setup webcam
cap = cv2.VideoCapture(0)

app = Flask(__name__)

# Global variables for image buffer and capture thread
image_buffer = None
capture_thread = None
stop_event = threading.Event()


def capture_image(stop_event):
    global image_buffer
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            return
        is_success, buffer = cv2.imencode(".jpg", frame)
        io_buf = io.BytesIO(buffer)
        image_buffer = io_buf
        print("Captured image")
        time.sleep(1)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/getLatestImage')
def get_image():
    global image_buffer
    if image_buffer is None:
        return "No image captured yet", 404
    image_buffer.seek(0)
    return send_file(image_buffer, mimetype='image/jpg')


@app.route('/startCapture')
def start_capture():
    global capture_thread, stop_event
    if capture_thread is None or not capture_thread.is_alive():
        stop_event = threading.Event()
        capture_thread = threading.Thread(target=capture_image, args=(stop_event,))
        capture_thread.start()
        return jsonify({"status": "Capture started"}), 200
    else:
        return jsonify({"status": "Capture already running"}), 400


@app.route('/stopCapture')
def stop_capture():
    global capture_thread, stop_event
    if capture_thread is not None and capture_thread.is_alive():
        stop_event.set()
        capture_thread.join()
        capture_thread = None
        return jsonify({"status": "Capture stopped"}), 200
    else:
        return jsonify({"status": "No capture to stop"}), 400


@app.route('/restartCapture')
def restart_capture():
    stop_capture()
    start_capture()
    return jsonify({"status": "Capture restarted"}), 200


if __name__ == '__main__':
    app.run(port=3002)
