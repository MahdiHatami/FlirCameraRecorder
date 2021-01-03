import math
from geneticalgorithm import geneticalgorithm as ga
import cv2
from simple_pyspin import Camera
import numpy as np

running = True


def calculate_cost_lap(img):
    lap = cv2.Laplacian(img, cv2.CV_64F).var()
    return lap


def calculate_cost_sobel(img):
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)  # x
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)  # y
    sobel_mag = math.sqrt(pow(sobelx, 2) + pow(sobely, 2))
    sobel_kenar_yaniti = sum(sum(sobel_mag))
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
        cam.Sharpness = p[3]
        cam.start()
        #
        return cam.get_image()


def calculate_cost(p):
    img = grap_image(p)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    sharp = calculate_cost_sobel(img)
    return -1 * sharp


def genetic():
    varbound = np.array([1, 30], [10000, 30000], [0, 3], [100, 3000])

    model = ga(function=calculate_cost,
               dimension=4,  # number of decision variables
               variable_type='int',
               variable_boundaries=varbound,
               algorithm_parameters={
                   "max_num_iteration": 1000,
                   'max_iteration_without_improv': 100
               })
    model.run()


if __name__ == "__main__":
    genetic()
