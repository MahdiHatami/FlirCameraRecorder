import math
import os
from datetime import datetime
from PIL import Image
from geneticalgorithm import geneticalgorithm as ga
import cv2
from simple_pyspin import Camera
import numpy as np

running = True
global gsharp
gsharp = -111111

save_folder = "C:/Optimization"
if not os.path.exists(save_folder):
    os.makedirs(save_folder)


def calculate_cost_lap(img):
    lap = cv2.Laplacian(img, cv2.CV_64F).var()
    return lap


def calculate_cost_sobel(img):
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)  # x
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)  # y
    sobelx = np.uint8(np.absolute(sobelx))
    sobely = np.uint8(np.absolute(sobely))
    sobelCombined = cv2.bitwise_or(sobelx, sobely)

    sobel_kenar_yaniti = math.sqrt(np.power(np.sum(sobelCombined), 2))

    return sobel_kenar_yaniti


# def grap_image(gain=15, exp=20000, exp_comp=1.5, sharp=2100, bright=3000):
def grap_image(p):
    # print("Parameters: Gain-{0}, Exposur-{1}, Exp_comp-{2}, Sharp-{3}, Bright-{4}"
    #   .format(gain, exp, exp_comp, sharp, bright))
    with Camera() as cam:
        cam.init()

        cam.AcquisitionMode = 'SingleFrame'

        cam.AcquisitionFrameRateEnabled = True
        cam.AcquisitionFrameRateAuto = 'Off'
        cam.AcquisitionFrameRate = 5
        cam.SharpnessEnabled = True
        cam.SharpnessAuto = 'Off'
        cam.ExposureAuto = 'Off'
        cam.GainAuto = 'Off'
        cam.pgrExposureCompensationAuto = 'Off'

        cam.Gain = p[0]
        cam.ExposureTime = p[1]
        cam.pgrExposureCompensation = p[2]
        cam.Sharpness = math.floor(p[3])
        cam.start()
        #
        return cam.get_array()


def save_image(img, p):
    time_str = str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
    filename = '%s-%d-%d-%d-%d' % (time_str, p[0], p[1], p[2], p[3])
    full_path = save_folder + "/" + filename

    save_im = Image.fromarray(img)
    save_im.save(full_path + '.jpg')


def calculate_cost(p):
    global gsharp
    print(p[0], p[1], p[2], p[3])
    img = grap_image(p)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    sharp = calculate_cost_sobel(img)
    sharp = -1 * sharp
    if sharp > gsharp:
        save_image(img, p)
        gsharp = sharp
    print(sharp)

    return sharp


def genetic():
    varbound = np.array([[1, 29], [10000, 22000], [0, 2], [100, 3000]])

    model = ga(function=calculate_cost,
               dimension=4,  # number of decision variables
               variable_type='real',
               variable_boundaries=varbound)
    model.run()


if __name__ == "__main__":
    # calculate_cost(p = [15, 20000, 1.5, 2100])
    genetic()
