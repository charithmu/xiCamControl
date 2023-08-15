# ximea_camera.py

from threading import Thread, Lock
from ximea import xiapi
from collections import deque
import logger_tools

class Image:
    """
    A class to hold image data and metadata.
    data: numpy array
    metadata: Metadata object
    """
    
    def __init__(self, data, metadata):
        self.data = data
        self.metadata = metadata

class Metadata:
    """A class to hold metadata for a single image."""

    def __init__(self):
        self.frame_id = 0
        self.timestamp = 0
        self.gain = -1
        self.exposure = 0
        self.width = 0
        self.height = 0
        self.img_format = ""


class CaptureThread(Thread):
    """A class to capture images from a camera in a thread."""

    def __init__(self, ximea_camera):
        Thread.__init__(self)
        self.cam = ximea_camera
        self.logger = logger_tools.get_logger(self.__class__.__name__)

    def run(self):
        self.logger.debug(f"CaptureThread Started. Running until stop event is set.")
        self.logger.debug(f"Image buffer size is {self.cam.buffer_size}.")
        self.logger.debug(f"Trigger type is {self.cam.get_xicam_instance().get_trigger_source()}.")

        while self.cam.stop_event.wait(0) is not True:
            # self.logger.debug(f"CaptureThread running. ")

            image = self.cam.get_image_from_device()
            
            if image.data is not None:
                with self.cam.buffer_lock:
                    self.cam.image_buffer.append(image)
                # self.logger.debug(f"CaptureThread: image acquired with {self.data.shape} and added to buffer.")
            else:
                self.logger.warning("No image available, skipping frame.")
        
        self.logger.debug("CaptureThread finished. Exiting with stop event.")


