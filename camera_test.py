from picamera2 import Picamera2
from pythonosc import udp_client
import cv2
import time

# switch
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

PINS = [14, 15, 18, 23]
prev_states = None

for pin in PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)    

# set up OSC
IP = "127.0.0.1"   
PORT = 3000        

client = udp_client.SimpleUDPClient(IP, PORT)

# set up camera
"""
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}
)
picam2.configure(config)
picam2.start()
"""

def main():
    # get camera
#     runCamera()
    readSwitch2()

# ?????????????
def get_dominant_color_mean(frame):
    small = cv2.resize(frame, (50, 50))  # ?????
    mean_color = small.mean(axis=(0, 1))  # B,G,R ???
    return mean_color.astype(int)  # (B, G, R)

def runCamera():
    frame = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    color = get_dominant_color_mean(frame)
    
    cv2.rectangle(frame, (0, 0), (100, 100), color.tolist(), -1)

    cv2.imshow("frame", frame)

    print("Dominant Color (B, G, R):", color)
    
    # send osc
    sendOSC(color.tolist())

    if cv2.waitKey(1) == 27:  # ESC
        cv2.destroyAllWindows()
        picam2.stop()

def readSwitch():
    btn1 = GPIO.input(14)
    btn2 = GPIO.input(15)
    btn3 = GPIO.input(18)
    btn4 = GPIO.input(23)
    
    print(f"{btn1} {btn2} {btn3} {btn4}")
    time.sleep(0.3)
    
def readSwitch2():
    global prev_states

    states = tuple(GPIO.input(pin) for pin in PINS)

    if states != prev_states:
        print(" ".join(map(str, states)))
        prev_states = states
        client.send_message("/btns", states)
        

    

def sendOSC(color):
    client.send_message("/value", color)
    time.sleep(0.1)

if __name__ == "__main__":
    while True:
        main()