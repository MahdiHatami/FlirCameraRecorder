import tkinter as tk
from PIL import Image
from PIL import ImageTk
import threading
import queue
import cv2

global camera_fps, camera_gain, camera_exp, camera_sharp
camera_fps = 5
camera_gain = 15
camera_exp = 20000
camera_sharp = 2100
# I have taken a more modular approach so that UI is easy to change, update and extend.
# I have also developed UI in a way so that UI has no knowledge of how data is fetched or processed, it is just a UI.

# Left Screen Views
class LeftView(tk.Frame):
    def __init__(self, root):
        # call super class (Frame) constructor
        tk.Frame.__init__(self, root)
        # save root layour for later references
        self.root = root
        # load all UI
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self, text="Fps: ").grid(row=0)
        tk.Label(self, text="Gain: ").grid(row=1)
        tk.Label(self, text="Exposure: ").grid(row=2)
        tk.Label(self, text="Sharpness: ").grid(row=3)

        fps_entry = tk.Entry(self, width=10)
        fps_entry.grid(row=0, column=1)
        fps_entry.insert(0, camera_fps)  # gain_entry.insert(0, cam.Gain)

        gain_entry = tk.Entry(self.camera_spec_frame, width=10)
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

    def update_image(self, image):
        # configure image_label with new image
        self.image_label.configure(image=image)
        # this is to avoid garbage collection, so we hold an explicit reference
        self.image = image


# Right Screen Views
class RightView(tk.Frame):
    def __init__(self, root):
        # call super class (Frame) constructor
        tk.Frame.__init__(self, root)
        # save root layour for later references
        self.root = root
        # load all UI
        self.setup_ui()

    def setup_ui(self):
        # create a webcam output label
        self.output_label = tk.Label(self, text="Face detection Output", bg="black", fg="white")
        self.output_label.pack(side="top", fill="both", expand="yes", padx=10)

        # create label to hold image
        self.image_label = tk.Label(self)
        # put the image label inside left screen
        self.image_label.pack(side="left", fill="both", expand="yes", padx=10, pady=10)

    def update_image(self, image):
        # configure image_label with new image
        self.image_label.configure(image=image)
        # this is to avoid garbage collection, so we hold an explicit reference
        self.image = image


# All App GUI Combined
class AppGui:
    def __init__(self):
        self.camera_fps = 5
        self.camera_gain = 15
        self.camera_exp = 20000
        self.camera_sharp = 2100
        # initialize the gui toolkit
        self.root = tk.Tk()
        # set the geometry of the window
        # self.root.geometry("550x300+300+150")

        # set title of window
        self.root.title('GAP Kumaş Hata Denetleme Sistemi')  # Add a title

        # ------------------------------------------------------------- Tabs
        self.tabControl = tk.Notebook(self.root)  # Create Tab Control
        self.tabControl.bind("<<NotebookTabChanged>>", self.handle_tab_changed)

        self.tab1 = tk.Frame(self.tabControl)  # Create a Tab
        self.tab2 = tk.Frame(self.tabControl)  # Create second Tab

        self.tabControl.add(self.tab1, text='Kayıt / Hata Tespit')  # Add the Tab
        self.tabControl.add(self.tab2, text='Hata Raporları')  # Add second Tab

        self.tabControl.pack(expand=1, fill='both')  # Pack to make visible

        self.camera_spec_frame = tk.LabelFrame(self.tab1, text='Kamera Özellikleri')
        self.camera_spec_frame.grid(row=0, column=0)

        self.detection_frame = tk.LabelFrame(self.tab1, text='Hata Tespiti')
        self.detection_frame.grid(row=1, column=0, padx=8, pady=4)

        self.image_frame = tk.LabelFrame(self.tab1, text='Kamera Görüntüsü')
        self.image_frame.grid(row=0, column=1, padx=8, pady=4)

        # create left screen view
        self.left_view = LeftView(self.camera_spec_frame)
        self.left_view.pack(side='left')

        # create right screen view
        self.right_view = RightView(self.detection_frame)
        self.right_view.pack(side='right')

        # define image width/height that we will use
        # while showing an image in webcam/neural network
        # output window
        self.image_width = 500
        self.image_height = 500

        # define the center of the cirlce based on image dimentions
        # this is the cirlce we will use for user focus
        self.circle_center = (int(self.image_width / 2), int(self.image_height / 4))
        # define circle radius
        self.circle_radius = 15
        # define circle color == red
        self.circle_color = (255, 0, 0)

        self.is_ready = True

    def launch(self):
        # start the gui loop to listen for events
        self.root.mainloop()

    def process_image(self, image):
        # resize image to desired width and height
        # image = image.resize((self.image_width, self.image_height),Image.ANTIALIAS)
        image = cv2.resize(image, (self.image_width, self.image_height))

        # if image is RGB (3 channels, which means webcam image) then draw a circle on it
        # for user to focus on that circle to align face
        # if(len(image.shape) == 3):
        #    cv2.circle(image, self.circle_center, self.circle_radius, self.circle_color, 2)

        # convert image to PIL library format which is required for Tk toolkit
        image = Image.fromarray(image)

        # convert image to Tk toolkit format
        image = ImageTk.PhotoImage(image)

        return image

    def update_webcam_output(self, image):
        # pre-process image to desired format, height etc.
        image = self.process_image(image)

        # pass the image to left_view to update itself
        self.left_view.update_image(image)

    def update_neural_network_output(self, image):
        # pre-process image to desired format, height etc.
        image = self.process_image(image)
        # pass the image to right_view to update itself
        self.right_view.update_image(image)

    def update_chat_view(self, question, answer_type):
        self.left_view.update_chat_view(question, answer_type)

    def update_emotion_state(self, emotion_state):
        self.right_view.update_emotion_state(emotion_state)


