import os
import tkinter as tk
from datetime import datetime
from tkinter import Button, messagebox

import PySpin
import imageio
import matplotlib.pyplot as plt
import numpy as np
from skimage import transform

save_folder = 'capture_image/'
Capture_FPS = 5
ExposureTime = 2.44
image_bit = 16
image_width = 960
image_height = 600

global continue_recording


class CamGUI(object):
    system = PySpin.System.GetInstance()

    def __init__(self):
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)

        self.cam_list = self.system.GetCameras()
        self.system = PySpin.System.GetInstance()
        self.cam = None
        self.continue_recording = True
        if self.cam is not None:
            self.sNodemap = self.cam.GetTLStreamNodeMap()
            self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
            self.nodemap = self.cam.GetNodeMap()

    @staticmethod
    def save_img(image):
        time_str = str(
            datetime.fromtimestamp(image.GetTimeStamp() / 1e6))
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

    def handle_close(self):
        self.continue_recording = True

    def acquire_and_display_images(self):
        try:
            self.cam = self.cam.Init()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)

        # Change buffer handling mode to NewestOnly
        node_bufferhandling_mode = PySpin.CEnumerationPtr(
            self.sNodemap.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(
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
                self.nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(
                    node_acquisition_mode):
                print(
                    'Unable to set acquisition mode to continuous (enum '
                    'retrieval). Aborting...')
                return False

            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                print(
                    'Unable to set acquisition mode to continuous (entry '
                    'retrieval). Aborting...')
                return False

            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            self.cam.BeginAcquisition()

            # Retrieve and display images
            while self.continue_recording:
                try:
                    image_result = self.cam.GetNextImage(1000)
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

            self.cam.EndAcquisition()

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return True

    def setup_camera_params(self):
        # setup gain
        self.cam.Width.SetValue(image_width)
        self.cam.Height.setValue(image_height)

        self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
        self.cam.Gain.SetValue(15)
        self.cam.GammaEnable.SetValue(False)

        self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        self.cam.ExposureMode.SetValue(PySpin.ExposureMode_Timed)
        self.cam.ExposureTime.SetValue(ExposureTime)

        # SensorShutterMode_Global = _PySpin.SensorShutterMode_Global
        # SensorShutterMode_Rolling = _PySpin.SensorShutterMode_Rolling
        # SensorShutterMode_GlobalReset = _PySpin.SensorShutterMode_GlobalReset
        # NUM_SENSORSHUTTERMODE = _PySpin.NUM_SENSORSHUTTERMODE
        self.cam.SensorShutterMode.SetValue(PySpin.SensorShutterMode_Global)
        self.cam.SensorShutter.SetValue(PySpin.NUM_SENSORSHUTTERMODE)

        self.cam.AcquisitionFrameRateEnable.SetValue(True)
        self.cam.AcquisitionFrameRate.SetValue(Capture_FPS)

    def stop_recording_callback(self):
        self.continue_recording = False
        if self.cam is not None:
            del self.cam
            self.cam_list.Clear()
            self.system.ReleaseInstance()

        messagebox.showinfo(title="Kayıt", message="Kayıt işlemi durduruldu")

    def start_recording_callback(self):
        num_cameras = self.cam_list.GetSize()

        # Finish if there are no cameras
        if num_cameras == 0:
            self.cam_list.Clear()
            self.system.ReleaseInstance()
            messagebox.showinfo(title="Kamera", message="Kamera Bağlantısı bulunamadı.")
            return False

        self.cam = self.cam_list.GetByIndex(0)
        self.setup_camera_params()
        self.acquire_and_display_images()

    def run_gui(self):
        master = tk.Tk()
        master.title("grid() method")
        master.geometry("500x300")
        master.minsize(500, 300)

        btn_start = Button(master, text="Kaydı Başlat",
                           command=self.start_recording_callback)
        btn_start.grid(row=1, column=0)

        btn_stop = Button(master, text="Kaydı Durdur",
                          command=self.stop_recording_callback)
        btn_stop.grid(row=2, column=0)

        # canvas = Canvas(master, width=300, height=300)
        # canvas.grid(row=3, column=1)
        # load = tk.Image("hata.jpg")
        # render = ImageTk.PhotoImage(load)
        # canvas.create_image(20, 20, image=render)

        master.mainloop()


if __name__ == "__main__":
    rec = CamGUI()
    rec.run_gui()
