import cv2
from simple_pyspin import Camera
from matplotlib import pyplot as plt
import numpy as np

camera_fps = 5
camera_gain = 15
camera_exp = 20000
camera_sharp = 2100
running = True


def calculate_cost(img):
    # convolute with proper kernels
    laplacian = cv2.Laplacian(img, cv2.CV_64F)
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)  # x
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)  # y

    return 0


def grap_image(gain=15, exp=20000, exp_comp=1.5, sharp=2100, bright=3000):
    print("gain: %i, exp: %i, exp_com: %i, sharp: %i, bright: %i", gain, exp, exp_comp, sharp, bright)
    with Camera() as cam:
        cam.init()

        cam.AcquisitionMode = 'SingleFrame'

        cam.AcquisitionFrameRateEnabled = True
        cam.AcquisitionFrameRateAuto = 'Off'
        cam.SharpnessEnabled = True
        cam.SharpnessAuto = 'Off'
        cam.ExposureAuto = 'Off'
        cam.GainAuto = 'Off'
        cam.pgrExposureCompensationAuto = 'Off'

        cam.Gain = gain
        cam.ExposureTime = exp
        cam.pgrExposureCompensation = exp_comp
        cam.Sharpness = sharp
        cam.AcquisitionFrameRate = 5
        cam.start()

        return cam.get_array()


def start_optimization():
    while running:
        image = grap_image()
        cost = calculate_cost(image)

        pass


if __name__ == "__main__":
    start_optimization()
