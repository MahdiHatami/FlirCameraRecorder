import numpy as np
import cv2
import matplotlib.pyplot as plt


def sobel():
    # img = cv2.imread('atki.jpg')
    # img = plt.imread('atki.jpg')
    # plt.imshow(img)

    img = cv2.imread("moving.jpg")

    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)  # x
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)  # y

    gradient_magnitude = np.sqrt(np.square(sobelx) + np.square(sobely))

    a = cv2.Laplacian(img, cv2.CV_64F).var()
    print(a)

    plt.imshow(gradient_magnitude)
    plt.title('Image')
    plt.show()


def detect_blur_fft(image, size=60):
    # grab the dimensions of the image and use the dimensions to
    # derive the center (x, y)-coordinates
    (h, w) = image.shape
    (cX, cY) = (int(w / 2.0), int(h / 2.0))

    fft = np.fft.fft2(image)
    fftShift = np.fft.fftshift(fft)

    # zero-out the center of the FFT shift (i.e., remove low
    # frequencies), apply the inverse shift such that the DC
    # component once again becomes the top-left, and then apply
    # the inverse FFT
    fftShift[cY - size:cY + size, cX - size:cX + size] = 0
    fftShift = np.fft.ifftshift(fftShift)
    recon = np.fft.ifft2(fftShift)

    # compute the magnitude spectrum of the reconstructed image,
    # then compute the mean of the magnitude values
    magnitude = 20 * np.log(np.abs(recon))
    mean = np.mean(magnitude)
    # the image will be considered "blurry" if the mean value of the
    # magnitudes is less than the threshold value
    return mean


def put_text_on_image(img, blurry):
    # draw on the image, indicating whether or not it is blurry
    image = np.dstack([img] * 3)
    color = (0, 0, 255) if blurry else (0, 255, 0)
    text = "Blurry ({:.4f})" if blurry else "Not Blurry ({:.4f})"
    text = text.format(mean)
    cv2.putText(image, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                color, 2)


if __name__ == '__main__':
    img = cv2.imread('atki.jpg', 0)
    mean = detect_blur_fft(img, size=60)
    print(mean)
