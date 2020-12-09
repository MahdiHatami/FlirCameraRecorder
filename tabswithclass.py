import os
from PIL import Image
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk
from matplotlib.figure import Figure
from datetime import datetime
from tkinter import Button, messagebox
import numpy as np
import PySpin
from simple_pyspin import Camera

save_folder = 'capture_image/'
Capture_FPS = 5
ExposureTime = 2.44
image_bit = 16
image_width = 960
image_height = 600
# create global parameters
# global parameter for upate frequency of camera image in live view
global update_freq
update_freq = 50  # milliseconds

# global parameter for camera acquisition
global running
running = True

global savename
savename = 'image'

global cmap
cmap = 'Greys_r'

global image
image = np.zeros((964, 1288))

global zoomMode
zoomMode = False

ColorMapOptions = ['Greys_r', 'inferno', 'viridis', 'jet']


class CamGUI(object):
    # Retrieve singleton reference to system object
    cam = None

    def __init__(self):
        # reset camera to default parameters
        # the camera will remember parameters from the last run, so it's important to reset them here
        with Camera() as cam:
            cam.init()
            cam.AcquisitionMode = 'SingleFrame'
            cam.SharpnessEnabled = True
            cam.SharpnessAuto = 'Off'
            cam.Sharpness = 750
            cam.ExposureAuto = 'Off'
            cam.ExposureTime = 10000
            cam.GainAuto = 'Off'
            gain = min(0, cam.get_info('Gain')['max'])
            cam.Gain = gain
            cam.AcquisitionFrameRateEnabled = True
            cam.AcquisitionFrameRateAuto = 'Off'
            cam.AcquisitionFrameRate = 8
            cam.pgrExposureCompensationAuto = 'Off'
            cam.pgrExposureCompensation = 1.5
        # run camera for GUI
        # reset the parameters again, for safety
        with Camera() as cam:
            cam.init()  # initialize the camera

            # cam.AcquisitionMode = 'Continuous' # continuous acquisition mode
            cam.AcquisitionMode = 'SingleFrame'  # single acquisition mode

            cam.SharpnessEnabled = True  # allow sharpness to be controlled
            # if we turn this off, need to comment out the next two lines
            cam.SharpnessAuto = 'Off'  # turn off auto sharpness
            cam.Sharpness = 750  # set the sharpness to zero to start

            cam.GainAuto = 'Off'  # turn automatic gain off
            gain = min(0, cam.get_info('Gain')['max'])  # don't allow the gain to exceed the max gain of 24
            cam.Gain = gain  # set the camera gain to 0

            cam.ExposureAuto = 'Off'  # turn off auto exposure
            cam.ExposureTime = 10000  # microseconds

            # Allow both long and short exposure times, without creating lag in live-viewing when  doing short.
            if cam.ExposureTime > 100000:
                cam.AcquisitionFrameRateEnabled = False  # if True, can uncomment the next two lines
            else:
                cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
                cam.AcquisitionFrameRateAuto = 'Off'
                cam.AcquisitionFrameRate = 8

            cam.pgrExposureCompensationAuto = 'Off'
            cam.pgrExposureCompensation = 1.5

        self.root = tk.Tk()  # set up the GUI
        self.root.wm_title("GAP Kumaş Denetleme Uygulaması")

        self.display_area = ttk.Labelframe(self.root, text=' Tab Display Area ')
        self.display_area.grid(column=0, row=1, sticky='WE')

        self.settingsFrame = tk.Frame(self.root)
        self.settingsFrame.grid(row=0, column=0, padx=10, pady=5)

        self.imageFrame = tk.Frame(self.root)
        self.imageFrame.grid(row=0, column=1, padx=10, pady=5)

    def update_im(self):
        """ A function to continuously update the image while in live viewing mode.
        The global parameter update_freq (milliseconds) sets the update frequency.
        """
        if running:  # this will be set to True when you click the live viewing mode button
            global image
            image = self.cam.get_array()
            if zoomMode:
                image = image[422:542, 563:724]
            # global image
            # image = root.image
            self.im.set_data(image)
            self.im.set_cmap(cmap)
            self.canvas.draw()
            self.root.after(update_freq, self.update_im)  # this is units of milliseconds

    def update_gain(self, event):
        """ A function to update the camera gain, and change the text in the GUI.
        """
        val = int(Gain_Entry.get())
        self.cam.Gain = min(val, self.cam.get_info('Gain')['max'])  # don't allow it to exceed the camera max of 24
        Current_Gain.configure(text='Current Gain = %.3f' % float(self.cam.Gain))

    def update_exp(self, event):
        """ A function to update the exposure time, and change the text in the GUI.
        Currently, this will only actually do anything if you're not in live viewing mode.
        """
        val = int(Exp_Entry.get())
        if val > 100000:
            self.cam.AcquisitionFrameRateEnabled = False
        else:
            self.cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
            self.cam.AcquisitionFrameRateAuto = 'Off'
            self.cam.AcquisitionFrameRate = 8

        self.cam.ExposureTime = val
        Current_Exp_Micro.configure(text='Current Exposure Time = %.3f microseconds' % (self.cam.ExposureTime))
        Current_Exp_Milli.configure(
            text='Current Exposure Time = %.3f milliseconds' % (float(self.cam.ExposureTime) * 0.001))
        Current_Exp_Sec.configure(text='Current Exposure Time = %.3f seconds' % (float(self.cam.ExposureTime) * 1e-6))

    def update_sharp(self, event):
        """ A function to update the sharpness, and change the text in the GUI.
        """
        val = int(Sharp_Entry.get())
        ### add in functionality to prevent user from exceeding the max
        self.cam.Sharpness = val
        Current_Sharp.configure(text='Current Sharpness = %.3f' % float(self.cam.Sharpness))

    def update_savename(self, event):
        global savename
        savename = str(Save_Entry.get())
        Save_Current.configure(text='(%s.jpg)' % savename)

    def notebook_callback(self, event):
        self.clear_display_area()

        current_notebook = str(event.widget)
        tab_no = str(event.widget.index("current") + 1)

        if current_notebook.endswith('notebook'):
            active_notebook = 'Notebook 1'
        elif current_notebook.endswith('notebook2'):
            active_notebook = 'Notebook 2'
        else:
            active_notebook = ''

        if active_notebook is 'Notebook 1':
            if tab_no == '1':
                self.display_tab1()
            elif tab_no == '2':
                self.display_tab1()

    def clear_display_area(self):
        for widget in self.display_area.grid_slaves():
            if int(widget.grid_info()["row"]) == 0:
                widget.grid_forget()

    def display_tab1(self):
        button_quit = tk.Button(master=self.root, text="Quit", command=self._quit)
        button_quit.grid(row=13, column=0)

        Gain_Label = tk.Label(master=self.settingsFrame, text='Gain: ', font=('TkDefaultFont', 14, 'bold'))
        Gain_Label.grid(row=0, sticky=tk.W)
        Gain_Entry = tk.Entry(master=self.settingsFrame)
        Gain_Entry.bind("<Return>", self.update_gain)
        Gain_Entry.grid(row=1, column=0)
        Current_Gain = tk.Label(master=self.settingsFrame, text='Current Gain = %.3f' % float(self.cam.Gain))
        Current_Gain.grid(row=2, column=0, sticky=tk.W)

        Exp_Label = tk.Label(master=self.settingsFrame, text='Exposure Time (microseconds): ',
                             font=('TkDefaultFont', 14, 'bold'))
        Exp_Label.grid(row=3, sticky=tk.W)
        Exp_Entry = tk.Entry(master=self.settingsFrame)
        Exp_Entry.bind("<Return>", self.update_exp)
        Exp_Entry.grid(row=4, column=0)
        Current_Exp_Micro = tk.Label(master=self.settingsFrame,
                                     text='Current Exposure Time = %.3f microseconds' % (self.cam.ExposureTime))
        Current_Exp_Micro.grid(row=5, column=0, sticky=tk.W)  # , columnspan=6)
        Current_Exp_Milli = tk.Label(master=self.settingsFrame, text='Current Exposure Time = %.3f milliseconds' % (
                float(self.cam.ExposureTime) * 0.001))
        Current_Exp_Milli.grid(row=6, column=0, sticky=tk.W)  # columnspan=6)
        Current_Exp_Sec = tk.Label(master=self.settingsFrame,
                                   text='Current Exposure Time = %.3f seconds' % (float(self.cam.ExposureTime) * 1e-6))
        Current_Exp_Sec.grid(row=7, column=0, sticky=tk.W)  # , columnspan=6)

        Sharp_Label = tk.Label(master=self.settingsFrame, text='Sharpness: ', font=('TkDefaultFont', 14, 'bold'))
        Sharp_Label.grid(row=8, sticky=tk.W)
        Sharp_Entry = tk.Entry(master=self.settingsFrame)
        Sharp_Entry.bind("<Return>", self.update_sharp)
        Sharp_Entry.grid(row=9, column=0)
        Current_Sharp = tk.Label(master=self.settingsFrame, text='Current Sharpness = %.3f' % float(self.cam.Sharpness))
        Current_Sharp.grid(row=10, column=0, sticky=tk.W)

        button_live = tk.Button(master=self.imageFrame, text="Live Viewing Mode", command=self._live)
        button_live.grid(row=11, column=6)

        button_singleImage = tk.Button(master=self.imageFrame, text="Single Image Mode", command=self._single)
        button_singleImage.grid(row=11, column=7)

        button_zoomIn = tk.Button(master=self.imageFrame, text='Zoom In', command=self._zoomIn)
        button_zoomIn.grid(row=6, column=6)

        button_zoomOut = tk.Button(master=self.imageFrame, text='Zoom Out', command=self._zoomOut)
        button_zoomOut.grid(row=6, column=7)

        Save_Name = tk.Label(master=self.imageFrame, text='Save As: ')
        Save_Name.grid(row=9, column=8)
        Save_Entry = tk.Entry(master=self.imageFrame)
        Save_Entry.bind("<Return>", self.update_savename)
        Save_Entry.grid(row=9, column=8)
        button_saveSingle = tk.Button(master=self.imageFrame, text='Save Current Image', command=self._save)
        button_saveSingle.grid(row=11, column=8)
        Save_Current = tk.Label(master=self.imageFrame, text='(%s.jpg)' % savename)
        Save_Current.grid(row=12, column=8)

    def _quit(self):
        """ A function to exit the program.
        """
        self.root.quit()  # stops mainloop
        self.root.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def _live(self):
        """ A function for live viewing mode in the GUI.
        """
        self.cam.stop()  # just in case
        self.cam.AcquisitionMode = 'Continuous'  # set acquisition mode to continuous
        self.cam.start()  # start acquiring data
        global running
        running = True  # need this for the uodate_im function, to keep updating the image
        val = self.cam.ExposureTime
        # print(val)
        self.cam.ExposureTime = val  # we force set an exposure time. If not, the update may be buggy
        # cam.ExposureTime = 10000 # we force set an exposure time. If not, the update may be buggy
        if running:
            self.cam.AcquisitionMode = 'Continuous'
            global update_freq
            update_freq = 50
            self.update_im()  # updates the image every 5 milliseconds

    def _single(self):
        """ A function to switch to single image viewing mode in the GUI.
        """
        self.cam.stop()
        self.cam.AcquisitionMode = 'SingleFrame'  # Switch the acquisition mode, so the camera isn't continuously taking data.
        self.cam.start()
        global running
        running = False  # stops the update_im functionality
        global image
        image = self.cam.get_array()  # gets current image
        if zoomMode:
            image = image[422:542, 563:724]
        self.im.set_data(image)  # sets view to current image
        self.im.set_cmap(cmap)
        self.canvas.draw()
        self.cam.stop()  # stop acquiring data while displaying a single image

    def _zoomIn(self):
        global zoomMode
        zoomMode = True
        if not running:
            self._single()

    def _zoomOut(self):
        global zoomMode
        zoomMode = False
        if not running:
            self._single()

    def _save(self):
        save_im = Image.fromarray(image)
        save_im.save(savename + '.jpg')

    def _cmapGreys(self):
        global cmap
        cmap = 'Greys_r'

    def _cmapInferno(self):
        global cmap
        cmap = 'inferno'

    def _cmapJet(self):
        global cmap
        cmap = 'jet'

    def run_gui(self):
        self.cam.start()  # now start acquiring data with the camera

        note1 = ttk.Notebook(self.root)
        note1.grid(column=0, row=0)

        note2 = ttk.Notebook(self.root)
        note2.grid(column=0, row=1)

        tab1 = ttk.Frame(note1, width=0, height=0)  # Create a tab for notebook 1
        tab2 = ttk.Frame(note2, width=0, height=0)  # Create a tab for notebook 2
        note1.add(tab1, text='Hata Tespit')  # Add tab notebook 1
        note2.add(tab2, text='Hata Inceleme')  # Add tab notebook 2

        note1.bind("<ButtonRelease-1>", self.notebook_callback)
        note2.bind("<ButtonRelease-1>", self.notebook_callback)

        # set up the figure
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.set_yticks([])
        ax.set_xticks([])

        # global image
        image = self.cam.get_array()
        # by default, we start showing the first image the camera was looking at
        self.im = ax.imshow(image, vmin=0, vmax=255, cmap=cmap)

        canvas = FigureCanvasTkAgg(fig, master=self.imageFrame)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=4, columnspan=6, rowspan=6)

        # update_im()
        tk.mainloop()

        self.cam.stop()


if __name__ == "__main__":
    rec = CamGUI()
    rec.run_gui()
