import os
import tkinter as tk
from tkinter import Entry, Label, Button, StringVar, IntVar, Tk, END, \
    Radiobutton, filedialog, ttk
from datetime import datetime
from skimage import transform
import numpy as np
import PySpin, imageio
import matplotlib.pyplot as plt
import threading
import time
import ffmpy
import nidaqmx
import cv2

window = tk.Tk()
save_folder = 'capture_image/'
Capture_FPS = 5  # Less than 10 FPS for 20MP camera at 12bit.
ExposureTime = 2.44
ShutterTime = 0.444
image_bit = 16
image_width = 960
image_height = 600


class CamGUI(object):

    def __init__(self):
        self.window = None
        self.selectCams()

    def browse_output(self):
        filepath = filedialog.askdirectory()
        self.output.set(filepath)

    def init_cam(self, num):
        setup_window = Tk()
        Label(setup_window, text="Setting up camera, please wait...").pack()
        setup_window.update()

        if self.record_on.get():
            setup_window.destroy()
            cam_on_window = Tk()
            Label(cam_on_window,
                  text="Video is recording, cannot reinitialize camera!").pack()
            Button(cam_on_window, text="Ok",
                   command=lambda: cam_on_window.quit()).pack()
            cam_on_window.mainloop()
            cam_on_window.destroy()
            return

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
        cam = self.setup_camera_params(cam)

        # reset output directory
        self.output.set(self.output_entry['values'][cam])

        setup_window.destroy()

    def set_exposure(self, num):
        # check if camera set up
        if len(self.cam) < num + 1:
            cam_check_window = Tk()
            Label(cam_check_window,
                  text="No camera is found! \nPlease initialize camera before "
                       "setting exposure.").pack()
            Button(cam_check_window, text="Ok",
                   command=lambda: cam_check_window.quit()).pack()
            cam_check_window.mainloop()
            cam_check_window.destroy()
        else:
            self.cam[num].set_exposure(int(self.exposure[num].get()))

    def lv_interrupt(self, task_handle, signal_type, callback_data):

        try:
            return_code = 0
            if self.record_on.get():
                self.lv_ts.append(time.time())
                print("\nRecording timestamp %d" % len(self.lv_ts))
        except Exception as e:
            print(e)
            return_code = 1
        finally:
            return return_code

    def init_labview(self):

        if self.lv_task is None:

            lv_chan = self.labview_channel.get()
            if lv_chan != "":
                self.lv_task = nidaqmx.Task("read_behavior_ttl")
                self.lv_task.di_channels.add_di_chan(lv_chan)
                self.lv_task.timing.cfg_change_detection_timing(
                    rising_edge_chan=lv_chan)
                self.lv_task.register_signal_event(
                    nidaqmx.constants.Signal.CHANGE_DETECTION_EVENT,
                    self.lv_interrupt)
                self.lv_task.start()
                Label(self.window, text="Recording Timestamps!").grid(
                    row=3 * (int(self.number_of_cams.get())), column=2,
                    sticky="w")
            else:
                no_labview_window = Tk()
                Label(no_labview_window,
                      text="No labview channel selected, please select one "
                           "before initializing").pack()
                Button(no_labview_window, text="Ok",
                       command=lambda: no_labview_window.quit()).pack()
                no_labview_window.mainloop()
                no_labview_window.destroy()
        else:
            no_labview_window = Tk()
            Label(no_labview_window,
                  text="Labview task already started, please end this task "
                       "before beginning a new one").pack()
            Button(no_labview_window, text="Ok",
                   command=lambda: no_labview_window.quit()).pack()
            no_labview_window.mainloop()
            no_labview_window.destroy()

    def end_labview(self):
        if self.lv_task is not None:
            # self.lv_task.stop()
            self.lv_task.close()
            self.lv_task = None
            Label(self.window, text="").grid(row=3, column=2, sticky="nsew")

    def record_on_thread(self, num):
        fps = int(self.fps.get())
        start_time = time.time()
        next_frame = start_time

        try:
            while self.record_on.get():
                if time.time() >= next_frame:
                    self.frame_times[num].append(time.time())
                    self.vid_out[num].write(self.cam[num].get_image())
                    next_frame = max(next_frame + 1.0 / fps,
                                     self.frame_times[num][-1] + 0.5 / fps)
        except Exception as e:
            print(e)

    def start_record(self):
        if len(self.vid_out) == 0:
            remind_vid_window = Tk()
            Label(remind_vid_window,
                  text="VideoWriter not initialized! \nPlease set up video "
                       "and try again.").pack()
            Button(remind_vid_window, text="Ok",
                   command=lambda: remind_vid_window.quit()).pack()
            remind_vid_window.mainloop()
            remind_vid_window.destroy()
        else:
            self.vid_start_time = time.time()
            t = []
            for i in range(len(self.cam)):
                t.append(
                    threading.Thread(target=self.record_on_thread, args=(i,)))
                t[-1].daemon = True
                t[-1].start()

    def compress_vid(self, ind):
        ff_input = dict()
        ff_input[self.vid_file[ind]] = None
        ff_output = dict()
        out_file = self.vid_file[ind].replace('avi', 'mp4')
        ff_output[out_file] = '-c:v libx264 -crf 17'
        ff = ffmpy.FFmpeg(inputs=ff_input, outputs=ff_output)
        ff.run()

    def save_vid(self, compress=False, delete=False):

        saved_files = []

        # check that videos have been initialized

        if len(self.vid_out) == 0:
            not_initialized_window = Tk()
            Label(not_initialized_window,
                  text="Video writer is not initialized. Please set up first "
                       "to record a video.").pack()
            Button(not_initialized_window, text="Ok",
                   command=lambda: not_initialized_window.quit()).pack()
            not_initialized_window.mainloop()
            not_initialized_window.destroy()

        else:

            # check for frames before saving. if any video has not taken
            # frames, delete all videos
            frames_taken = all([len(i) > 0 for i in self.frame_times])

            # release video writer (saves file).
            # if no frames taken or delete specified, delete the file and do
            # not save timestamp files; otherwise, save timestamp files.
            for i in range(len(self.vid_out)):
                self.vid_out[i].release()
                self.vid_out[i] = None
                if (delete) or (not frames_taken):
                    os.remove(self.vid_file[i])
                else:
                    np.save(str(self.ts_file[i]), np.array(self.frame_times[i]))
                    saved_files.append(self.vid_file[i])
                    saved_files.append(self.ts_file[i])
                    if compress:
                        threading.Thread(
                            target=lambda: self.compress_vid(i)).start()

        if (len(self.lv_ts) > 0) and (not delete):
            np.save(str(self.lv_file), np.array(self.lv_ts))
            saved_files.append(self.lv_file)

        save_msg = ""
        if len(saved_files) > 0:
            save_msg = "The following files have been saved:"
            for i in saved_files:
                save_msg += "\n" + i
        elif delete:
            save_msg = "Video has been deleted, please set up a new video to " \
                       "take another recording."
        elif not frames_taken:
            save_msg = "Video was initialized but no frames were " \
                       "recorded.\nVideo has been deleted, please set up a " \
                       "new video to take another recording."

        if save_msg:
            save_window = Tk()
            Label(save_window, text=save_msg).pack()
            Button(save_window, text="Close",
                   command=lambda: save_window.quit()).pack()
            save_window.mainloop()
            save_window.destroy()

        self.vid_out = []
        self.frame_times = []
        self.current_file_label['text'] = ""

    def close_window(self):

        self.end_labview()
        if not self.setup:
            self.done = True
            self.window.destroy()
        else:
            self.done = True
            self.window.destroy()

    def selectCams(self):
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
        cam.Init()
        try:
            # Retrieve GenICam nodemap
            nodemap = cam.GetNodeMap()

            cam.DeInit()

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)

    def save_img(image):
        time_str = str(
            datetime.datetime.fromtimestamp(image.GetTimeStamp() / 1e6))
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
            node_acquisition_mode_continuous = \
                node_acquisition_mode.GetEntryByName(
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
            if PySpin.IsAvailable(
                    node_device_serial_number) and PySpin.IsReadable(
                node_device_serial_number):
                device_serial_number = node_device_serial_number.GetValue()
                print(
                    'Device serial number retrieved as %s...' %
                    device_serial_number)

            # Retrieve and display images
            while continue_recording:
                try:
                    image_result = cam.GetNextImage(1000)

                    #  Ensure image completion
                    if image_result.IsIncomplete():
                        print('Image incomplete with image status %d ...' %
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

    def setup_camera_params(cam):
        cam.Width.SetValue(image_width)
        cam.Height.setValue(image_height)

        # setup gain
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
        cam.SensorShutterTime.SetValue(ShutterTime)

        cam.AcquisitionFrameRateEnable.SetValue(True)
        cam.AcquisitionFrameRate.SetValue(Capture_FPS)

        return cam

    def createGUI(self):
        self.window = tk.Tk()
        self.window.title("Camera Control")

        cur_row = 0
        self.camera = []
        self.camera_entry = []
        self.exposure = []
        self.exposure_entry = []
        for i in range(int(self.number_of_cams.get())):
            # drop down menu to select camera
            Label(self.window, text="Camera " + str(i + 1) + ": ").grid(
                sticky="w", row=cur_row, column=0)
            self.camera.append(StringVar())
            self.camera_entry.append(
                ttk.Combobox(self.window, textvariable=self.camera[i]))
            self.camera_entry[i]['values'] = self.cam_names
            self.camera_entry[i].current(i)
            self.camera_entry[i].grid(row=cur_row, column=1)

            # inialize camera button
            if i == 0:
                Button(self.window, text="Initialize Camera 1",
                       command=lambda: self.init_cam(0)).grid(sticky="nsew",
                                                              row=cur_row + 1,
                                                              column=0,
                                                              columnspan=2)
            elif i == 1:
                Button(self.window, text="Initialize Camera 2",
                       command=lambda: self.init_cam(1)).grid(sticky="nsew",
                                                              row=cur_row + 1,
                                                              column=0,
                                                              columnspan=2)
            elif i == 2:
                Button(self.window, text="Initialize Camera 3",
                       command=lambda: self.init_cam(2)).grid(sticky="nsew",
                                                              row=cur_row + 1,
                                                              column=0,
                                                              columnspan=2)

            # change exposure
            self.exposure.append(StringVar())
            self.exposure_entry.append(
                Entry(self.window, textvariable=self.exposure[i]))
            self.exposure_entry[i].grid(sticky="nsew", row=cur_row, column=2)
            if i == 0:
                Button(self.window, text="Set Exposure 1",
                       command=lambda: self.set_exposure(0)).grid(sticky="nsew",
                                                                  row=cur_row
                                                                      + 1,
                                                                  column=2)
            elif i == 1:
                Button(self.window, text="Set Exposure 2",
                       command=lambda: self.set_exposure(1)).grid(sticky="nsew",
                                                                  row=cur_row
                                                                      + 1,
                                                                  column=2)
            elif i == 2:
                Button(self.window, text="Set Exposure 3",
                       command=lambda: self.set_exposure(2)).grid(sticky="nsew",
                                                                  row=cur_row
                                                                      + 1,
                                                                  column=2)

            # empty row
            Label(self.window, text="").grid(row=cur_row + 2, column=0)

            # end of camera loop
            cur_row = cur_row + 3

        # Labview Channel
        Label(self.window, text="Labview Channel: ").grid(sticky="w",
                                                          row=cur_row, column=0)
        self.labview_channel = StringVar(value="")
        self.labview_channel_entry = ttk.Combobox(self.window,
                                                  textvariable=self.labview_channel)
        self.labview_channel_entry['values'] = tuple(self.labview_channel_list)
        self.labview_channel_entry.grid(sticky="nsew", row=cur_row, column=1)
        Button(self.window, text="Initialize Labview",
               command=self.init_labview).grid(sticky="nsew", row=cur_row + 1,
                                               column=0, columnspan=2)
        Button(self.window, text="End LV", command=self.end_labview).grid(
            sticky="nsew", row=cur_row + 1, column=2)
        cur_row += 2

        # empty row
        Label(self.window, text="").grid(row=cur_row, column=0)
        cur_row += 1

        # subject name
        Label(self.window, text="Subject: ").grid(sticky="w", row=cur_row,
                                                  column=0)
        self.subject = StringVar()
        self.subject_entry = ttk.Combobox(self.window,
                                          textvariable=self.subject)
        self.subject_entry['values'] = tuple(self.mouse_list)
        self.subject_entry.grid(row=cur_row, column=1)
        cur_row += 1

        # attempt
        Label(self.window, text="Attempt: ").grid(sticky="w", row=cur_row,
                                                  column=0)
        self.attempt = StringVar(value="1")
        self.attempt_entry = ttk.Combobox(self.window,
                                          textvariable=self.attempt)
        self.attempt_entry['values'] = tuple(range(1, 10))
        self.attempt_entry.grid(row=cur_row, column=1)
        cur_row += 1

        # type frame rate
        Label(self.window, text="Frame Rate: ").grid(sticky="w", row=cur_row,
                                                     column=0)
        self.fps = StringVar()
        self.fps_entry = Entry(self.window, textvariable=self.fps)
        self.fps_entry.insert(END, '100')
        self.fps_entry.grid(sticky="nsew", row=cur_row, column=1)
        cur_row += 1

        # output directory
        Label(self.window, text="Output Directory: ").grid(sticky="w",
                                                           row=cur_row,
                                                           column=0)
        self.output = StringVar()
        self.output_entry = ttk.Combobox(self.window, textvariable=self.output)
        self.output_entry['values'] = self.output_dir
        self.output_entry.grid(row=cur_row, column=1)
        Button(self.window, text="Browse", command=self.browse_output).grid(
            sticky="nsew", row=cur_row, column=2)
        cur_row += 1

        Label(self.window, text="Current :: ").grid(row=cur_row, column=0,
                                                    sticky="w")
        self.current_file_label = Label(self.window, text="")
        self.current_file_label.grid(row=cur_row, column=1, sticky="w")
        cur_row += 1

        # empty row
        Label(self.window, text="").grid(row=cur_row, column=0)
        cur_row += 1

        # record button
        Label(self.window, text="Record: ").grid(sticky="w", row=cur_row,
                                                 column=0)
        self.record_on = IntVar(value=0)
        self.button_on = Radiobutton(self.window, text="On",
                                     selectcolor='green', indicatoron=0,
                                     variable=self.record_on, value=1,
                                     command=self.start_record).grid(
            sticky="nsew", row=cur_row, column=1)
        self.button_off = Radiobutton(self.window, text="Off",
                                      selectcolor='red', indicatoron=0,
                                      variable=self.record_on, value=0).grid(
            sticky="nsew", row=cur_row + 1, column=1)
        self.release_vid0 = Button(self.window, text="Save Video",
                                   command=lambda: self.save_vid(
                                       compress=False)).grid(sticky="nsew",
                                                             row=cur_row,
                                                             column=2)
        self.release_vid1 = Button(self.window, text="Compress & Save Video",
                                   command=lambda: self.save_vid(
                                       compress=True)).grid(sticky="nsew",
                                                            row=cur_row + 1,
                                                            column=2)
        self.release_vid2 = Button(self.window, text="Delete Video",
                                   command=lambda: self.save_vid(
                                       delete=True)).grid(sticky="nsew",
                                                          row=cur_row + 2,
                                                          column=2)
        cur_row += 3

        # close window/reset GUI
        Label(self.window).grid(row=cur_row, column=0)
        self.reset_button = Button(self.window, text="Reset GUI",
                                   command=self.selectCams).grid(sticky="nsew",
                                                                 row=cur_row
                                                                     + 1,
                                                                 column=0,
                                                                 columnspan=2)
        self.close_button = Button(self.window, text="Close",
                                   command=self.close_window).grid(
            sticky="nsew", row=cur_row + 2, column=0, columnspan=2)

    def runGUI(self):
        self.window.mainloop()


if __name__ == "__main__":
    rec = CamGUI()
    rec.runGUI()
