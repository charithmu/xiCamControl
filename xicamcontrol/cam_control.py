import sys, signal, logging, traceback, os, datetime
import argparse
import opencv_tools as ocv_tools
import ximea_camera as xi_cam

from threading import Thread, Event, Lock
import logger_tools


class CameraController:
    def __init__(self):
        self.cam = xi_cam.XimeaCamera()
        self.stop_event = Event()
        self.lock = Lock()
        self.capture_started = False
        self.save = False
        self.save_dir = "data"
        self.logger = logger_tools.get_logger(self.__class__.__name__)

    def start_capture(self, manual=False, save=False, save_dir="data"):
        self.logger.debug(f"Cam Controller start called: {manual}, {save}")

        try:
            num = self.cam.get_xicam().get_number_devices()
            self.logger.debug("Number of cameras: " + str(num))

            self.cam.open()
            self.cam.configure_camera(manual)
            self.save = save
            self.save_dir = save_dir
            self.cam.start_acquisition()
            self.stop_event.clear()
            self.capture_thread = xi_cam.CaptureThread(
                self.cam, self.stop_event, self.lock
            )
            self.capture_thread.start()
            self.capture_started = True
            return True

        except Exception:
            self.logger.error("Camera cannot be opened!", exc_info=True)
            return False

    def stop_capture(self):
        self.logger.debug("Cam Controller stop called")
        try:
            self.stop_event.set()
            self.cam.stop_acquisition()
            self.cam.close()
            self.capture_started = False
            self.save = False
            return True

        except Exception:
            self.logger.error("Camera cannot be closed!", exc_info=True)
            return False

    def get_image(self):
        # self.logger.debug("Cam Controller get_image called")
        if self.capture_started:
            with self.lock:
                data = self.capture_thread.data
                metadata = self.capture_thread.metadata

            if data is None:
                # self.logger.warning("No image available")
                return None
            else:
                if self.save:
                    # self.logger.debug("Saving image to folder: " + os.path.abspath(self.save_dir))
                    ocv_tools.save_image(data, metadata, self.save_dir)

                return ocv_tools.resize_with_aspect_ratio(data, 600)
        else:
            return None


def main(mode, timer=None):
    global stop_event

    cam = xi_cam.XimeaCamera()
    cam.open()

    if mode == "manual" or mode == "output":
        cam.configure_camera(manual=True)
    else:
        cam.configure_camera()

    cam.start_acquisition()

    resize_percent = 25
    skip_frames = 50

    # manul_preview_thread = Thread(target=ocv_tools.manual_trigger_preview, args=(stop_event, cam, None, resize_percent))
    # manual_save_thread = Thread(target=ocv_tools.manual_trigger_save, args=(stop_event, cam, "data"))

    data_lock = Lock()
    capture_thread = xi_cam.CaptureThread(cam, stop_event, data_lock)
    # capture_thread = ocv_tools.CaptureThreadWebCam(stop_event)

    # try:
    if mode == "image":
        data, metadata = cam.get_image_with_metadata_delayed(skip_frames)
        ocv_tools.show_image(data, metadata, percent=resize_percent)

    elif mode == "save":
        data, metadata = cam.get_image_with_metadata_delayed(skip_frames)
        ocv_tools.save_image(data, metadata, "data")

    elif mode == "video":
        ocv_tools.stream_video(cam, percent=resize_percent)

    elif mode == "manual":
        capture_thread.start()
        ocv_tools.manual_trigger_preview(capture_thread, percent=25)
        # manul_preview_thread.start()
        # ocv_tools.manual_trigger_preview(cam, percent=resize_percent)

    elif mode == "output":
        capture_thread.start()
        ocv_tools.manual_trigger_save(capture_thread, "data")
        # manual_save_thread.start()
        # ocv_tools.manual_trigger_save(cam, "data")

    elif mode == "timer":
        capture_thread.start()
        ocv_tools.capture_with_timer(capture_thread, timer, "data", percent=25)

    # except KeyboardInterrupt:
    #     print("Keyboard Interrupt. Exiting in main.")
    #     stop_event.set()

    # if manul_preview_thread.is_alive():
    #     manul_preview_thread.join()

    # if manual_save_thread.is_alive():
    #     manual_save_thread.join()

    cam.stop_acquisition()
    cam.close()
    logger.debug("Exiting main.")


###############################################
if __name__ == "__main__":
    logger = logger_tools.get_logger(__name__)

    stop_event = Event()

    def signal_handler(signal, frame):
        print("\nProgram exiting gracefully")
        stop_event.set()
        # sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    argparse = argparse.ArgumentParser(
        description="Capture images and videos from Ximea Camera",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argparse.add_argument(
        "-i", "--image", help="Capture and show single image", action="store_true"
    )
    argparse.add_argument(
        "-s", "--save", help="Capture and save single image", action="store_true"
    )
    argparse.add_argument(
        "-v", "--video", help="Open video stream", action="store_true"
    )
    argparse.add_argument(
        "-t",
        "--timer",
        help="Capture and save images in given interval (seconds)",
        type=int,
        default=0,
    )
    argparse.add_argument(
        "-m",
        "--manual",
        help="Preview images from manual hardware trigger",
        action="store_true",
    )

    argparse.add_argument(
        "-o",
        "--output",
        help="Save images from manual hardware trigger",
        action="store_true",
    )

    args = argparse.parse_args()
    config = vars(args)

    mod_config = {k: v for k, v in config.items() if k != "timer"}
    options = [k for k, v in mod_config.items() if v == True]
    if config["timer"] > 0:
        options.append("timer")

    # logger.debug(config)
    # logger.debug(options)

    if len(options) > 1:
        logger.warning("Only one option allowed at a time. Exiting.")
        exit()
    elif len(options) == 0:
        logger.warning("No option given. Exiting.")
        exit()
    elif len(options) == 1:
        if options[0] == "timer":
            logger.info(
                f"Running in {options[0]} mode with {config['timer']} seconds interval."
            )
            main(options[0], config["timer"])
        else:
            logger.info(f"Running in {options[0]} mode.")
            main(options[0])
