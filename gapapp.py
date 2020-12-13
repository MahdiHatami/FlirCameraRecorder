import os
import tkinter as tk
import numpy as np
import tensorflow as tf
import time
from tkinter import ttk
from tkinter import messagebox
from PIL import Image
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from simple_pyspin import Camera

fabric_speed = 10  # 10 mm/s
defect_folder = ""
save_folder = ""
folder_sep = ""

global camera_fps, camera_gain, camera_exp, camera_sharp
camera_fps = 5
camera_gain = 15
camera_exp = 10000
camera_sharp = 2100

global timer, camera, detection, image, update_freq, running, index, current_dir
timer = 1
camera = None
detection = False
image = np.zeros((960, 600))
update_freq = 50  # milliseconds
running = True
index = 1

model = tf.keras.models.load_model('assets/network.h5')

if os.name == 'posix':
    defect_folder = "/Users/metis/Desktop/Hata"
    save_folder = "/Users/metis/Desktop/Kayit"
    folder_sep = "/"
    if not os.path.exists(defect_folder):
        os.makedirs(defect_folder)
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
else:
    defect_folder = "C:\Hata"
    save_folder = "C:\Kayit"
    folder_sep = "\\"
    if not os.path.exists(defect_folder):
        os.makedirs(defect_folder)
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

sliced_pos = {
    (0, 0, 320, 300),
    (321, 0, 640, 300),
    (641, 0, 960, 300),
    (0, 300, 320, 600),
    (321, 301, 641, 600),
    (641, 301, 960, 600)
}


# def update_exp():
#     global camera, camera_exp
#     val = int(exposure_entry.get())
#     if val > 100000:
#         camera.AcquisitionFrameRateEnabled = False
#     else:
#         camera.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
#         camera.AcquisitionFrameRateAuto = 'Off'
#         camera.AcquisitionFrameRate = camera_fps
#
#     camera.ExposureTime = val
#
#     camera_exp = val
#
#
# def update_sharp():
#     global camera_sharp
#     sharp = int(sharp_entry.get())
#     camera.Sharpness = sharp
#
#     camera_sharp = sharp
#
#
# def update_gain():
#     global camera, camera_gain
#     val = int(gain_entry.get())
#     val = min(val, camera.get_info('Gain')['max'])  # don't allow it to exceed the camera max of 24
#     camera.Gain = val
#
#     camera_gain = val
#
#
# def update_fps():
#     entry_fps = fps_entry.get()
#     camera_fps = entry_fps
#     camera.AcquisitionFrameRate = entry_fps
#     camera.pgrExposureCompensationAuto = 'Off'
#     camera.pgrExposureCompensation = 1.5


def init_camera():
    with Camera() as cam:
        cam.init()

        cam.AcquisitionMode = 'Continuous'

        cam.SharpnessEnabled = True
        cam.SharpnessAuto = 'Off'
        cam.Sharpness = sharp_entry.get()

        cam.ExposureAuto = 'Off'
        cam.ExposureTime = exposure_entry.get()

        cam.GainAuto = 'Off'
        gain = min(0, cam.get_info('Gain')['max'])
        cam.Gain = gain

        cam.AcquisitionFrameRateEnabled = True
        cam.AcquisitionFrameRateAuto = 'Off'
        cam.AcquisitionFrameRate = fps_entry.get()

        cam.pgrExposureCompensationAuto = 'Off'
        cam.pgrExposureCompensation = 1.5
        # Allow both long and short exposure times, without creating lag in live-viewing when  doing short.
        if cam.ExposureTime > 100000:
            cam.AcquisitionFrameRateEnabled = False  # if True, can uncomment the next two lines
        else:
            cam.AcquisitionFrameRateEnabled = True  # if True, can uncomment the next two lines
            cam.AcquisitionFrameRateAuto = 'Off'
            cam.AcquisitionFrameRate = fps_entry.get()

        cam.pgrExposureCompensationAuto = 'Off'
        cam.pgrExposureCompensation = 1.5
        global camera
        camera = cam


def update_clock():
    global timer
    timer_label_val.configure(text="$i " % timer)
    fabric_produced_label_val.configure(text="%f metre" % 1)
    root.after(1000, update_clock)


def create_new_directory_with_current_time(path):
    date_str = datetime.now().strftime("%d-%m-%Y %H-%M-%S")
    destination = path + folder_sep + date_str
    os.mkdir(destination)
    return destination


def start_detection():
    global detection
    detection = True
    start_recording()


def stop_detection():
    enable_entries()
    global detection
    detection = False
    start_detection_button['state'] = tk.NORMAL
    stop_detection_button['state'] = tk.DISABLED


def enable_entries():
    fps_entry['state'] = tk.NORMAL
    gain_entry['state'] = tk.NORMAL
    exposure_entry['state'] = tk.NORMAL
    sharp_entry['state'] = tk.NORMAL


def disable_entries():
    fps_entry['state'] = tk.DISABLED
    gain_entry['state'] = tk.DISABLED
    exposure_entry['state'] = tk.DISABLED
    sharp_entry['state'] = tk.DISABLED


