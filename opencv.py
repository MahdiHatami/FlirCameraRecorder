import tkinter as tk
from tkinter import *
import os
import tensorflow as tf
from datetime import datetime
import time
import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk
from tkinter import ttk
from Database import Database

db_name = "gap"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
fabric_speed = 8  # 10 mm/s
defect_folder = ""
save_folder = ""
folder_sep = ""

db = Database(db_name)

global camera_fps, camera_gain, camera_exp, camera_sharp
camera_fps = 5
camera_gain = 15
camera_exp = 20000
camera_sharp = 2100

global panelA

global record_start_time, detection, image, update_freq, running, index, current_dir
detection = False
image = np.zeros((600, 960))
update_freq = 50  # milliseconds
running = True
index = 1

model = tf.keras.models.load_model('assets/network.h5')
labels = ['hata1', 'hata2', 'saglam']


def populate_list():
    for i in tree_view.get_children():
        tree_view.delete(i)
    for row in db.fetch_all():
        tree_view.insert('', 'end', values=row)


def handle_tab_changed(event):
    selection = event.widget.select()
    tab = event.widget.tab(selection, "text")
    if tab == "Hata Raporları":
        populate_list()


def update_clock():
    global record_start_time
    timer_label_val.configure(text="$i " % record_start_time)
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
    global detection, current_dir, running, update_freq, record_start_time
    detection = True
    record_start_time = datetime.now()

    current_dir = create_new_directory_with_current_time(defect_folder)

    start_detection_button['state'] = tk.DISABLED
    stop_detection_button['state'] = tk.NORMAL

    start_record_button['state'] = tk.DISABLED

    disable_entries()

    # cam.stop()  # just in case
    # cam.AcquisitionMode = 'Continuous'  # set acquisition mode to continuous
    # cam.start()
    #
    # val = cam.ExposureTime
    # cam.ExposureTime = val  # we force set an exposure time. If not, the update may be buggy
    # cam.ExposureTime = 10000 # we force set an exposure time. If not, the update may be buggy

    running = True
    update_freq = 50
    update_im()


def stop_detection():
    global detection, running
    detection = False
    running = False
    enable_entries()

    start_detection_button['state'] = tk.NORMAL
    stop_detection_button['state'] = tk.DISABLED
    start_record_button['state'] = tk.NORMAL


def takeSnapshot(self):
    # grab the current timestamp and use it to construct the
    # output path
    ts = datetime.datetime.now()
    filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
    p = os.path.sep.join((self.outputPath, filename))
    # save the file
    cv2.imwrite(p, self.frame.copy())
    print("[INFO] saved {}".format(filename))


def start_recording():
    global panelA
    global current_dir, running, update_freq, detection, record_start_time
    record_start_time = datetime.now()

    detection = False

    timer_label_val.configure(text=time.strftime("%H:%M:%S"))

    current_dir = create_new_directory_with_current_time(save_folder)

    start_record_button['state'] = tk.DISABLED
    stop_record_button['state'] = tk.NORMAL
    start_detection_button['state'] = tk.DISABLED

    disable_entries()

    running = True
    update_freq = 50

    cap = cv2.VideoCapture(0)

    while (running):
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Our operations on the frame come here
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        global image
        image = gray
        update_im()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

    # cap = cv2.VideoCapture(running)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 864)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.7)
    # cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    # cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)
    #
    # row_bytes = float(len(image.getData())) / float(image.getRows())
    # cv_image = np.array(image.getData(), dtype="uint8").reshape((image.getRows(), image.getCols()))
    # cv2.imshow('frame', cv_image)

    # update_im()


def stop_recording():
    enable_entries()
    global running
    running = False
    start_record_button['state'] = tk.NORMAL
    stop_record_button['state'] = tk.DISABLED
    start_detection_button['state'] = tk.NORMAL


def update_im():
    if running:
        global image, detection, current_dir, panelA

        if detection:
            predict_defect_image(image)
        else:
            # save_image("", image)

            image = Image.fromarray(image)  # convert the images to PIL format
            image = ImageTk.PhotoImage(image)  # and then to ImageTk format

            if panelA is None:
                panelA = Label(master=image_frame, image=image)
                panelA.image = image
            else:
                panelA.configure(image=image)
                panelA.image = image


def to_array(img):
    input_arr = tf.keras.preprocessing.image.img_to_array(img)
    input_arr = np.array([input_arr])  # Convert single image to a batch.
    return input_arr


def extract_label(label_index):
    return labels[label_index]


