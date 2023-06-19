from flask import Flask, render_template, Response, request
import cv2
import cam_control as cam_control
import opencv_tools

app = Flask(__name__)

camera = cam_control.CameraController()

def gen_frames():  
    while camera.capture_started:
        print("gen_frames called")
        data = camera.get_image()
        if data is None:
            break
        else:
            print("sending image data")
            # opencv_tools.save_image(data, metadata, "data")
            ret, buffer = cv2.imencode('.jpg', data)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') # concat frame one by one and show result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_capture', methods=['GET'])
def start_capture():
    print('start_capture called')
    manual = True if (request.args.get('manual') == 'True') else False
    save = True if (request.args.get('save') == 'True') else False
    camera.start_capture(manual, save)
    return "Capture started."

@app.route('/stop_capture')
def stop_capture():
    print('stop_capture called')
    camera.stop_capture()
    return "Capture stopped."

@app.route('/video_feed')
def video_feed():
    print('video_feed called')
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
