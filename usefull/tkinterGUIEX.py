import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import sqlite3
from PIL import ImageTk, Image
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from simple_pyspin import Camera
from PIL import Image

root = tk.Tk()
root.title("GAP")

tabcontrol = ttk.Notebook(root)

InspectionFrame = ttk.Frame(tabcontrol)
ExaminationFrame = ttk.Frame(tabcontrol)

tabcontrol.add(InspectionFrame, text='Hata Tespit Sistemi')
tabcontrol.pack(expand=1, fill="both")

tabcontrol.add(ExaminationFrame, text="Kayıt İnceleme")
tabcontrol.pack(expand=1, fill="both")

# ******************************** Inspection Panel *************************************
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

# running camera through simple_pyspin wrapper for PySpin (in turn a wrapper for the Spinnaker C++ framework)

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


    def update_im():
        """ A function to continuously update the image while in live viewing mode.
        The global parameter update_freq (milliseconds) sets the update frequency.
        """
        if running:  # this will be set to True when you click the live viewing mode button
            global image
            image = cam.get_array()
            if zoomMode:
                image = image[422:542, 563:724]
            # global image
            # image = root.image
            im.set_data(image)
            im.set_cmap(cmap)
            canvas.draw()
            root.after(update_freq, update_im)  # this is units of milliseconds


    def update_gain(event):
        """ A function to update the camera gain, and change the text in the GUI.
        """
        val = int(Gain_Entry.get())
        cam.Gain = min(val, cam.get_info('Gain')['max'])  # don't allow it to exceed the camera max of 24
        Current_Gain.configure(text='Current Gain = %.3f' % float(cam.Gain))


    def update_exp(event):
        """ A function to update the exposure time, and change the text in the GUI.
        Currently, this will only actually do anything if you're not in live viewing mode.
        """
        val = int(Exp_Entry.get())
        if val > 100000:
            cam.AcquisitionFrameRateEnabled = False
        else:
            cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
            cam.AcquisitionFrameRateAuto = 'Off'
            cam.AcquisitionFrameRate = 8

        cam.ExposureTime = val
        Current_Exp_Micro.configure(text='Current Exposure Time = %.3f microseconds' % (cam.ExposureTime))
        Current_Exp_Milli.configure(
            text='Current Exposure Time = %.3f milliseconds' % (float(cam.ExposureTime) * 0.001))
        Current_Exp_Sec.configure(text='Current Exposure Time = %.3f seconds' % (float(cam.ExposureTime) * 1e-6))


    def update_sharp(event):
        """ A function to update the sharpness, and change the text in the GUI.
        """
        val = int(Sharp_Entry.get())
        cam.Sharpness = val  ### add in functionality to prevent user from exceeding the max
        Current_Sharp.configure(text='Current Sharpness = %.3f' % float(cam.Sharpness))


    def update_savename(event):
        global savename
        savename = str(Save_Entry.get())
        Save_Current.configure(text='(%s.png)' % savename)


    cam.start()  # now start acquiring data with the camera

    root = tk.Tk()  # set up the GUI
    root.wm_title("GAP Kumaş Denetleme Uygulaması")

    InspectionFrame = tk.Frame(root)
    InspectionFrame.grid(row=0, column=0, padx=10, pady=5)

    imageFrame = tk.Frame(root)
    imageFrame.grid(row=0, column=1, padx=10, pady=5)

    cmapFrame = tk.Frame(root)
    cmapFrame.grid(row=0, column=2, padx=10, pady=5)

    # set up the figure
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_yticks([])
    ax.set_xticks([])

    # global image
    image = cam.get_array()
    im = ax.imshow(image, vmin=0, vmax=255,
                   cmap=cmap)  # by default, we start showing the first image the camera was looking at

    canvas = FigureCanvasTkAgg(fig, master=imageFrame)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=4, columnspan=6, rowspan=6)


    def _quit():
        """ A function to exit the program.
        """
        root.quit()  # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate


    def _live():
        """ A function for live viewing mode in the GUI.
        """
        cam.stop()  # just in case
        cam.AcquisitionMode = 'Continuous'  # set acquisition mode to continuous
        cam.start()  # start acquiring data
        global running
        running = True  # need this for the uodate_im function, to keep updating the image
        val = cam.ExposureTime
        # print(val)
        cam.ExposureTime = val  # we force set an exposure time. If not, the update may be buggy
        # cam.ExposureTime = 10000 # we force set an exposure time. If not, the update may be buggy
        if running:
            cam.AcquisitionMode = 'Continuous'
            global update_freq
            update_freq = 50
            update_im()  # updates the image every 5 milliseconds


    def _single():
        """ A function to switch to single image viewing mode in the GUI.
        """
        cam.stop()
        cam.AcquisitionMode = 'SingleFrame'  # Switch the acquisition mode, so the camera isn't continuously taking data.
        cam.start()
        global running
        running = False  # stops the update_im functionality
        global image
        image = cam.get_array()  # gets current image
        if zoomMode:
            image = image[422:542, 563:724]
        im.set_data(image)  # sets view to current image
        im.set_cmap(cmap)
        canvas.draw()
        cam.stop()  # stop acquiring data while displaying a single image


    def _zoomIn():
        global zoomMode
        zoomMode = True
        if not running:
            _single()


    def _zoomOut():
        global zoomMode
        zoomMode = False
        if not running:
            _single()


    def _save():
        """ Just saves the current image.
        NEED TO:
        - set up functionality for changing the name
        - set up functionality for acquiring many images
        """
        # fig.savefig(savename+'.png', bbox_inches='tight', pad_inches=0)
        # image.dump('test.npy')
        save_im = Image.fromarray(image)
        save_im.save(savename + '.png')


    def _cmapGreys():
        global cmap
        cmap = 'Greys_r'


    def _cmapInferno():
        global cmap
        cmap = 'inferno'


    def _cmapJet():
        global cmap
        cmap = 'jet'