# Class to Access Webcam
class VideoCamera:
    def __init__(self):
        # passing 0 to VideoCapture means fetch video from webcam
        self.video_capture = cv2.VideoCapture(0)

    # release resources like webcam
    def __del__(self):
        self.video_capture.release()

    def read_image(self):
        # get a single frame of video
        ret, frame = self.video_capture.read()
        # return the frame to user
        return ret, frame

    # method to release webcam manually
    def release(self):
        self.video_capture.release()


# function to detect face using OpenCV
def detect_defects(img):
    pass


# Thread Class for Webcam Feed
class WebcamThread(threading.Thread):
    def __init__(self, app_gui, callback_queue):
        # call super class (Thread) constructor
        threading.Thread.__init__(self)
        # save reference to callback_queue
        self.callback_queue = callback_queue

        # save left_view reference so that we can update it
        self.app_gui = app_gui

        # set a flag to see if this thread should stop
        self.should_stop = False

        # set a flag to return current running/stop status of thread
        self.is_stopped = False

        # create a Video camera instance
        self.camera = VideoCamera()

    # define thread's run method
    def run(self):
        # start the webcam video feed
        while True:
            # check if this thread should stop
            # if yes then break this loop
            if self.should_stop:
                self.is_stopped = True
                break

            # read a video frame
            ret, self.current_frame = self.camera.read_image()

            if ret == False:
                print('Video capture failed')
                exit(-1)

            # opencv reads image in BGR color space, let's convert it
            # to RGB space
            self.current_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            # key = cv2.waitKey(10)

            if self.callback_queue.full() == False:
                # put the update UI callback to queue so that main thread can execute it
                self.callback_queue.put((lambda: self.update_on_main_thread(self.current_frame, self.app_gui)))

        # fetching complete, let's release camera
        # self.camera.release()

    # this method will be used as callback and executed by main thread
    def update_on_main_thread(self, current_frame, app_gui):
        app_gui.update_webcam_output(current_frame)
        face = detect_defects(current_frame)
        app_gui.update_neural_network_output(face)

    def __del__(self):
        self.camera.release()

    def release_resources(self):
        self.camera.release()

    def stop(self):
        self.should_stop = True


# A GUI Wrappr (Interface) to Connect it with Data
class Wrapper:
    def __init__(self):
        self.app_gui = AppGui()

        # create a Video camera instance
        # self.camera = VideoCamera()

        # intialize variable to hold current webcam video frame
        self.current_frame = None

        # create a queue to fetch and execute callbacks passed
        # from background thread
        self.callback_queue = queue.Queue()

        # create a thread to fetch webcam feed video
        self.webcam_thread = WebcamThread(self.app_gui, self.callback_queue)

        # save attempts made to fetch webcam video in case of failure
        self.webcam_attempts = 0

        # register callback for being called when GUI window is closed
        self.app_gui.root.protocol("WM_DELETE_WINDOW", self.on_gui_closing)

        # start webcam
        self.start_video()

        # start fetching video
        self.fetch_webcam_video()

    def on_gui_closing(self):
        self.webcam_attempts = 51
        self.webcam_thread.stop()
        self.webcam_thread.join()
        self.webcam_thread.release_resources()

        self.app_gui.root.destroy()

    def start_video(self):
        self.webcam_thread.start()

    def fetch_webcam_video(self):
        try:
            # while True:
            # try to get a callback put by webcam_thread
            # if there is no callback and call_queue is empty
            # then this function will throw a Queue.Empty exception
            callback = self.callback_queue.get_nowait()
            callback()
            self.webcam_attempts = 0
            # self.app_gui.root.update_idletasks()
            self.app_gui.root.after(70, self.fetch_webcam_video)

        except queue.Empty:
            if self.webcam_attempts <= 50:
                self.webcam_attempts = self.webcam_attempts + 1
                self.app_gui.root.after(100, self.fetch_webcam_video)

    def launch(self):
        self.app_gui.launch()

    def __del__(self):
        self.webcam_thread.stop()


wrapper = Wrapper()
wrapper.launch()
