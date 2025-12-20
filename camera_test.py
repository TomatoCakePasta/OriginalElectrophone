# include necessary libraries
# A library provides ready-made functions, 
# classes, or modules that you can call from your own program.
# Pros / advantages of libraries
# - Save development time
# - Reuse code
# - Improve code quality
# - Access to specialized functionality
from picamera2 import Picamera2

# for OSC data sending
from pythonosc import udp_client

# for image processing
import cv2

# for time delay
import time

# for GPIO input
import RPi.GPIO as GPIO
# RPi.GPIO library allows you to control the GPIO pins 
# on a Raspberry Pi.

# What is GPIO?
# GPIO stands for General Purpose Input/Output.
# GPIO pins can be used to read input signals (like button presses)
# or send output signals (like turning on an LED).

# set up GPIO
# You can choose GPIO.BCM or GPIO.BOARD numbering system.
# BCM refers to the Broadcom SOC channel numbers,
# ex. GPIO14, GPIO15, etc.,

# while BOARD refers to the physical pin numbers on the Raspberry Pi board.
# ex. Pin 8 is GPIO14 in BCM numbering.

# --- Just different ways to refer to the same pins ---
GPIO.setmode(GPIO.BCM)

# for switch input
# Using 4 GPIO pins for 4 switches
# GPIO14, GPIO15, GPIO18, GPIO23
PINS = [14, 15, 18, 23]
prev_states = None

# set up input pins with pull-up resistors
# You just remember to set up the pins you want to use as inputs.
for pin in PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)    

# set up OSC
# what is IP and PORT?
# IP: Internet Protocol address, identifies a device on a network.
# PORT: A communication endpoint, like a door number for data.

# --- IP is similar to apartment address, ---
# --- PORT is like room number within that building. ---
IP = "127.0.0.1"   
PORT = 3000        

client = udp_client.SimpleUDPClient(IP, PORT)

# setup function
# it runs once at the beginning
def setup():
    setupCamera()

# main loop
# it runs every frame
def main():
    # get camera
    # runCamera()
    readSwitch()

# reference
# https://github.com/raspberrypi/picamera2/blob/main/examples/capture_png.py
# please check the following directory
# examples/capture_png.py
def setupCamera():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
    picam2.configure(config)
    picam2.start()

# run camera and process frame
def runCamera():
    # reference
    # https://github.com/raspberrypi/picamera2/blob/main/examples/opencv_face_detect.py
    # please check the following directory
    # examples/opencv_face_detect.py
    frame = picam2.capture_array()
    # frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    color = get_dominant_color_mean(frame)
    
    # draw rectangle with dominant color
    # position: (0, 0), size: 100 x 100
    cv2.rectangle(frame, (0, 0), (100, 100), color.tolist(), -1)

    # display camera frame on window
    cv2.imshow("frame", frame)

    print("Dominant Color (B, G, R):", color)
    
    # send osc
    # send color as a list to Pure Data
    sendOSC(color.tolist())

    # exit on ESC key
    if cv2.waitKey(1) == 27:  # ESC
        cv2.destroyAllWindows()
        picam2.stop()

# get dominant color using mean method
# Get the most common color on the screen

# ex. many apples on the white table
# it gets "red" as the dominant color
def get_dominant_color_mean(frame):
    small = cv2.resize(frame, (50, 50))  
    mean_color = small.mean(axis=(0, 1))  
    return mean_color.astype(int)  # (B, G, R)

def readSwitch():
    global prev_states

    # tuple is like array / list but immutable
    # when switch is pressed 0
    # when switch is not pressed 1
    # it reads all 4 switch states as a tuple 
    # (0, 0, 0, 0)
    # when switch 2 is pressed
    # it reads (1, 0, 1, 1)
    states = tuple(GPIO.input(pin) for pin in PINS)

    # send only when state changes
    # e.x.
    # (0, 0, 0, 0)  --> (1, 0, 0, 0) --> send
    # (1, 0, 0, 0)  --> (1, 0, 0, 0) --> no send
    if states != prev_states:
        print(" ".join(map(str, states)))
        prev_states = states
        client.send_message("/btns", states)
    

def sendOSC(color):
    client.send_message("/value", color)
    time.sleep(0.1)

if __name__ == "__main__":
    setup()
    while True:
        main()