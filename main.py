import tkinter as tk
import onnx
from onnx2keras import onnx_to_keras

from PIL import Image
from tensorflow.python.keras.applications.densenet import decode_predictions


def print_hi(name):
    print("Hi, {0}".format(name))  # Press ⌘F8 to toggle the breakpoint.


if __name__ == '__main__':
    # Load ONNX model
    onnx_model = onnx.load('network.onnx')

    # DEBUG:onnx2keras:Input 0 -> imageinput_Mean.
    # DEBUG:onnx2keras:Input 1 -> conv_1_W.
    # DEBUG:onnx2keras:Input 2 -> conv_1_B.
    # DEBUG:onnx2keras:Input 3 -> batchnorm_1_scale.
    # DEBUG:onnx2keras:Input 4 -> batchnorm_1_B.
    # DEBUG:onnx2keras:Input 5 -> batchnorm_1_mean.
    # DEBUG:onnx2keras:Input 6 -> batchnorm_1_var.
    # DEBUG:onnx2keras:Input 7 -> conv_2_W.
    # DEBUG:onnx2keras:Input 8 -> conv_2_B.
    # DEBUG:onnx2keras:Input 9 -> batchnorm_2_scale.
    # DEBUG:onnx2keras:Input 10 -> batchnorm_2_B.
    # DEBUG:onnx2keras:Input 11 -> batchnorm_2_mean.
    # DEBUG:onnx2keras:Input 12 -> batchnorm_2_var.
    # DEBUG:onnx2keras:Input 13 -> fc_W.
    # DEBUG:onnx2keras:Input 14 -> fc_B.
    # DEBUG:onnx2keras:Input 15 -> imageinput.
    k_model = onnx_to_keras(onnx_model, input(['imageinput_Mean']))

    image = Image.open('images/defect/1.jpg')
    image = image.resize((960, 600))

    r1 = image.crop((0, 0, 320, 300))
    prediction = k_model.predict(r1)

    r2 = image.crop((321, 0, 640, 300))
    print(decode_predictions(k_model.predict(r2), top=3)[0])
    # r3 = image.crop((641, 0, 960, 300))
    # prediction = k_model.predict(r3)
    # r4 = image.crop((0, 300, 320, 600))
    # prediction = k_model.predict(r4)
    # r5 = image.crop((321, 301, 641, 600))
    # prediction = k_model.predict(r5)
    # r6 = image.crop((641, 301, 960, 600))
    # prediction = k_model.predict(r6)

    # window = tk.Tk()
    # label = tk.Label(text="Python rocks!")
    # label.pack()
    #
    # window.mainloop()
