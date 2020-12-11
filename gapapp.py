import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

global image
image = np.zeros((960, 600))


def update_exp():
    """ A function to update the exposure time, and change the text in the GUI.
    Currently, this will only actually do anything if you're not in live viewing mode.
    """
    # val = int(Exp_Entry.get())
    # if val > 100000:
    #     cam.AcquisitionFrameRateEnabled = False
    # else:
    #     cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
    #     cam.AcquisitionFrameRateAuto = 'Off'
    #     cam.AcquisitionFrameRate = 8
    #
    # cam.ExposureTime = val
    # Current_Exp_Micro.configure(text='Current Exposure Time = %.3f microseconds' % (cam.ExposureTime))
    # Current_Exp_Milli.configure(
    #     text='Current Exposure Time = %.3f milliseconds' % (float(cam.ExposureTime) * 0.001))
    # Current_Exp_Sec.configure(text='Current Exposure Time = %.3f seconds' % (float(cam.ExposureTime) * 1e-6))


def update_sharp():
    """ A function to update the sharpness, and change the text in the GUI.
    """
    # val = int(Sharp_Entry.get())
    # cam.Sharpness = val  ### add in functionality to prevent user from exceeding the max
    # Current_Sharp.configure(text='Current Sharpness = %.3f' % float(cam.Sharpness))


def update_gain():
    """ A function to update the camera gain, and change the text in the GUI.
    """
    # val = int(Gain_Entry.get())
    # cam.Gain = min(val, cam.get_info('Gain')['max'])  # don't allow it to exceed the camera max of 24
    # Current_Gain.configure(text='Current Gain = %.3f' % float(cam.Gain))


def update_fps():
    """ A function to update the camera fps
    """
    # cam.AcquisitionFrameRate = 8
    # cam.pgrExposureCompensationAuto = 'Off'
    # cam.pgrExposureCompensation = 1.5


# run camera for GUI
# reset the parameters again, for safety

root = tk.Tk()  # Create instance
root.title('GAP Kumaş Hata Denetleme Sistemi')  # Add a title


# ------------------------------------------------------------- Tabs
tabControl = ttk.Notebook(root)  # Create Tab Control

tab1 = ttk.Frame(tabControl)  # Create a Tab
tab2 = ttk.Frame(tabControl)  # Create second Tab

tabControl.add(tab1, text='Kayıt / Hata Tespit')  # Add the Tab
tabControl.add(tab2, text='Hata Raporları')  # Add second Tab

tabControl.pack(expand=1, fill='both')  # Pack to make visible
# ------------------------------------------------------------- camera spec frame
camera_spec_frame = ttk.LabelFrame(tab1, text='Kamera Özellikleri')
camera_spec_frame.grid(row=0, column=0)

tk.Label(camera_spec_frame, text="Fps: ").grid(row=0)
tk.Label(camera_spec_frame, text="Gain: ").grid(row=1)
tk.Label(camera_spec_frame, text="Exposure: ").grid(row=2)
tk.Label(camera_spec_frame, text="Sharpness: ").grid(row=3)

fps_entry = tk.Entry(camera_spec_frame, width=10)
fps_entry.grid(row=0, column=1)
fps_entry.insert(0, 0)  # gain_entry.insert(0, cam.Gain)
fps_entry.bind("<Return>", update_fps)

gain_entry = tk.Entry(camera_spec_frame, width=10)
gain_entry.grid(row=1, column=1)
gain_entry.insert(0, 0)  # gain_entry.insert(0, cam.Gain)
gain_entry.bind("<Return>", update_gain)

exposure_entry = tk.Entry(camera_spec_frame, width=10)
exposure_entry.grid(row=2, column=1)
exposure_entry.insert(0, 0)  # gain_entry.insert(0, cam.Gain)
exposure_entry.bind("<Return>", update_exp)

sharp_entry = tk.Entry(camera_spec_frame, width=10)
sharp_entry.grid(row=3, column=1)
sharp_entry.insert(0, 0)  # gain_entry.insert(0, cam.Gain)
sharp_entry.bind("<Return>", update_sharp)

# ------------------------------------------------------------- defect detection frame
detection_frame = ttk.LabelFrame(tab1, text='Hata Tespiti')
detection_frame.grid(row=1, column=0, padx=8, pady=4)

# elements
action = ttk.Button(detection_frame, text="Hata Tespitine Başla")
action.grid(row=0, column=0, sticky='W')  # change column to 2

# ------------------------------------------------------------- image frame
image_frame = ttk.LabelFrame(tab1, text='Kamera Görüntüsü')
image_frame.grid(row=0, column=1, padx=8, pady=4)

# elements
a = ttk.Label(image_frame, text='Geçen Süre: /')
a.grid(row=0, column=0, sticky='W')

a = ttk.Label(image_frame, text='Üretilen Kumaş(metre): ')
a.grid(row=0, column=1, sticky='W')

# set up the figure
fig = Figure()
ax = fig.add_subplot(111)
ax.set_yticks([])
ax.set_xticks([])

# global image
# image = cam.get_array()
im = ax.imshow(image, vmin=0, vmax=600)  # by default, we start showing the first image the camera was looking at
canvas = FigureCanvasTkAgg(master=image_frame, figure=fig)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().grid(row=9, column=0, columnspan=6, rowspan=6)

root.mainloop()
