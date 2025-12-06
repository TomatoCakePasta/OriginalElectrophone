from picamera2 import Picamera2
import cv2

picam2 = Picamera2()

config = picam2.create_preview_configuration()
picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("frame", frame_bgr)

    if cv2.waitKey(1) == 27:  # ESC
        break

cv2.destroyAllWindows()
picam2.stop()
