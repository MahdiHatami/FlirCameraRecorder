import tkinter as tk
import os
import tensorflow as tf
from datetime import datetime
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from simple_pyspin import Camera
from PIL import Image
from tkinter import ttk

fabric_speed = 10  # 10 mm/s
defect_folder = ""
save_folder = ""
folder_sep = ""

global camera_fps, camera_gain, camera_exp, camera_sharp
camera_fps = 5
camera_gain = 15
camera_exp = 10000
camera_sharp = 2100

global timer, detection, image, update_freq, running, index, current_dir
timer = 1
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
    defect_folder = "C:/Hata"
    save_folder = "C:/Kayit"
    folder_sep = "/"
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

    cam.start()  # now start acquiring data with the camera

    root = tk.Tk()  # Create instance
    root.title('GAP Kumaş Hata Denetleme Sistemi')  # Add a title

    # ------------------------------------------------------------- Tabs
    tabControl = ttk.Notebook(root)  # Create Tab Control

    tab1 = ttk.Frame(tabControl)  # Create a Tab
    tab2 = ttk.Frame(tabControl)  # Create second Tab

    tabControl.add(tab1, text='Kayıt / Hata Tespit')  # Add the Tab
    tabControl.add(tab2, text='Hata Raporları')  # Add second Tab

    tabControl.pack(expand=1, fill='both')  # Pack to make visible

    camera_spec_frame = ttk.LabelFrame(tab1, text='Kamera Özellikleri')
    camera_spec_frame.grid(row=0, column=0)

    detection_frame = ttk.LabelFrame(tab1, text='Hata Tespiti')
    detection_frame.grid(row=1, column=0, padx=8, pady=4)

    image_frame = ttk.LabelFrame(tab1, text='Kamera Görüntüsü')
    image_frame.grid(row=0, column=1, padx=8, pady=4)

    # set up the figure
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_yticks([])
    ax.set_xticks([])

    # global image
    image = cam.get_array()
    im = ax.imshow(image, vmin=0, vmax=255)  # by default, we start showing the first image the camera was looking at

    canvas = FigureCanvasTkAgg(fig, master=image_frame)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().grid(row=5, column=0, columnspan=6, rowspan=6)


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


    def start_detection():
        global detection, current_dir
        detection = True

        current_dir = create_new_directory_with_current_time(save_folder)

        start_detection_button['state'] = tk.DISABLED
        stop_detection_button['state'] = tk.NORMAL

        cam.stop()  # just in case
        cam.AcquisitionMode = 'Continuous'  # set acquisition mode to continuous
        cam.start()
        disable_entries()

        global running, update_freq
        running = True
        if running:
            update_freq = 50
            update_im()


    def stop_detection():
        global detection
        detection = False
        enable_entries()

        start_detection_button['state'] = tk.NORMAL
        stop_detection_button['state'] = tk.DISABLED


    def start_recording():
        timer_label_val.configure(text=time.strftime("%H:%M:%S"))

        global current_dir
        current_dir = create_new_directory_with_current_time(defect_folder)

        start_record_button['state'] = tk.DISABLED
        stop_record_button['state'] = tk.NORMAL

        cam.stop()  # just in case
        cam.AcquisitionMode = 'Continuous'  # set acquisition mode to continuous
        cam.start()
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


    def update_im():
        if running:
            global image, detection, current_dir

            # image = root.image
            image = cam.get_array()

            if detection:
                predict_defect_image(image)
            else:
                save_image(image)

            im = ax.imshow(image, vmin=0, vmax=255)
            im.set_data(image)
            canvas.draw()
            root.after(update_freq, update_im)  # this is units of milliseconds


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
            # img_predict = model.predict(s_image)
            # print(img_predict)
            # save_image(s_image)  # save defect one

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
        time_str = str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
        filename = '%s-%d.jpg' % (time_str, index)
        full_path = current_dir + "/" + filename
        save_im = Image.fromarray(image)
        save_im.save(full_path + '.jpg')
        index = index + 1


    def create_directory(path):
        if not os.path.exists(path):
            os.makedirs(path)


# ------------------------------------------------------------- camera spec frame
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
# elements
start_detection_button = tk.Button(detection_frame, text="Hata Tespitine Başla", width=18, command=start_detection)
start_detection_button.grid(row=0, column=0, pady=4)  # change column to 2

stop_detection_button = tk.Button(detection_frame, text="Hata Tespitini Durdur", width=18, command=stop_detection)
stop_detection_button['state'] = tk.DISABLED
stop_detection_button.grid(row=1, column=0, pady=4)
# ------------------------------------------------------------- image frame
# elements
timer_label = ttk.Label(image_frame, text='Kayıt Başlangıç Saat: ')
timer_label.grid(row=0, column=0)

timer_label_val = ttk.Label(image_frame)
timer_label_val.grid(row=0, column=1)

fabric_produced_label = ttk.Label(image_frame, text='Üretilen Kumaş(metre): ')
fabric_produced_label.grid(row=1, column=0)

fabric_produced_label_val = ttk.Label(image_frame, text='1')
fabric_produced_label_val.grid(row=1, column=1)

# update_im()
tk.mainloop()

cam.stop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.
