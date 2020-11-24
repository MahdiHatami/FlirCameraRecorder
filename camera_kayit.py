import threading
from tkinter import *
from tkinter import messagebox

import numpy as np
import cv2
import datetime
import time


class MyJob(threading.Thread):
    e = None
    saat = 0
    dakika = 0
    saniye = 0
    sayacc = 0

    def __init__(self, coz1, coz2, fps, sure):
        super(MyJob, self).__init__()
        self._stop = threading.Event()
        self.coz1 = coz1
        self.coz2 = coz2
        self.fps = fps
        self.sure = sure

    def stop(self):
        self._stop.set()

    def run(self):
        sayac = 0
        coz1 = self.coz1
        coz2 = self.coz2
        fps = self.fps
        sure = self.sure
        while not self._stopisSet():
            cap = cv2.VideoCapture(0)
            ret = cap.set(3, coz1)
            ret = cap.set(4, coz2)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')

            t0 = time.time()
            now = datetime.datetime.now()
            video = 'Video'
            zaman = str(now.strftime("%Y-%m-%d-%H-%M-%S"))
            avi = '.avi'
            videoismi = video + '-' + zaman + '-' + str(sayac) + avi
            out = cv2.VideoWriter(videoismi, fourcc, fps, (coz1, coz2))
            while (cap.isOpened()):
                if self._stop.isSet():
                    return
                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 180)
                    out.write(frame)
                    t1 = time.time()
                    num_seconds = t1 - t0
                    if num_seconds >= sure:
                        break
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            time.sleep(1)
            sayac += 1


class videoGUI2:
    def __init__(self, master):
        self.master = master
        master.title("video Programi")

        self.calisiyor = True
        self.var = IntVar()

        self.sayac = 0
        self.girilen_sayi1 = 0
        self.girilen_sayi2 = 0

        self.saniye1 = Label(master, text="Video Suresi(saniye):")
        vcmd1 = master.register(self.donustur1)
        self.entry1 = Entry(master, validate="key",
                            validatecommand=(vcmd1, '%P'))

        self.fpsYazi = Label(master, text="FPS:")
        vcmd2 = master.register(self.donustur2)
        self.entry2 = Entry(master, validate="key",
                            validatecommand=(vcmd2, '%P'))

        self.cozunurluk1 = Radiobutton(master, text="640x480",
                                       variable=self.var, value=1)
        self.cozunurluk2 = Radiobutton(master, text="800x600",
                                       variable=self.var, value=2)

        self.defaultButton = Button(master, text="Kaydi Baslat",
                                    command=self.kaydiBaslat,
                                    background="green")

        self.sure = Label(master, text="")

        self.master.protocol("WM_DELETE_WINDOW", self.cikis)

        self.saniye1.grid(row=0, column=0, sticky=W)
        self.entry1.grid(row=0, column=1, columnspan=2, sticky=E)
        self.fpsYazi.grid(row=1, column=0, sticky=W)
        self.entry2.grid(row=1, column=1, columnspan=2, sticky=E)
        self.cozunurluk1.grid(row=3, column=0, sticky=W)
        self.cozunurluk2.grid(row=4, column=0, sticky=W)
        self.defaultButton.grid(row=3, column=1, sticky=E)
        self.sure.grid(row=5, column=0, sticky=W)

    def donustur1(self, new_text):
        if not new_text:  # the field is being cleared
            self.girilen_sayi1 = 0
            return True

        try:
            self.girilen_sayi1 = int(new_text)
            return True
        except ValueError:
            return False

    def donustur2(self, new_text):
        if not new_text:  # the field is being cleared
            self.girilen_sayi2 = 0
            return True

        try:
            self.girilen_sayi2 = float(new_text)
            return True
        except ValueError:
            return False

    def vidCek(self, val1, val2, fps, saniye):
        cap = cv2.VideoCapture(0)
        ret = cap.set(3, 640)
        ret = cap.set(4, 480)
        fourcc = cv2.cv.CV_FOURCC(*'XVID')
        t0 = time.time()
        now = datetime.datetime.now()
        video = 'video'
        zaman = str(now.strftime("%Y-%m-%d-%H-%M-%S"))
        avi = '.avi'
        videoismi = video + '-' + zaman + '-' + str(self.sayac) + avi
        out = cv2.VideoWriter(videoismi, fourcc, 30.0, (640, 480))
        while (cap.isOpened()):
            if self.calisiyor == False:
                return
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 180)
                out.write(frame)
                t1 = time.time()
                num_seconds = t1 - t0
                if num_seconds >= 5:
                    break
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        time.sleep(2)
        self.sayac += 1

    def kaydiBaslat(self):
        global e
        if self.var.get() == 0:
            messagebox.showinfo("Hata", "Cozunurluk secmediniz!!!")
        elif self.entry1.get() == '':
            messagebox.showinfo("Hata", "Video suresi yazmadiniz!!!")
        elif self.entry2.get() == '':
            messagebox.showinfo("Hata", "FPS yazmadiniz!!!")
        else:
            if self.var.get() == 1:
                videoSuresi = int(self.entry1.get())
                FPS = float(self.entry2.get())
                e = MyJob(640, 480, FPS, videoSuresi)
                e.start()
                self.defaultButton.configure(text="Kaydi Durdur",
                                             command=self.kaydiDurdur,
                                             background="red")
                self.yazdirBaslat()
            elif self.var.get() == 2:
                videoSuresi = int(self.entry1.get())
                FPS = float(self.entry2.get())
                e = MyJob(800, 600, FPS, videoSuresi)
                e.start()
                self.defaultButton.configure(text="Kaydi Durdur",
                                             command=self.kaydiDurdur,
                                             background="red")
                self.yazdirBaslat()

    def kaydiDurdur(self):
        global e
        e.stop()
        e = None
        self.yazdirDurdur()
        self.defaultButton.configure(text="Kaydi Baslat",
                                     command=self.kaydiBaslat,
                                     background="green")

    def yazdir(self):
        global saat
        global dakika
        global saniye
        global sayacc
        if self.cancel_id == False:
            self.sure['text'] = "Toplam kayit suresi: " + " " + str(
                saat) + ":" + str(dakika) + ":" + str(
                saniye) + "\n" + "Toplam video sayisi:" + " " + str(sayacc)
            if ((saat * 3600 + dakika * 60 + saniye) % (
                    int(self.entry1.get()) + 1) == 0):
                sayacc += 1
            saniye += 1
            if saniye == 60:
                saniye = 0
                dakika += 1
            if dakika == 60:
                dakika = 0
                saat += 1
            self.master.after(1000, self.yazdir)

    def yazdirBaslat(self):
        self.cancel_id = False
        self.yazdir()

    def yazdirDurdur(self):
        global saat
        global dakika
        global saniye
        global sayacc
        if self.cancel_id == False:
            self.cancel_id = True
            saat = 0
            dakika = 0
            saniye = 0
            sayacc = 0
            self.sure['text'] = ""

    def cikis(self):
        self.master.quit()
        self.master.destroy()


root = Tk()
my_gui = videoGUI2(root)
root.mainloop()
