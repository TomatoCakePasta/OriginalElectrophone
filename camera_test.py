from picamera2 import Picamera2
import cv2

# ?????????????
def get_dominant_color_mean(frame):
    small = cv2.resize(frame, (50, 50))  # ?????
    mean_color = small.mean(axis=(0, 1))  # B,G,R ???
    return mean_color.astype(int)  # (B, G, R)


picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}
)
picam2.configure(config)
picam2.start()

while True:
    frame = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    color = get_dominant_color_mean(frame_bgr)
    
    cv2.rectangle(frame_bgr, (0, 0), (100, 100), color.tolist(), -1)

    cv2.imshow("frame", frame_bgr)

    # ?????

    # ????
    print("Dominant Color (B, G, R):", color)

    if cv2.waitKey(1) == 27:  # ESC
        break

cv2.destroyAllWindows()
picam2.stop()
