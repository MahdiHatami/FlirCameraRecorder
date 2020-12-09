from tkinter import Tk as tk, Label, Button, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from simple_pyspin import Camera
from PIL import Image


class Inspection:
    def __init__(self, root):

        # with Camera() as cam:
        #     cam.init()
        #
        #     cam.AcquisitionMode = 'SingleFrame'
        #     cam.SharpnessEnabled = True
        #     cam.SharpnessAuto = 'Off'
        #     cam.Sharpness = 750
        #     cam.ExposureAuto = 'Off'
        #     cam.ExposureTime = 10000
        #     cam.GainAuto = 'Off'
        #     gain = min(0, cam.get_info('Gain')['max'])
        #     cam.Gain = gain
        #     cam.AcquisitionFrameRateEnabled = True
        #     cam.AcquisitionFrameRateAuto = 'Off'
        #     cam.AcquisitionFrameRate = 8
        #     cam.pgrExposureCompensationAuto = 'Off'
        #     cam.pgrExposureCompensation = 1.5
        #
        # # run camera for GUI
        # # reset the parameters again, for safety
        # with Camera() as cam:
        #     cam.init()  # initialize the camera
        #
        #     # cam.AcquisitionMode = 'Continuous' # continuous acquisition mode
        #     cam.AcquisitionMode = 'SingleFrame'  # single acquisition mode
        #
        #     cam.SharpnessEnabled = True  # allow sharpness to be controlled
        #     # if we turn this off, need to comment out the next two lines
        #     cam.SharpnessAuto = 'Off'  # turn off auto sharpness
        #     cam.Sharpness = 750  # set the sharpness to zero to start
        #
        #     cam.GainAuto = 'Off'  # turn automatic gain off
        #     gain = min(0, cam.get_info('Gain')['max'])  # don't allow the gain to exceed the max gain of 24
        #     cam.Gain = gain  # set the camera gain to 0
        #
        #     cam.ExposureAuto = 'Off'  # turn off auto exposure
        #     cam.ExposureTime = 10000  # microseconds
        #
        #     # Allow both long and short exposure times, without creating lag in live-viewing when  doing short.
        #     if cam.ExposureTime > 100000:
        #         cam.AcquisitionFrameRateEnabled = False  # if True, can uncomment the next two lines
        #     else:
        #         cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
        #         cam.AcquisitionFrameRateAuto = 'Off'
        #         cam.AcquisitionFrameRate = 8
        #
        #     cam.pgrExposureCompensationAuto = 'Off'
        #     cam.pgrExposureCompensation = 1.5

        settingsFrame = tk.Frame(root)
        settingsFrame.grid(row=0, column=0, padx=10, pady=5)

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
        im = ax.imshow(image, vmin=0, vmax=255)

        canvas = FigureCanvasTkAgg(fig, master=imageFrame)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_wid


root = tk.Tk()
my_gui = Inspection(root)
root.mainloop()
