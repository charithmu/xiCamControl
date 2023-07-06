from threading import Thread
from ximea import xiapi
 
class ImageMetadata:
    """A class to hold metadata for a single image."""
    frame_id = 0
    timestamp = 0
    gain = -1
    exposure = 0
    width = 0
    height = 0
    img_format = ""

#class used as a thread target which calls the camera's get_image_with_metadata_safe() method
#and saves it to a variable
class CaptureThread(Thread):
    def __init__(self, cam, stop_event):
        Thread.__init__(self)
        self.cam = cam
        self.data = None
        self.metadata = None
        self.stop_event = stop_event

    def run(self):
        while self.stop_event.wait(0) is not True:
            # print("CaptureThread running: trigger:"+ self.cam.get_xicam().get_trigger_source())
            data, metadata = self.cam.get_image_with_metadata_safe()
            if data is None:
                print("No image available")
                continue
            self.data = data
            self.metadata = metadata

    def stop(self):
        self.stop_event.set()

class XimeaCamera:
    """A class to control a Ximea camera."""

    def __init__(self):
        """Initialize the camera."""
        self.cam = xiapi.Camera()
        self.img = xiapi.Image()

    def get_xicam(self):
        return self.cam

    def open(self):
        """Open the camera."""
        print("Opening camera...")
        self.cam.open_device()

    def close(self):
        """Close the camera."""
        print("Closing camera...")
        self.cam.close_device()

    def start_acquisition(self):
        """Start data acquisition."""
        print("Starting acquisition...")
        self.cam.start_acquisition()

    def stop_acquisition(self):
        """Stop data acquisition."""
        print("Stopping acquisition...")
        self.cam.stop_acquisition()

    def get_image(self):
        """Get a single image as numpy array"""
        self.cam.get_image(self.img)
        return self.img.get_image_data_numpy()

    def get_image_safe(self):
        """Get a single image as numpy array, gracefully return None if it fails"""
        try:
            return self.get_image()
        except:
            return None

    def get_image_delayed(self, skipped_frames=50):
        """Get a single image as numpy array after skipping given number of frames
        This allows for the camera to adjust the auto exposure and gain and white balance settings
        """
        delayed_img_data = None
        for i in range(skipped_frames):
            delayed_img_data = self.get_image()

        return delayed_img_data

    def get_image_with_metadata(self):
        """Get a single image as numpy array with metadata for a the image."""
        self.cam.get_image(self.img)
        data = self.img.get_image_data_numpy()

        metadata = ImageMetadata()
        metadata.frame_id = self.img.acq_nframe
        metadata.timestamp = self.img.tsSec + self.img.tsUSec / 1e6
        metadata.exposure = self.img.exposure_time_us
        metadata.gain = self.img.gain_db
        metadata.width = self.img.width
        metadata.height = self.img.height
        metadata.img_format = self.img.frm

        return data, metadata
    
    # try to get the image with metadata, gracefully return None if it fails
    def get_image_with_metadata_safe(self):
        try:
            return self.get_image_with_metadata()
        except:
            return None, None

    def get_image_with_metadata_delayed(self, skipped_frames=50):
        """Get a single image as numpy array with metadata for a the image after skipping given number of frames
        This allows for the camera to adjust the auto exposure and gain and white balance settings
        """
        delayed_img_data = None
        delayed_img_metadata = None

        for i in range(skipped_frames):
            delayed_img_data, delayed_img_metadata = self.get_image_with_metadata()

        return delayed_img_data, delayed_img_metadata

    def configure_camera(self, manual=False):
        """Configure the camera with the necessary parameters."""
        print("Configuring camera...")
        self.cam.set_imgdataformat("XI_RGB24")
        self.cam.enable_auto_wb()
        self.cam.enable_aeag()
        self.cam.set_exp_priority(0.5)
        self.cam.set_aeag_level(30)
        # self.cam.set_ae_max_limit(200000)
        # self.cam.set_ag_max_limit(12.0)
        if not manual:
            self.cam.set_trigger_source("XI_TRG_OFF")
            self.cam.set_trigger_selector("XI_TRG_SEL_FRAME_START")
            self.cam.set_trigger_overlap("XI_TRG_OVERLAP_OFF")
            self.cam.set_gpi_selector("XI_GPI_PORT1")
            self.cam.set_gpi_mode("XI_GPI_OFF")
            print("Configured for continoues triggger...")
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
            print("Configured for manual hardware triggger...")


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