Gain_Label = tk.Label(master=InspectionFrame, text='Gain: ', font=('TkDefaultFont', 14, 'bold'))
Gain_Label.grid(row=0, sticky=tk.W)
Gain_Entry = tk.Entry(master=InspectionFrame)
Gain_Entry.bind("<Return>", update_gain)
Gain_Entry.grid(row=1, column=0)
Current_Gain = tk.Label(master=InspectionFrame, text='Current Gain = %.3f' % float(cam.Gain))
Current_Gain.grid(row=2, column=0, sticky=tk.W)

Exp_Label = tk.Label(master=InspectionFrame, text='Exposure Time (microseconds): ',
                     font=('TkDefaultFont', 14, 'bold'))
Exp_Label.grid(row=3, sticky=tk.W)
Exp_Entry = tk.Entry(master=InspectionFrame)
Exp_Entry.bind("<Return>", update_exp)
Exp_Entry.grid(row=4, column=0)
Current_Exp_Micro = tk.Label(master=InspectionFrame,
                             text='Current Exposure Time = %.3f microseconds' % (cam.ExposureTime))
Current_Exp_Micro.grid(row=5, column=0, sticky=tk.W)  # , columnspan=6)
Current_Exp_Milli = tk.Label(master=InspectionFrame, text='Current Exposure Time = %.3f milliseconds' % (
        float(cam.ExposureTime) * 0.001))
Current_Exp_Milli.grid(row=6, column=0, sticky=tk.W)  # columnspan=6)
Current_Exp_Sec = tk.Label(master=InspectionFrame,
                           text='Current Exposure Time = %.3f seconds' % (float(cam.ExposureTime) * 1e-6))
Current_Exp_Sec.grid(row=7, column=0, sticky=tk.W)  # , columnspan=6)

Sharp_Label = tk.Label(master=InspectionFrame, text='Sharpness: ', font=('TkDefaultFont', 14, 'bold'))
Sharp_Label.grid(row=8, sticky=tk.W)
Sharp_Entry = tk.Entry(master=InspectionFrame)
Sharp_Entry.bind("<Return>", update_sharp)
Sharp_Entry.grid(row=9, column=0)
Current_Sharp = tk.Label(master=InspectionFrame, text='Current Sharpness = %.3f' % float(cam.Sharpness))
Current_Sharp.grid(row=10, column=0, sticky=tk.W)

# image
button_live = tk.Button(master=InspectionFrame, text="Live Viewing Mode", command=_live)
button_live.grid(row=11, column=6)

button_singleImage = tk.Button(master=InspectionFrame, text="Single Image Mode", command=_single)
button_singleImage.grid(row=11, column=7)

button_zoomIn = tk.Button(master=InspectionFrame, text='Zoom In', command=_zoomIn)
button_zoomIn.grid(row=6, column=6)

button_zoomOut = tk.Button(master=InspectionFrame, text='Zoom Out', command=_zoomOut)
button_zoomOut.grid(row=6, column=7)

Save_Name = tk.Label(master=InspectionFrame, text='Save As: ')
Save_Name.grid(row=9, column=8)
Save_Entry = tk.Entry(master=InspectionFrame)
Save_Entry.bind("<Return>", update_savename)
Save_Entry.grid(row=9, column=8)
button_saveSingle = tk.Button(master=InspectionFrame, text='Save Current Image', command=_save)
button_saveSingle.grid(row=11, column=8)
Save_Current = tk.Label(master=InspectionFrame, text='(%s.png)' % savename)
Save_Current.grid(row=12, column=8)

# ******************************** Examination Panel *************************************
productName = ttk.Label(ExaminationFrame, text="Kayit bak: ")
productName.grid(column=0, row=2, sticky='W')

root.mainloop()
