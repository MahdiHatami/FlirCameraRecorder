import PySpin
import cv2
import EasyPySpin

cap = EasyPySpin.VideoCapture(0)

cap.set(cv2.cv2.CAP_PROP_FPS, 5)
cap.set(cv2.CAP_PROP_EXPOSURE, 100000)  # us
cap.set(cv2.CAP_PROP_GAIN, 10)  # dB
cap.set(cv2.CAP_PROP_XI_SHUTTER_TYPE, '')

print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# advanced params
# QuickSpinAPI example
cap.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)
cap.cam.PixelFormat.SetValue(PySpin.NUM_SENSORSHUTTERMODE)

# GenAPI example
node_exposureAuto = PySpin.CEnumerationPtr(cap.nodemap.GetNode("ExposureAuto"))
exposureAuto = PySpin.CEnumEntryPtr(
    node_exposureAuto.GetEntryByName("Once")).GetValue()
node_exposureAuto.SetIntValue(exposureAuto)

ret, frame = cap.read()

cv2.imwrite("frame.png", frame)

cap.release()
