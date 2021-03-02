import io
import os
import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
import time
import datetime as dt
import argparse
from tkinter import ttk
from datetime import datetime
import numpy as np
import tensorflow as tf
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from Database import Database
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
# self.get_file_drive(file_id="1GEb5BGZMzcgp4VJljuoIvP5tE2xzcctc")
camera_fps = 5
camera_gain = 15
camera_exp = 20000
camera_sharp = 2100

saveLocally = False


def generate_file_name(self):
    time_str = str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
    filename = '%s-%d.jpg' % (time_str, self.index)
    # full_path = current_dir + "/" + filename
    full_path = filename
    return full_path


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


class App:
    def __init__(self, window, window_title, video_source=0):
        self.index = 1
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.drive_service = build('drive', 'v3', credentials=creds)

        time_str = str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
        file_metadata = {
            'name': time_str,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        parent_file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        parent_folder_id = parent_file.get('id')

        file_metadata = {
            'name': 'Hata1',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        self.hata1_folder = file.get('id')

        file_metadata = {
            'name': 'Hata2',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        self.hata2_folder = file.get('id')

        self.model = tf.keras.models.load_model('assets/network.h5')
        self.labels = ['hata1', 'hata2', 'saglam']
        self.width = 640
        self.height = 480
        self.record_start_time = datetime.now()

        self.fabric_speed = 8

        self.detection = False

        self.window = window
        self.window.title(window_title)
        self.video_source = video_source
        self.ok = False

        self.db = Database('gapopenc')

        # timer
        self.timer = ElapsedTimeClock(self.window)

        self.timerLabel = None

        # open video source (by default this will try to open the computer webcam)
        # self.vid = VideoCapture(self.video_source)

        self.vid = cv2.VideoCapture(video_source)

        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

        self.vid.set(cv2.CAP_PROP_FPS, camera_fps)
        # self.vid.set(cv2.CAP_PROP_GAIN, camera_gain)
        # self.vid.set(cv2.CAP_PROP_SHARPNESS, camera_sharp)
        # self.vid.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        # self.vid.set(cv2.CAP_PROP_EXPOSURE, camera_exp)

        # ------------------------------------------------------------- Tabs
        self.tabControl = ttk.Notebook(window)  # Create Tab Control
        self.tabControl.bind("<<NotebookTabChanged>>", self.handle_tab_changed)

        self.tab1 = ttk.Frame(self.tabControl)  # Create a Tab
        self.tab2 = ttk.Frame(self.tabControl)  # Create second Tab

        self.tabControl.add(self.tab1, text='Kayıt / Hata Tespit')  # Add the Tab
        self.tabControl.add(self.tab2, text='Hata Raporları')  # Add second Tab

        self.tabControl.pack(expand=1, fill='both')  # Pack to make visible

        self.camera_spec_frame = ttk.LabelFrame(self.tab1, text='Kamera Özellikleri')
        self.camera_spec_frame.grid(row=0, column=0)

        self.detection_frame = ttk.LabelFrame(self.tab1, text='Hata Tespiti')
        self.detection_frame.grid(row=1, column=0, padx=8, pady=4)

        self.image_frame = ttk.LabelFrame(self.tab1, text='Kamera Görüntüsü')
        self.image_frame.grid(row=0, column=1, padx=8, pady=4)

        # ------------------------------------------------------------- camera spec frame
        tk.Label(self.camera_spec_frame, text="Fps: ").grid(row=0)
        tk.Label(self.camera_spec_frame, text="Gain: ").grid(row=1)
        tk.Label(self.camera_spec_frame, text="Exposure: ").grid(row=2)
        tk.Label(self.camera_spec_frame, text="Sharpness: ").grid(row=3)

        self.fps_entry = tk.Entry(self.camera_spec_frame, width=10)
        self.fps_entry.grid(row=0, column=1)
        self.fps_entry.insert(0, camera_fps)  # gain_entry.insert(0, cam.Gain)

        self.gain_entry = tk.Entry(self.camera_spec_frame, width=10)
        self.gain_entry.grid(row=1, column=1)
        self.gain_entry.insert(0, camera_gain)  # gain_entry.insert(0, cam.Gain)

        self.exposure_entry = tk.Entry(self.camera_spec_frame, width=10)
        self.exposure_entry.grid(row=2, column=1)
        self.exposure_entry.insert(0, camera_exp)  # gain_entry.insert(0, cam.Gain)

        self.sharp_entry = tk.Entry(self.camera_spec_frame, width=10)
        self.sharp_entry.grid(row=3, column=1)
        self.sharp_entry.insert(0, camera_sharp)  # gain_entry.insert(0, cam.Gain)

        self.start_record_button = tk.Button(self.camera_spec_frame, text="Kayıt Yap", command=self.start_recording)
        self.start_record_button.grid(row=5, column=0, pady=10)  # change column to 2

        self.stop_record_button = tk.Button(self.camera_spec_frame, text="Kaydı Durdur", command=self.stop_recording)
        self.stop_record_button['state'] = tk.DISABLED
        self.stop_record_button.grid(row=6, column=0, )  # change column to 2

        # ------------------------------------------------------------- defect detection frame
        # elements
        self.start_detection_button = tk.Button(self.detection_frame, text="Hata Tespitine Başla", width=18,
                                                command=self.start_detection)
        self.start_detection_button.grid(row=0, column=0, pady=4)  # change column to 2

        self.stop_detection_button = tk.Button(self.detection_frame, text="Hata Tespitini Durdur", width=18,
                                               command=self.stop_detection)
        self.stop_detection_button['state'] = tk.DISABLED
        self.stop_detection_button.grid(row=1, column=0, pady=4)
        # ------------------------------------------------------------- image frame
        # elements
        self.imer_label = ttk.Label(self.image_frame, text='Kayıt Başlangıç Saat: 09:00')
        self.imer_label.grid(row=0, column=0)

        self.imer_label_val = ttk.Label(self.image_frame)
        self.imer_label_val.grid(row=0, column=1)

        self.abric_produced_label = ttk.Label(self.image_frame, text='Üretilen Kumaş(metre): 30')
        self.abric_produced_label.grid(row=1, column=0)

        self.abric_produced_label_val = ttk.Label(self.image_frame, text='')
        self.abric_produced_label_val.grid(row=1, column=1)

        # Create a canvas that can fit the above video source size
        self.canvas = tk.Canvas(window, width=self.width, height=self.height)
        self.canvas.pack()

        # -------------------------------------------------------------------------------- Tab 2
        self.frame_query_view = ttk.LabelFrame(self.tab2, text='Raporlar')
        self.frame_query_view.grid(row=0, column=0, padx=8, pady=4)
        self.frame_query_view.pack(fill='both')

        columns = ['id', 'Kayıt Saati', 'Hata Saati', 'Hata Türü', 'Dosya Yolu', 'Hata Konumu']
        self.tree_view = ttk.Treeview(self.frame_query_view, columns=columns, show="headings")
        self.tree_view.column("id", width=30)
        for col in columns[1:]:
            self.tree_view.column(col, width=150)
            self.tree_view.heading(col, text=col)
        self.tree_view.bind("<Double-1>", self.show_selected_row())
        self.tree_view.pack(fill="both")

        self.scrollbar = tk.Scrollbar(self.frame_query_view, orient='vertical')
        self.scrollbar.configure(command=self.tree_view.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.tree_view.config(yscrollcommand=self.scrollbar.set)

        # After it is called once, the update method will be automatically called every delay milliseconds
        # 5fps 166
        self.delay = 200
        self.update()

        self.window.mainloop()

    # ----------------------------------------------------------------------------------------------------------------->
    def upload_image(self, image, defect_type):
        image_name = "defect-" + defect_type + "-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg"
        cv2.imwrite(image_name, image)
        if defect_type == 'hata1':
            file_metadata = {'name': image_name, 'parents': [self.hata1_folder]}
        else:
            file_metadata = {'name': image_name, 'parents': [self.hata2_folder]}

        media = MediaFileUpload(image_name, mimetype='image/jpeg')
        file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.remove(image_name)
        print('File ID: %s' % file.get('id'))

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                return ret, None
        else:
            return None, None

    def start_recording(self):
        self.ok = True
        self.timer.start()

        self.detection = False

        self.disable_entries()
        self.start_record_button['state'] = tk.DISABLED
        self.stop_record_button['state'] = tk.NORMAL
        self.start_detection_button['state'] = tk.DISABLED
        print("camera opened => Recording")

    def stop_recording(self):
        self.ok = False
        self.timer.stop()

        self.enable_entries()
        self.start_record_button['state'] = tk.NORMAL
        self.stop_record_button['state'] = tk.DISABLED
        self.start_detection_button['state'] = tk.NORMAL
        print("camera closed => Not Recording")

    def start_detection(self):
        print("camera opened => Detecting")
        self.timer.start()
        self.ok = True
        self.detection = True
        self.update()
        self.record_start_time = datetime.now()

        self.disable_entries()
        self.start_detection_button['state'] = tk.DISABLED
        self.stop_detection_button['state'] = tk.NORMAL
        self.start_record_button['state'] = tk.DISABLED

    # self.vid.out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def stop_detection(self):
        self.ok = False
        self.timer.stop()
        self.detection = False
        self.enable_entries()

        self.start_detection_button['state'] = tk.NORMAL
        self.stop_detection_button['state'] = tk.DISABLED
        self.start_record_button['state'] = tk.NORMAL

    def update(self):
        print("update " + self.index.__str__())
        # Get a frame from the video source
        ret, frame = self.get_frame()
        if self.ok:
            if ret:
                self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
                if self.detection:
                    self.predict_defect_image(frame)
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.window.after(self.delay, self.update)

        self.index = self.index + 1

    def handle_tab_changed(self, event):
        selection = event.widget.select()
        tab = event.widget.tab(selection, "text")
        if tab == "Hata Raporları":
            self.populate_list()

    def populate_list(self):
        for i in self.tree_view.get_children():
            self.tree_view.delete(i)
        for row in self.db.fetch_all():
            self.tree_view.insert('', 'end', values=row)

    def show_selected_row(self):
        if self.tree_view.selection().__len__() > 0:
            item_pos = self.tree_view.selection()[0]
            item = self.tree_view.item(item_pos)
            # id = item['values'][0]
            # rec_time = item['values'][1]
            # def_time = item['values'][2]
            # type = item['values'][3]
            # img_path = item['values'][4]

    def enable_entries(self):
        self.fps_entry['state'] = tk.NORMAL
        self.gain_entry['state'] = tk.NORMAL
        self.exposure_entry['state'] = tk.NORMAL
        self.sharp_entry['state'] = tk.NORMAL

    def disable_entries(self):
        self.fps_entry['state'] = tk.DISABLED
        self.gain_entry['state'] = tk.DISABLED
        self.exposure_entry['state'] = tk.DISABLED
        self.sharp_entry['state'] = tk.DISABLED

        self.start_detection_button['state'] = tk.NORMAL
        self.stop_detection_button['state'] = tk.DISABLED
        self.start_record_button['state'] = tk.NORMAL

    def predict(self, img):
        img = img.reshape(-1, 320, 300, 1)
        pred = self.model.predict(img)
        top_prediction_index = np.argmax(pred)
        predicted_label = self.extract_label(top_prediction_index)
        # predictions = pred.tolist()[0]
        # extracted_predictions = [{extract_label(i): "%.2f%%" % (x * 100)} for i, x in enumerate(predictions)]
        # top_percent = "%.2f%%" % (predictions[top_prediction_index] * 100)
        # print(top_percent)

        return predicted_label

    def predict_defect_image(self, img):
        print("predict " + self.index.__str__())
        # 1s -> 10mm

        if self.index > 5:
            # resize image to half
            im1 = img
            rimage = cv2.resize(im1, dsize=(960, 600), interpolation=cv2.INTER_CUBIC)

            # 6 slice and predict
            r1 = rimage[0:300, 0:320]
            pred_label = self.predict(r1)
            if pred_label != self.labels[2]:
                self.save_image(pred_label, r1)
                return

            r2 = rimage[0:300, 320:640]
            pred_label = self.predict(r2)
            if pred_label != self.labels[2]:
                self.save_image(pred_label, r2)
                return

            r3 = rimage[0:300, 640:960]
            pred_label = self.predict(r3)
            if pred_label != self.labels[2]:
                self.save_image(pred_label, r3)
                return

            r4 = rimage[300:600, 0:320]
            pred_label = self.predict(r4)
            if pred_label != self.labels[2]:
                self.save_image(pred_label, r4)
                return

            r5 = rimage[300:600, 320:640]
            pred_label = self.predict(r5)
            if pred_label != self.labels[2]:
                self.save_image(pred_label, r5)
                return

            r6 = rimage[300:600, 640:960]
            pred_label = self.predict(r6)
            if pred_label != self.labels[2]:
                self.save_image(pred_label, r6)
                return

    def save_image(self, defect_type, img):
        print(defect_type)
        file_id = 0
        full_path = generate_file_name(self)
        save_im = PIL.Image.fromarray(img)

        if saveLocally:
            save_im.save(full_path + '.jpg')
        else:
            self.upload_image(image=img, defect_type=defect_type)

        if self.detection:
            self.save_to_db(defect_type_str=defect_type, full_path=full_path, file_id=file_id)

    def get_file_drive(self, file_id):
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

    def save_to_db(self, defect_type_str, full_path, file_id):
        defect_time = datetime.now()
        # get how many seconds passed from start
        passed_seconds = (defect_time - self.record_start_time).total_seconds()
        predict_location = (passed_seconds * self.fabric_speed) / 1000
        predict_location = "{:.2f}".format(predict_location)
        self.db.insert(record_create_date=self.record_start_time,
                       created_date=defect_time,
                       defect_type=defect_type_str,
                       image_path=full_path,
                       defect_location=predict_location,
                       file_id=file_id,
                       is_valid=1)

    def extract_label(self, label_index):
        return self.labels[label_index]


class VideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)

        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Command Line Parser
        args = CommandLineParser().args

        # create videowriter

        # 1. Video Type
        VIDEO_TYPE = {
            'avi': cv2.VideoWriter_fourcc(*'XVID'),
            # 'mp4': cv2.VideoWriter_fourcc(*'H264'),
            'mp4': cv2.VideoWriter_fourcc(*'XVID'),
        }

        self.fourcc = VIDEO_TYPE[args.type[0]]

        # 2. Video Dimension
        STD_DIMENSIONS = {
            '480p': (640, 480),
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '4k': (3840, 2160),
        }
        res = STD_DIMENSIONS[args.res[0]]
        print(args.name, self.fourcc, res)
        # self.out = cv2.VideoWriter(args.name[0] + '.' + args.type[0], self.fourcc, 10, res)

        # set video sourec width and height
        self.vid.set(3, res[0])
        self.vid.set(4, res[1])

        # Get video source width and height
        self.width, self.height = res

    # To get frames
    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return ret, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                return ret, None
        else:
            return None, None

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
            # self.out.release()
            cv2.destroyAllWindows()


class ElapsedTimeClock:
    def __init__(self, window):
        self.T = tk.Label(window, text='00:00:00', font=('times', 20, 'bold'), bg='green')
        self.T.pack(fill=tk.BOTH, expand=1)
        self.elapsedTime = dt.datetime(1, 1, 1)
        self.running = 0
        self.lastTime = ''
        t = time.localtime()
        self.zeroTime = dt.timedelta(hours=t[3], minutes=t[4], seconds=t[5])
        # self.tick()

    def tick(self):
        # get the current local time from the PC
        self.now = dt.datetime(1, 1, 1).now()
        self.elapsedTime = self.now - self.zeroTime
        self.time2 = self.elapsedTime.strftime('%H:%M:%S')
        # if time string has changed, update it
        if self.time2 != self.lastTime:
            self.lastTime = self.time2
            self.T.config(text=self.time2)
        # calls itself every 200 milliseconds
        # to update the time display as needed
        # could use >200 ms, but display gets jerky
        self.updwin = self.T.after(100, self.tick)

    def start(self):
        if not self.running:
            self.zeroTime = dt.datetime(1, 1, 1).now() - self.elapsedTime
            self.tick()
            self.running = 1

    def stop(self):
        if self.running:
            self.T.after_cancel(self.updwin)
            self.elapsedTime = dt.datetime(1, 1, 1).now() - self.zeroTime
            self.time2 = self.elapsedTime
            self.running = 0


class CommandLineParser:

    def __init__(self):
        # Create object of the Argument Parser
        parser = argparse.ArgumentParser(description='Script to record videos')

        # Create a group for requirement
        # for now no required arguments
        # required_arguments=parser.add_argument_group('Required command line arguments')

        # Only values is supporting for the tag --type. So nargs will be '1' to get
        parser.add_argument('--type', nargs=1, default=['avi'], type=str,
                            help='Type of the video output: for now we have only AVI & MP4')

        # Only one values are going to accept for the tag --res. So nargs will be '1'
        parser.add_argument('--res', nargs=1, default=['480p'], type=str,
                            help='Resolution of the video output: for now we have 480p, 720p, 1080p & 4k')

        # Only one values are going to accept for the tag --name. So nargs will be '1'
        parser.add_argument('--name', nargs=1, default=['output'], type=str, help='Enter Output video title/name')

        # Parse the arguments and get all the values in the form of namespace.
        # Here args is of namespace and values will be accessed through tag names
        self.args = parser.parse_args()


def main():
    # Create a window and pass it to the Application object
    App(tk.Tk(), 'GAP Kumaş Hata Denetleme Sistemi')


main()
