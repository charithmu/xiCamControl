# opencv_tools.py

import cv2, os, time, datetime
from threading import Thread
import logger_tools

logger = logger_tools.get_logger(__name__)

def resize_with_aspect_ratio(image, width):
    """Resize image to a given width keeping the aspect ratio"""
    r = width / image.shape[1]
    dim = (width, int(image.shape[0] * r))
    resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    return resized


def resize_with_percent(image, percent):
    """Resize image to a given percent of the original size"""
    width = int(image.shape[1] * percent / 100)
    height = int(image.shape[0] * percent / 100)
    dim = (width, height)
    resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    return resized


def wait_with_check_closing(win_name):
    """
    Wait for a key press and check if the window is closed
    https://stackoverflow.com/questions/35003476/opencv-python-how-to-detect-if-a-window-is-closed/37881722
    """
    while True:
        keyCode = cv2.waitKey(50)
        if keyCode != -1:
            break
        win_prop = cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE)
        if win_prop <= 0:
            break


def show_image(data, metadata, width=None, percent=None):
    """Show the image in a window. Press any key to close the window."""
    logger.debug("Showing image...")

    if width is not None:
        resized = resize_with_aspect_ratio(data, width)
    elif percent is not None:
        resized = resize_with_percent(data, percent)
    else:
        resized = data

    cv2.namedWindow("Preview")
    cv2.imshow("Preview", resized)
    wait_with_check_closing("Preview")
    cv2.destroyAllWindows()

    logger.debug("Done.")


def save_image(data, metadata, path):
    """Save the image to disk."""
    logger.debug("Saving image...")

    filename = "xi_" + str(metadata.timestamp) + ".png"
    filepath = os.path.join(path, filename)

    cv2.imwrite(filepath, data)

    logger.debug("Image saved: " + filepath)


