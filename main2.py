import PySpin, time, datetime, imageio, threading
import numpy as np
from skimage import transform
import matplotlib.pyplot as plt
import os

save_folder = '/capture_image/captured'
ExposureTime = 10  # in millisecond
Capture_FPS = 5.  # Less than 10 FPS for 20MP camera at 12bit.
Gain = 0.
ReverseX = False
ReverseY = False
bit = 8

if not os.path.exists(save_folder):
    os.mkdir(save_folder)

# Get system
system = PySpin.System.GetInstance()
# Get camera list
cam_list = system.GetCameras()
cam = cam_list.GetByIndex(0)
cam.Init()
# load default configuration
cam.UserSetSelector.SetValue(PySpin.UserSetSelector_Default)
cam.UserSetLoad()

# set acquisition. Continues acquisition. Auto exposure off. Set frame rate.
cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
cam.ExposureMode.SetValue(PySpin.ExposureMode_Timed)
cam.ExposureTime.SetValue(ExposureTime * 1e3)
cam.AcquisitionFrameRateEnable.SetValue(True)
cam.AcquisitionFrameRate.SetValue(Capture_FPS)

# set analog. Set Gain. Turn off Gamma.
cam.GainAuto.SetValue(PySpin.GainAuto_Off)
cam.Gain.SetValue(Gain)
cam.GammaEnable.SetValue(False)

# set image format. 12 bit ADC. Image format Mono12p.
cam.ReverseX.SetValue(ReverseX)
cam.ReverseY.SetValue(ReverseY)
if bit > 8:
    image_bit = 16

    cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit12)
    cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono12p)
else:
    image_bit = 8
    cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit10)
    cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
max_grayscale = 2 ** image_bit - 1

# Iteratively accquiring test image and adjusting the exposure time.
cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
while True:
    cam.BeginAcquisition()
    if image_bit == 16:
        test_image = cam.GetNextImage().Convert(PySpin.PixelFormat_Mono16).GetNDArray()
    else:
        test_image = cam.GetNextImage().GetNDArray()

    # convert mono image into RGB and mark highligh region into red
    plot_image = np.repeat(test_image[:, :, np.newaxis], 3, axis=2)
    overexposed_location = np.where(plot_image >= max_grayscale * 0.99)[:2]
    plot_image[overexposed_location] = (max_grayscale, 0, 0)
    plot_image = plot_image.astype(np.float) / max_grayscale

    plt.figure()
    plt.imshow(plot_image, cmap='gray')
    plt.pause(0.5)

    # plot histogram of grayscale
    plt.figure()
    plt.hist(np.ravel(test_image), bins=100)
    plt.xlim(0, max_grayscale)
    plt.pause(0.5)

    print('Image value: min = {}, max = {}'.format(np.min(test_image), np.max(test_image)))
    answer = input(
        '''Enter 'y' to accept current exposure time {:d}ms, or enter a new exposure time in millisecond: '''.format(
            ExposureTime))
    if answer.lower() == 'y':
        plt.close('all')
        cam.EndAcquisition()
        break
    else:
        ExposureTime = int(answer)
        cam.EndAcquisition()
        cam.ExposureTime.SetValue(ExposureTime * 1e3)
        plt.close('all')
cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

print('Exposure time: {:d}ms'.format(int(cam.ExposureTime.GetValue() / 1e3)))


def save_img(image):
    # convert PySpin image object into ND array, rescale the image, save small jpg image and the ND array.

    time_str = str(datetime.datetime.fromtimestamp(image.GetTimeStamp() / 1e6))
    if image_bit == 16:
        img_nd = image.Convert(PySpin.PixelFormat_Mono16).GetNDArray()
    else:
        img_nd = image.GetNDArray()
    imageio.imsave('{}/{}.jpg'.format(save_folder, time_str), (
            transform.rescale(img_nd, 0.2, multichannel=False, mode='constant', anti_aliasing=False,
                              preserve_range=False) * 255).round().astype(np.uint8))
    np.save('{}/{}'.format(save_folder, time_str), img_nd)


try:
    input('Images will be saved to folder {}\nPress enter to start. Press ctrl+c to stop'.format(save_folder))
    cam.BeginAcquisition()
    t1 = time.time()
    i = 0
    save_threads = []
    while True:
        print(i)
        image = cam.GetNextImage()
        # multithreads to accelerate saving and avoid filling up the buff of the camera
        save_threads.append(threading.Thread(target=save_img, args=(image,)))
        save_threads[-1].start()
        i += 1
except KeyboardInterrupt:
    pass

for thread in save_threads:
    thread.join()

t2 = time.time()
print('Capturing time: {:.3f}s'.format(t2 - t1))
print('AcquisitionResultingFrameRate: {:.2f}FPS'.format(cam.AcquisitionResultingFrameRate()))

cam.EndAcquisition()
cam.UserSetSelector.SetValue(PySpin.UserSetSelector_Default)
cam.UserSetLoad()
cam.DeInit()
cam_list.Clear()
del image
del cam
del cam_list
system.ReleaseInstance()
