from flask import Flask, render_template, Response, request
import cv2, os, datetime
import cam_control as cam_control
import opencv_tools
import logger_tools

logger = logger_tools.get_logger(__name__)

app = Flask(__name__, static_url_path="/static")

camera = cam_control.CameraController()


def gen_frames():
    while camera.capture_started:
        # logger.debug("gen_frames called")
        data = camera.get_image()
        if data is None:
            continue
        else:
            # logger.debug("sending image data")
            # opencv_tools.save_image(data, metadata, "data")
            ret, buffer = cv2.imencode(".jpg", data)
            frame = buffer.tobytes()
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )  # concat frame one by one and show result


# main page
@app.route("/")
def index():
    return render_template("index.html")


# start capture
@app.route("/start_capture", methods=["GET"])
def start_capture():
    logger.debug(f"start_capture called with args: {request.args}")

    manual = True if (str(request.args.get("manual")).lower() == "true") else False
    save = True if (str(request.args.get("save")).lower() == "true") else False

    save_dir = os.path.join(
        "data", datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    )
    os.makedirs(save_dir)

    success = camera.start_capture(manual, save, save_dir)
    if success:
        return "Capture started."
    else:
        return "Capture start failed."


# stop capture
@app.route("/stop_capture")
def stop_capture():
    logger.debug("stop_capture called")

    success = camera.stop_capture()
    if success:
        return "Capture stopped."
    else:
        return "Capture stop failed."


# serve images
@app.route("/image_stream")
def video_feed():
    logger.debug("image_stream called")
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