def stream_video(cam, width=None, percent=None):
    """Show a video stream. Press CTRL+C to exit."""

    try:
        logger.info("Starting video. Press CTRL+C to exit.")

        while True:
            if cam.capture_thread is not None and cam.capture_thread.is_alive():
                    
                image = cam.get_image_from_buffer()

                if image is None or image.data is None:
                    continue

                if width is not None:
                    resized = resize_with_aspect_ratio(image.data, width)
                elif percent is not None:
                    resized = resize_with_percent(image.data, percent)
                else:
                    resized = image.data

                text1 = "FrameID:{:f}, Timestamp:{:f} s".format(
                    image.metadata.frame_id, image.metadata.timestamp
                )
                text2 = "Gain:{:5.1f} dB, Exp:{:5.1f} us".format(
                    image.metadata.gain, image.metadata.exposure
                )
                cv2.putText(
                    resized,
                    text1,
                    (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    resized,
                    text2,
                    (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )

                cv2.namedWindow("Preview")
                cv2.imshow("Preview", resized)

                keyCode = cv2.waitKey(1)
                if keyCode != -1:
                    break
                win_prop = cv2.getWindowProperty("Preview", cv2.WND_PROP_VISIBLE)
                if win_prop <= 0:
                    break
            
            else:
                logger.warning("Capture not started. Waiting for the capture thread to start.")

        cv2.destroyAllWindows()

    except KeyboardInterrupt:
        cv2.destroyAllWindows()


def manual_trigger_preview(cam, width=None, percent=None):
    """Show a video stream. Press CTRL+C to exit.
    Intended to use as a Thread target.
    """
    logger.info("Starting Preview. Press CTRL+C to exit.")

    while capture_thread.is_alive():
        data = capture_thread.data
        metadata = capture_thread.metadata

        if data is None:
            continue

        if width is not None:
            resized = resize_with_aspect_ratio(data, width)
        elif percent is not None:
            resized = resize_with_percent(data, percent)
        else:
            resized = data

        if metadata is not None:
            text1 = "FrameID:{:f}, Timestamp:{:f} s".format(
                metadata.frame_id, metadata.timestamp
            )
            text2 = "Gain:{:5.1f} dB, Exp:{:5.1f} us".format(
                metadata.gain, metadata.exposure
            )
            cv2.putText(
                resized,
                text1,
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                resized,
                text2,
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

        cv2.namedWindow("Preview")
        cv2.imshow("Preview", resized)

        # if cv2.waitKey(1) == ord("q"):
        #     break

        keyCode = cv2.waitKey(1)
        if keyCode != -1:
            break
        win_prop = cv2.getWindowProperty("Preview", cv2.WND_PROP_VISIBLE)
        if win_prop <= 0:
            break

    cv2.destroyAllWindows()
    logger.debug("Manual trigger thread has finished.")


def manual_trigger_save(capture_thread, path):
    """Save the image to disk.
    Intended to use as a Thread target.
    """
    logger.info("Saving images.")

    save_dir = os.path.join(path, datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    os.makedirs(save_dir)
    logger.info("Using folder: " + os.path.abspath(save_dir))

    last_timestamp = time.time()

    while capture_thread.is_alive():
        data = capture_thread.data
        metadata = capture_thread.metadata

        if data is not None and metadata is not None:
            timestamp = metadata.timestamp

            if last_timestamp != timestamp:
                last_timestamp = timestamp

                filename = "xi_" + str(timestamp) + ".png"
                filepath = os.path.join(save_dir, filename)
                cv2.imwrite(filepath, data)

                logger.debug("Saved to: " + filepath)
        else:
            # logger.warning("No image available.")
            pass

    capture_thread.stop()
    logger.debug("Manual trigger thread has finished.")


def capture_with_timer(capture_thread, interval, path, percent=None):
    """Save the image to disk.
    Intended to use as a Thread target.
    """
    logger.info(
        f"Capturing and saving images with {interval} second interval. Press CTRL+C to exit."
    )

    save_dir = os.path.join(path, datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    os.makedirs(save_dir)
    logger.info("Using folder: " + os.path.abspath(save_dir))

    s_time = time.time()

    while capture_thread.is_alive():
        n_time = time.time()
        if n_time - s_time < interval:
            continue
        s_time = n_time

        data = capture_thread.data
        metadata = capture_thread.metadata

        if data is None:
            continue

        if metadata is None:
            timestamp = time.time()
        else:
            timestamp = metadata.timestamp

        filename = "xi_" + str(timestamp) + ".png"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, data)

        logger.debug("Saved to: " + filepath)

        if percent is not None:
            resized = resize_with_percent(data, percent)
        else:
            resized = data

        if metadata is not None:
            text1 = "FrameID:{:f}, Timestamp:{:f} s".format(
                metadata.frame_id, metadata.timestamp
            )
            text2 = "Gain:{:5.1f} dB, Exp:{:5.1f} us".format(
                metadata.gain, metadata.exposure
            )
            cv2.putText(
                resized,
                text1,
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                resized,
                text2,
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

        cv2.namedWindow("Preview")
        cv2.imshow("Preview", resized)

        # if cv2.waitKey(1) == ord("q"):
        #     break

        keyCode = cv2.waitKey(1)
        if keyCode != -1:
            break
        win_prop = cv2.getWindowProperty("Preview", cv2.WND_PROP_VISIBLE)
        if win_prop <= 0:
            break

    if capture_thread.is_alive():
        capture_thread.stop()

    cv2.destroyAllWindows()
    logger.debug("Interval trigger thread has finished.")


class CaptureThreadWebCam(Thread):
    def __init__(self, stop_event):
        Thread.__init__(self)
        self.metadata = None
        self.stop_event = stop_event
        self.stream = cv2.VideoCapture(0)
        (self.frame_ok, self.data) = self.stream.read()

    def run(self):
        while self.stop_event.wait(0) is not True:
            (self.frame_ok, self.data) = self.stream.read()

        self.stream.release()

    def stop(self):
        self.stream.release()
        self.stop_event.set()