class XimeaCamera:
    """A class to control a Ximea camera."""

    def __init__(self, image_buffer_size=10):
        """Initialize the camera."""
        self.cam = xiapi.Camera()
        self.img = xiapi.Image()
        self.capture_thread = None
        self.stop_event = None
        self.buffer_size = image_buffer_size
        self.image_buffer = deque(maxlen=self.buffer_size)
        self.buffer_lock = Lock()
        self.logger = logger_tools.get_logger(self.__class__.__name__)

    def get_xicam_instance(self):
        return self.cam

    def open_device(self):
        """Open the camera."""
        self.logger.info("Opening camera...")
        self.cam.open_device()

    def close_device(self):
        """Close the camera."""
        self.logger.info("Closing camera...")
        self.cam.close_device()

    def start_acquisition(self):
        """Start data acquisition."""
        self.logger.info("Starting acquisition...")
        self.cam.start_acquisition()

    def stop_acquisition(self):
        """Stop data acquisition."""
        self.logger.info("Stopping acquisition...")
        self.cam.stop_acquisition()

    def start_capture_thread(self, stop_event=None):
        """
        Start a thread to capture images from the camera.
        Additionally provide a stop event to stop the thread.
        """
        self.stop_event = stop_event

        self.logger.info("Starting capture thread...")
        self.capture_thread = CaptureThread(self)
        self.capture_thread.start()

    def stop_capture_thread(self):
        """Stop the thread to capture images from the camera."""
        self.logger.info("Stopping capture thread...")
        self.capture_thread.stop()
        self.capture_thread.join()

    def get_image_from_buffer(self):
        """
        Get a single Image object from the image buffer.
        returns: Image object
        """
        with self.buffer_lock:
            if len(self.image_buffer) > 0:
                image = self.image_buffer.popleft()
                return image
            else:
                self.logger.warning("Image buffer is empty.")
                return None

    def get_metadata_from_frame(image):
        """Get a single image as numpy array with metadata for a the image."""

        metadata = Metadata()
        metadata.frame_id = image.acq_nframe
        metadata.timestamp = image.tsSec + image.tsUSec / 1e6
        metadata.exposure = image.exposure_time_us
        metadata.gain = image.gain_db
        metadata.width = image.width
        metadata.height = image.height
        metadata.img_format = image.frm

        return metadata
    
    def get_image_from_device(self, skipped_frames=None):
        """
        Get a single image as numpy array, gracefully return None if it fails
        skipped frames allow to skip given number of frames allowing 
        the camera to incrementally stabilize the auto exposure/gain and white balance
        returns: Image object
        """
        try:
            
            if skipped_frames is not None:
                for i in range(skipped_frames):
                    self.get_image_from_device(self.img)
            else:
                self.cam.get_image(self.img)

            image_data = self.img.get_image_data_numpy()

            if image_data is None:
                metadata = None
            else:
                metadata = self.get_metadata_from_frame(self.img)
                
            return Image(image_data, metadata)
        
        except: 
            #add Xi_error and error info
            self.logger.warning("Failed to get image frame")
            return None

    def configure_camera(self, manual=False):
        """Configure the camera with the necessary parameters."""

        self.logger.info("Configuring camera...")
        
        self.cam.set_imgdataformat("XI_RGB24")
        self.cam.enable_auto_wb()
        self.cam.enable_aeag()
        self.cam.set_exp_priority(0.5)
        self.cam.set_aeag_level(50)
        # self.cam.set_ae_max_limit(200000)
        # self.cam.set_ag_max_limit(12.0)
        if not manual:
            self.cam.set_trigger_source("XI_TRG_OFF")
            self.cam.set_trigger_selector("XI_TRG_SEL_FRAME_START")
            self.cam.set_trigger_overlap("XI_TRG_OVERLAP_OFF")
            self.cam.set_gpi_selector("XI_GPI_PORT1")
            self.cam.set_gpi_mode("XI_GPI_OFF")
            self.logger.info("Configured for continoues triggger...")
        else:
            self.cam.set_gpi_selector("XI_GPI_PORT1")
            self.cam.set_gpi_mode("XI_GPI_TRIGGER")
            self.cam.set_trigger_source("XI_TRG_EDGE_RISING")
            self.cam.set_trigger_selector("XI_TRG_SEL_FRAME_START")
            # self.cam.set_trigger_overlap("XI_TRG_OVERLAP_OFF")
            # self.cam.enable_dbnc_en()
            self.cam.set_dbnc_t0(100)
            self.cam.set_dbnc_t1(50)
            # self.cam.set_dbnc_pol(1)
            self.logger.info("Configured for manual hardware triggger...")

    # def configure_camera_settings(cam):

    # cam.set_imgdataformat('XI_RGB24')
    # # cam.set_exposure(200000) # us

    # cam.enable_auto_wb()
    # # cam.enable_horizontal_flip()
    # # cam.enable_vertical_flip()

    # cam.enable_aeag()
    # cam.set_exp_priority(0.5)
    # # Value: 1.0 >>> meaning: Exposure priority. Only exposure will be changed.
    # # Value: 0.5 >>> meaning: Exposure and gain will be used (50%:50%).
    # # Value: 0.0 >>> meaning: Gain priority. Only gain will be changed.

    # # cam.set_ag_max_limit(12.0) # gain limit
    # # ag_max_limit_min = cam.get_ag_max_limit_minimum()
    # # ag_max_limit_max = cam.get_ag_max_limit_maximum()
    # # ag_max_limit_inc = cam.get_ag_max_limit_increment()

    # # cam.set_ae_max_limit(200000) # exposure limit in us
    # cam.set_aeag_level(30) # target intensity of output signal AEAG should achieve(in %)

    # cam.set_trigger_source('XI_TRG_OFF')
    # # Note: To set input as external trigger, gpi_mode of selected input should be set to XI_GPI_TRIGGER. See example at gpi_mode .
    # # XI_TRG_OFF	        Capture of next image is automatically started after previous.
    # # XI_TRG_EDGE_RISING	Capture is started on rising edge of selected input.
    # # XI_TRG_EDGE_FALLING	Capture is started on falling edge of selected input
    # # XI_TRG_SOFTWARE	    Capture is started with software trigger.
    # # XI_TRG_LEVEL_HIGH	    Specifies that the trigger is considered valid as long as the level of the source signal is high.
    # # XI_TRG_LEVEL_LOW	    Specifies that the trigger is considered valid as long as the level of the source signal is low.

    # cam.set_trigger_selector('XI_TRG_SEL_FRAME_START') # Selects the type of trigger.
    # # XI_TRG_SEL_FRAME_START	    Trigger starts the capture of one frame.
    # # XI_TRG_SEL_EXPOSURE_START	    Trigger controls the start and length of the exposure.
    # # XI_TRG_SEL_EXPOSURE_START	    Trigger controls the start of the exposure of one Frame.
    # # XI_TRG_SEL_FRAME_BURST_START	Trigger starts the capture of the bursts of frames.
    # # more on documentation https://www.ximea.com/support/wiki/apis/XiAPI_Python_Manual#Trigger-selector

    # cam.set_trigger_overlap('XI_TRG_OVERLAP_OFF') #

    # cam.set_gpi_selector('XI_GPI_PORT1')
    # cam.set_gpi_mode('XI_GPI_OFF')
    # # Note1: To use GPI as trigger source, the trigger_source should be also set to XI_TRG_EDGE_RISING or XI_TRG_EDGE_FALLING
    # # Note2: If bidirectional (input/output) pin is used, set gpo_mode to XI_GPO_HIGH_IMPEDANCE. This will disable output driver on the pin from camera.
    # # XI_GPI_OFF	    Input is not used for triggering, but can be used to get parameter GPI_LEVEL. This can be used to switch I/O line on some cameras to input mode.
    # # XI_GPI_TRIGGER	Input can be used for triggering.
    # # XI_GPI_EXT_EVENT	External signal input (not implemented)

    # # gpi_level = cam.get_gpi_level() #  Read the level of digital input selected by gpi_selector.

    # # cam.enable_dbnc_en() # Enable/Disable debounce to selected GPI by gpi_selector.
    # # cam.set_dbnc_t0(100) # Debounce time (x * 10us) for transition to inactive level of GPI selected by dbnc_pol .
    # # cam.set_dbnc_t1(50) # Debounce time (x * 10us)for transition to active level of GPI selected by dbnc_pol
    # # cam.set_dbnc_pol(1) # Debounce polarity selects active level of GPI (see gpi_selector parameter). Does not inverts the signal if set.
    # # https://www.ximea.com/support/wiki/apis/XiAPI_Python_Manual#Debounce-polarity

    # # cam.set_gpo_selector('XI_GPO_PORT2')
    # # cam.set_gpo_mode(gpo_mode) # https://www.ximea.com/support/wiki/apis/XiAPI_Python_Manual#GPO-Mode

    # # framerate = cam.get_framerate()
    # timestamp = cam.get_timestamp()
    # isexist = cam.is_isexist()
    # # cam.set_param('exposure', 10000)