def save_to_db(type, image_path):
    global record_start_time
    defect_time = datetime.now()
    passed_seconds = (defect_time - record_start_time).total_seconds()  # get how many seconds passed from start
    predict_location = (passed_seconds * fabric_speed) / 1000
    predict_location = "{:.2f}".format(predict_location)
    db.insert(record_create_date=record_start_time,
              created_date=defect_time,
              defect_type=type,
              image_path=image_path,
              defect_location=predict_location,
              is_valid=1)


def predict(img):
    img = img.reshape(-1, 320, 300, 1)
    pred = model.predict(img)
    top_prediction_index = np.argmax(pred)
    predicted_label = extract_label(top_prediction_index)
    # predictions = pred.tolist()[0]
    # extracted_predictions = [{extract_label(i): "%.2f%%" % (x * 100)} for i, x in enumerate(predictions)]
    # top_percent = "%.2f%%" % (predictions[top_prediction_index] * 100)
    # print(top_percent)

    return predicted_label


def predict_defect_image(img):
    # 1s -> 10mm

    # resize image to half
    im1 = img
    rimage = np.resize(im1, (600, 960))

    # 6 slice and predict
    r1 = rimage[0:300, 0:320]
    pred_label = predict(r1)
    if pred_label != labels[2]:
        save_image(pred_label, r1)

    r2 = rimage[0:300, 320:640]
    pred_label = predict(r2)
    if pred_label != labels[2]:
        save_image(pred_label, r2)

    r3 = image[0:300, 640:960]
    pred_label = predict(r3)
    if pred_label != labels[2]:
        save_image(pred_label, r3)

    r4 = image[300:600, 0:320]
    pred_label = predict(r4)
    if pred_label != labels[2]:
        save_image(pred_label, r4)

    r5 = image[300:600, 320:640]
    pred_label = predict(r5)
    if pred_label != labels[2]:
        save_image(pred_label, r5)

    r6 = image[300:600, 640:960]
    pred_label = predict(r6)
    if pred_label != labels[2]:
        save_image(pred_label, r6)


def save_image(defect_type, img):
    full_path = generate_file_name()
    save_im = Image.fromarray(img)
    save_im.save(full_path + '.jpg')
    if detection:
        save_to_db(defect_type, full_path)


def generate_file_name():
    global index
    time_str = str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
    filename = '%s-%d.jpg' % (time_str, index)
    full_path = current_dir + "/" + filename
    index = index + 1
    return full_path


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


root = tk.Tk()  # Create instance
root.title('GAP Kumaş Hata Denetleme Sistemi')  # Add a title

# ------------------------------------------------------------- Tabs
tabControl = ttk.Notebook(root)  # Create Tab Control
tabControl.bind("<<NotebookTabChanged>>", handle_tab_changed)

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
timer_label = ttk.Label(image_frame, text='Kayıt Başlangıç Saat: 09:00')
timer_label.grid(row=0, column=0)

timer_label_val = ttk.Label(image_frame)
timer_label_val.grid(row=0, column=1)

fabric_produced_label = ttk.Label(image_frame, text='Üretilen Kumaş(metre): 30')
fabric_produced_label.grid(row=1, column=0)

fabric_produced_label_val = ttk.Label(image_frame, text='')
fabric_produced_label_val.grid(row=1, column=1)

panelA = Label(master=image_frame)


# -------------------------------------------------------------------------------- Tab 2


def show_selected_row(event):
    item_pos = tree_view.selection()[0]
    item = tree_view.item(item_pos)
    id = item['values'][0]
    rec_time = item['values'][1]
    def_time = item['values'][2]
    type = item['values'][3]
    img_path = item['values'][4]


frame_query_view = ttk.LabelFrame(tab2, text='Raporlar')
frame_query_view.grid(row=0, column=0, padx=8, pady=4)
frame_query_view.pack(fill='both')

columns = ['id', 'Kayıt Saati', 'Hata Saati', 'Hata Türü', 'Dosya Yolu', 'Hata Konumu']
tree_view = ttk.Treeview(frame_query_view, columns=columns, show="headings")
tree_view.column("id", width=30)
for col in columns[1:]:
    tree_view.column(col, width=150)
    tree_view.heading(col, text=col)
tree_view.bind("<Double-1>", show_selected_row)
tree_view.pack(fill="both")

scrollbar = Scrollbar(frame_query_view, orient='vertical')
scrollbar.configure(command=tree_view.yview)
scrollbar.pack(side="right", fill="y")

tree_view.config(yscrollcommand=scrollbar.set)

populate_list()

panelA = None

tk.mainloop()
