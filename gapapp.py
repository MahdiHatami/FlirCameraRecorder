import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

from matplotlib.figure import Figure
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from simple_pyspin import Camera

global camera
camera = None

global detection
detection = False

global image
image = np.zeros((960, 600))

global update_freq
update_freq = 50  # milliseconds

# global parameter for camera acquisition
global running
running = True


def update_exp():
    global camera
    val = int(exposure_entry.get())
    if val > 100000:
        camera.AcquisitionFrameRateEnabled = False
    else:
        camera.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
        camera.AcquisitionFrameRateAuto = 'Off'
        camera.AcquisitionFrameRate = 5

    camera.ExposureTime = val


def update_sharp():
    camera.Sharpness = int(sharp_entry.get())


def update_gain():
    global camera
    val = int(gain_entry.get())
    camera.Gain = min(val, camera.get_info('Gain')['max'])  # don't allow it to exceed the camera max of 24


def update_fps():
    camera.AcquisitionFrameRate = 8
    camera.pgrExposureCompensationAuto = 'Off'
    camera.pgrExposureCompensation = 1.5


def init_camera():
    with Camera() as cam:
        cam.init()

        cam.AcquisitionMode = 'Continuous'
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
        # Allow both long and short exposure times, without creating lag in live-viewing when  doing short.
        if cam.ExposureTime > 100000:
            cam.AcquisitionFrameRateEnabled = False  # if True, can uncomment the next two lines
        else:
            cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
            cam.AcquisitionFrameRateAuto = 'Off'
            cam.AcquisitionFrameRate = 8

        cam.pgrExposureCompensationAuto = 'Off'
        cam.pgrExposureCompensation = 1.5
        global camera
        camera = cam


def start_detection():
    global detection
    detection = True
    start_recording()


def start_recording():
    global camera
    try:
        init_camera()
    except:
        messagebox.showinfo(title="Kamera", message="Kamera Bağlantısı bulunamadı.")

    camera.start()  # start acquiring data

    global running, update_freq
    running = True
    if running:
        update_freq = 50
        update_im()


def predict_defect_image(image):
    # 1s -> 10mm

    # 6 paracaya bol

    # 6 goruntu icin predict

    # hataliyi kaydet

    # tahminiHataZaman(s) = hata buldugu saat - baslangic saat

    # tahiniHataKonum = tahminiHataZaman * 10mm

    # rapor icin veri kaydi

    # goruntuyu klasore kaydet

    # veri tabani kismi
        # kumasin kayit baslangic saaati (timestamp)
        # hata saati (timestamp)
        # hatali goruntunun yolu
        # onay (goruntu dogru bulmus mu)


    pass


def save_image(image):
    # time_str = str(datetime.fromtimestamp(image.GetTimeStamp() / 1e6))
    # image_converted = image.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
    # filename = '%s-%d.jpg' % (time_str, i)
    pass


def update_im():
    if running:
        global image, camera, detection

        # image = root.image
        image = camera.get_array()

        if detection:
            predict_defect_image(image)
        else:
            save_image(image)

        im = ax.imshow(image, vmin=0, vmax=255)
        im.set_data(image)
        canvas.draw()
        root.after(update_freq, update_im)  # this is units of milliseconds


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

start_record_button = ttk.Button(camera_spec_frame, text="Kayıt Yap", command=start_recording)
start_record_button.grid(row=5, column=0, pady=10)  # change column to 2

# ------------------------------------------------------------- defect detection frame
detection_frame = ttk.LabelFrame(tab1, text='Hata Tespiti')
detection_frame.grid(row=1, column=0, padx=8, pady=4)

# elements
action = ttk.Button(detection_frame, text="Hata Tespitine Başla", command=start_detection)
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
canvas = FigureCanvasTkAgg(master=image_frame, figure=fig)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().grid(row=9, column=0, columnspan=6, rowspan=6)

root.mainloop()