def start_recording():
    timer_label_val.configure(text=time.strftime("%H:%M:%S"))

    global camera
    try:
        init_camera()
    except Exception as e:
        print(e)
        messagebox.showinfo(title="Kamera", message="Kamera Bağlantısı bulunamadı.")

    camera.start()  # start acquiring data
    disable_entries()

    global running, update_freq
    running = True
    if running:
        update_freq = 50
        update_im()


def stop_recording():
    enable_entries()
    start_record_button['state'] = tk.NORMAL
    stop_record_button['state'] = tk.DISABLED


def to_array(img):
    input_arr = tf.keras.preprocessing.image.img_to_array(img)
    input_arr = np.array([input_arr])  # Convert single image to a batch.
    return input_arr


def predict_defect_image(img):
    # 1s -> 10mm

    # resize image to half
    rimage = img.resize((960, 600))

    # 6 slice and predict
    for pos in sliced_pos:
        s_image = to_array(rimage.crop(pos))
        img_predict = model.predict(s_image)
        print(img_predict)
        save_image(s_image)  # save defect one

    # tahminiHataZaman(s) = hata buldugu saat - baslangic saat

    # tahminiHataKonum = tahminiHataZaman * 10mm

    # rapor icin veri kaydi

    # goruntuyu klasore kaydet

    # veri tabani kismi
    # kumasin kayit baslangic saaati (timestamp)
    # hata saati (timestamp)
    # hatali goruntunun yolu
    # onay (goruntu dogru bulmus mu)


def save_image(image):
    global index
    time_str = str(datetime.fromtimestamp(image.GetTimeStamp() / 1e6))
    filename = '%s-%d.jpg' % (time_str, index)
    full_path = current_dir + folder_sep + filename
    save_im = Image.fromarray(image)
    save_im.save(full_path + '.jpg')
    index = index + 1


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def update_im():
    if running:
        global image, camera, detection, current_dir

        # image = root.image
        image = camera.get_array()

        if detection:
            current_dir = create_new_directory_with_current_time(defect_folder)
            create_directory(defect_folder)
            predict_defect_image(image)
            start_detection_button['state'] = tk.DISABLED
            stop_detection_button['state'] = tk.NORMAL

        else:
            current_dir = create_new_directory_with_current_time(save_folder)
            start_record_button['state'] = tk.DISABLED
            stop_record_button['state'] = tk.NORMAL

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
fps_entry.insert(0, camera_fps)  # gain_entry.insert(0, cam.Gain)

gain_entry = tk.Entry(camera_spec_frame, width=10)
gain_entry.grid(row=1, column=1)
gain_entry.insert(0, camera_gain)  # gain_entry.insert(0, cam.Gain)

exposure_entry = tk.Entry(camera_spec_frame, width=10)
exposure_entry.grid(row=2, column=1)
exposure_entry.insert(0, camera_exp)  # gain_entry.insert(0, cam.Gain)

sharp_entry = tk.Entry(camera_spec_frame, width=10)
sharp_entry.grid(row=3, column=1)
sharp_entry.insert(0, camera_sharp)  # gain_entry.insert(0, cam.Gain)

start_record_button = tk.Button(camera_spec_frame, text="Kayıt Yap", command=start_recording)
start_record_button.grid(row=5, column=0, pady=10)  # change column to 2

stop_record_button = tk.Button(camera_spec_frame, text="Kaydı Durdur", command=stop_recording)
stop_record_button['state'] = tk.DISABLED
stop_record_button.grid(row=6, column=0, )  # change column to 2

# ------------------------------------------------------------- defect detection frame
detection_frame = ttk.LabelFrame(tab1, text='Hata Tespiti')
detection_frame.grid(row=1, column=0, padx=8, pady=4)

# elements
start_detection_button = tk.Button(detection_frame, text="Hata Tespitine Başla", width=18, command=start_detection)
start_detection_button.grid(row=0, column=0, pady=4)  # change column to 2

stop_detection_button = tk.Button(detection_frame, text="Hata Tespitini Durdur", width=18, command=stop_detection)
stop_detection_button['state'] = tk.DISABLED
stop_detection_button.grid(row=1, column=0, pady=4)
# ------------------------------------------------------------- image frame
image_frame = ttk.LabelFrame(tab1, text='Kamera Görüntüsü')
image_frame.grid(row=0, column=1, padx=8, pady=4)

# elements
timer_label = ttk.Label(image_frame, text='Kayıt Başlangıç Saat: ')
timer_label.grid(row=0, column=0)

timer_label_val = ttk.Label(image_frame)
timer_label_val.grid(row=0, column=1)

fabric_produced_label = ttk.Label(image_frame, text='Üretilen Kumaş(metre): ')
fabric_produced_label.grid(row=1, column=0)

fabric_produced_label_val = ttk.Label(image_frame, text='1')
fabric_produced_label_val.grid(row=1, column=1)

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
