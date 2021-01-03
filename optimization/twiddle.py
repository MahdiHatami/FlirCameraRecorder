import math
import cv2
from simple_pyspin import Camera
from matplotlib import pyplot as plt
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


def calculate_cost(img):
    img = cv2.GaussianBlur(img, (3, 3), 0)
    sharp = calculate_cost_sobel(img)
    return sharp

    # plt.subplot(2, 2, 1), plt.imshow(img, cmap='gray')
    # plt.title('Original'), plt.xticks([]), plt.yticks([])
    # plt.subplot(2, 2, 2), plt.imshow(laplacian, cmap='gray')
    # plt.title('Laplacian'), plt.xticks([]), plt.yticks([])
    # plt.subplot(2, 2, 3), plt.imshow(sobelx, cmap='gray')
    # plt.title('Sobel X'), plt.xticks([]), plt.yticks([])
    # plt.subplot(2, 2, 4), plt.imshow(sobely, cmap='gray')
    # plt.title('Sobel Y'), plt.xticks([]), plt.yticks([])

    # return lap


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


def twiddle():
    # Choose an initialization parameter vector
    # p = {'gain': 15, 'exp': 20000, 'exp_comp': 1.5, 'sharpness': 2100}
    p = [15, 20000, 1.5, 2100]
    # Define potential changes
    dp = [1, 1000, 0.1, 50]
    # Calculate the error
    img = grap_image(p)
    best_sharp = calculate_cost(img)

    threshold = 10

    while sum(dp) > threshold:
        for i in range(len(p)):
            p[i] += dp[i]
            img = grap_image(p)
            sharp = calculate_cost(img)

            if sharp > best_sharp:  # There was some improvement
                best_sharp = sharp
                dp[i] *= 1.1
                # save image and param (img)
            else:  # There was no improvement
                p[i] -= 2 * dp[i]  # Go into the other direction
                img = grap_image(p)
                sharp = calculate_cost(img)

                if sharp > best_sharp:  # There was an improvement
                    best_sharp = sharp
                    dp[i] *= 1.05
                    # save image and param
                else:  # There was no improvement
                    p[i] += dp[i]
                    # As there was no improvement, the step size in either
                    # direction, the step size might simply be too big.
                    dp[i] *= 0.95


if __name__ == "__main__":
    twiddle()
