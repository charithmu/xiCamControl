from ximea import xiapi
import cv2      

#create instance for first connected camera
cam = xiapi.Camera()

#start communication
print('Opening first camera...')
cam.open_device()

#settings
cam.set_imgdataformat('XI_RGB24')
cam.set_exposure(10000)

#create instance of Image to store image data and metadata
img = xiapi.Image()

#start data acquisition
print('Starting data acquisition...')
cam.start_acquisition()

#get data and pass them from camera to img
cam.get_image(img)

#create numpy array with data from camera. Dimensions of array are determined
#by imgdataformat
data = img.get_image_data_numpy()

#stop data acquisition
print('Stopping acquisition...')
cam.stop_acquisition()

#stop communication
cam.close_device()

#show acquired image
print('Drawing image...')
# cv2.imshow('XiCAM example', data)
# cv2.waitKey(0)
# cv2.destroyAllWindows()


# Resize the image with given width keeping the aspect ratio

def ResizeWithAspectRatio(image, width):
    r = width / image.shape[1]
    dim = (width, int(image.shape[0] * r))
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resized

# Rezie image by given percent keeping the aspect ratio

def ResizeWithPercent(image, percent):
    width = int(image.shape[1] * percent / 100)
    height = int(image.shape[0] * percent / 100)
    dim = (width, height)
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resized

def wait_with_check_closing(win_name):
    """ 
        https://stackoverflow.com/questions/35003476/"
        "opencv-python-how-to-detect-if-a-window-is-closed/37881722
    """
    while True:
        keyCode = cv2.waitKey(50)
        if keyCode != -1:
            break
        win_prop = cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE)
        if win_prop <= 0:
            break


cv2.namedWindow('Preview')
# Resize image to 800x600 keeping the aspect ratio
# resized = ResizeWithAspectRatio(data, width=800)
resized = ResizeWithPercent(data, percent=25)
cv2.imshow('Preview', resized)
wait_with_check_closing('Preview')
# cv2.waitKey(0)
cv2.destroyAllWindows()

print('Done.')
