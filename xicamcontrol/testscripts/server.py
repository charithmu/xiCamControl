import cv2
import time
import os
from threading import Thread
from flask import Flask, send_file, jsonify

app = Flask(__name__, static_folder="static")

def capture_images():
    cap = cv2.VideoCapture(0) # 0 is the default webcam
    count = 0
    image_folder = 'img'

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        filename = os.path.join(image_folder, f'{count}.jpg')
        cv2.imwrite(filename, frame)
        count += 1
        time.sleep(1)  # wait for 1 second

    cap.release()
    cv2.destroyAllWindows()

@app.route('/latest_image')
def latest_image():
    image_folder = 'img'
    list_of_images = sorted(os.listdir(image_folder))
    latest_image = list_of_images[-1] if list_of_images else None
    return jsonify({'latest_image': latest_image})

@app.route('/images/<path:path>')
def serve_image(path):
    filename = os.path.join("img", path)
    return send_file(filename, mimetype='image/jpg')

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    Thread(target=capture_images).start()
    app.run(port=8080)
