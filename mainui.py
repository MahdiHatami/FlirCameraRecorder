import os
import tkinter as tk
from datetime import datetime
from skimage import transform
import numpy as np
import PySpin, imageio
import matplotlib.pyplot as plt

window = tk.Tk()
save_folder = 'capture_image/'
Capture_FPS = 5  # Less than 10 FPS for 20MP camera at 12bit.
ExposureTime = 2.44
image_bit = 16
image_width = 960
image_height = 600

if not os.path.exists(save_folder):
    os.mkdir(save_folder)


def save_img(image):
    time_str = str(datetime.datetime.fromtimestamp(image.GetTimeStamp() / 1e6))
    if image_bit == 16:
        img_nd = image.Convert(PySpin.PixelFormat_Mono16).GetNDArray()
    else:
        img_nd = image.GetNDArray()
    imageio.imsave('{}/{}.jpg'.format(save_folder, time_str), (
            transform.rescale(img_nd, 0.2, multichannel=False,
                              mode='constant', anti_aliasing=False,
                              preserve_range=False) * 255).round().astype(
        np.uint8))
    np.save('{}/{}'.format(save_folder, time_str), img_nd)


def handle_close(evt):
    global continue_recording
    continue_recording = False


def acquire_and_display_images(cam, nodemap, nodemap_tldevice):
    global continue_recording

    sNodemap = cam.GetTLStreamNodeMap()

    # Change bufferhandling mode to NewestOnly
    node_bufferhandling_mode = PySpin.CEnumerationPtr(
        sNodemap.GetNode('StreamBufferHandlingMode'))
    if not PySpin.IsAvailable(
            node_bufferhandling_mode) or not PySpin.IsWritable(
        node_bufferhandling_mode):
        print('Unable to set stream buffer handling mode.. Aborting...')
        return False

    # Retrieve entry node from enumeration node
    node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
    if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(
            node_newestonly):
        print('Unable to set stream buffer handling mode.. Aborting...')
        return False

    # Retrieve integer value from entry node
    node_newestonly_mode = node_newestonly.GetValue()

    # Set integer value from entry node as new value of enumeration node
    node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

    print('*** IMAGE ACQUISITION ***\n')
    try:
        node_acquisition_mode = PySpin.CEnumerationPtr(
            nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(
                node_acquisition_mode) or not PySpin.IsWritable(
            node_acquisition_mode):
            print(
                'Unable to set acquisition mode to continuous (enum '
                'retrieval). Aborting...')
            return False

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName(
            'Continuous')
        if not PySpin.IsAvailable(
                node_acquisition_mode_continuous) or not PySpin.IsReadable(
            node_acquisition_mode_continuous):
            print(
                'Unable to set acquisition mode to continuous (entry '
                'retrieval). Aborting...')
            return False

        # Retrieve integer value from entry node
        acquisition_mode_continuous = \
            node_acquisition_mode_continuous.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        cam.BeginAcquisition()

        print('Acquiring images...')

        #  Retrieve device serial number for filename
        device_serial_number = ''
        node_device_serial_number = PySpin.CStringPtr(
            nodemap_tldevice.GetNode('DeviceSerialNumber'))
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(
                node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()
            print(
                'Device serial number retrieved as %s...' %
                device_serial_number)

        # Close program
        print('Press enter to close the program..')

        # Figure(1) is default so you can omit this line. Figure(0) will
        # create a new window every time program hits this line
        fig = plt.figure(1)

        # Close the GUI when close event happens
        fig.canvas.mpl_connect('close_event', handle_close)

        # Retrieve and display images
        while continue_recording:
            try:
                #  Capturing an image houses images on the camera buffer. Trying
                #  to capture an image that does not exist will hang the camera.
                #
                #  Once an image from the buffer is saved and/or no longer
                #  needed, the image must be released in order to keep the
                #  buffer from filling up.

                image_result = cam.GetNextImage(1000)

                #  Ensure image completion
                if image_result.IsIncomplete():
                    print(
                        'Image incomplete with image status %d ...' %
                        image_result.GetImageStatus())

                else:
                    # Getting the image data as a numpy array
                    image_data = image_result.GetNDArray()

                    plt.imshow(image_data, cmap='gray')

                    plt.pause(0.001)
                    plt.clf()

                image_result.Release()

            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False

        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return True


def run_single_camera(cam):
    try:
        result = True

        nodemap_tldevice = cam.GetTLDeviceNodeMap()

        # Initialize camera

        cam.Init()

        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()

        # Acquire images
        result &= acquire_and_display_images(cam, nodemap, nodemap_tldevice)

        # Deinitialize camera
        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def setup_camera_params(cam):
    # setup gain
    cam.Width.SetValue(image_width)
    cam.Height.setValue(image_height)

    cam.GainAuto.SetValue(PySpin.GainAuto_Off)
    cam.Gain.SetValue(15)
    cam.GammaEnable.SetValue(False)

    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
    cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
    cam.ExposureMode.SetValue(PySpin.ExposureMode_Timed)
    cam.ExposureTime.SetValue(ExposureTime)

    # SensorShutterMode_Global = _PySpin.SensorShutterMode_Global
    # SensorShutterMode_Rolling = _PySpin.SensorShutterMode_Rolling
    # SensorShutterMode_GlobalReset = _PySpin.SensorShutterMode_GlobalReset
    # NUM_SENSORSHUTTERMODE = _PySpin.NUM_SENSORSHUTTERMODE
    cam.SensorShutterMode.SetValue(PySpin.SensorShutterMode_Global)
    cam.SensorShutter.SetValue(PySpin.NUM_SENSORSHUTTERMODE)

    cam.AcquisitionFrameRateEnable.SetValue(True)
    cam.AcquisitionFrameRate.SetValue(Capture_FPS)

    return cam


def startRecordingCallBack():
    result = True

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()

    # Finish if there are no cameras
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        print('Not enough cameras!')
        return False

    cam = cam_list.GetByIndex(0)
    cam = setup_camera_params(cam)
    result &= run_single_camera(cam)

    # Release reference to camera
    # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being
    # automatically
    # cleaned up when going out of scope.
    # The usage of del is preferred to assigning the variable to None.
    del cam

    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()

    return result


B = tk.Button(window, text="Kaydı Başlat", background='black',
              command=startRecordingCallBack)

B.pack()

window.title('GAP Tekstil')
window.geometry("900x700+10+10")
window.mainloop()
