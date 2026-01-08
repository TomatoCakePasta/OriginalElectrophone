# include necessary libraries
# A library provides ready-made functions, 
# classes, or modules that you can call from your own program.
# Pros / advantages of libraries
# - Save development time
# - Reuse code
# - Improve code quality
# - Access to specialized functionality

# for OSC data sending
from pythonosc import udp_client

# for image processing
import cv2

# for time delay
import time

import numpy as np

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

# for Neo-pixel LED tape
from rpi5_ws2812.ws2812 import Color, WS2812SpiDriver

strip = None

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

# --- global ---
# initial color black
color = np.array([0, 0, 0], dtype=np.uint8) 
center_roi = np.zeros((100, 100, 3), dtype=np.uint8)

# setup function
# it runs once at the beginning
def setup():
    setupWebCamera()
    setupNeopixel()

# main loop
# it runs every frame
def main():
    runWebCamera()
    readSwitch()

def setupWebCamera():
    global cap
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

def setupNeopixel():
    global strip 
    strip = WS2812SpiDriver(spi_bus=0, spi_device=0, led_count=8).get_strip()

    setNeopixelColor(np.array([40, 40, 40], dtype=np.uint8) )

def runWebCamera():
    global color, center_roi

    key = cv2.waitKey(1)

    # update with 's' key
    if key == ord('s'):
        ret, frame = cap.read()
        if ret:
            h, w, _ = frame.shape
            cx = w // 2
            cy = h // 2
            half = 50

            # cut out center 100x100 region
            center_roi = frame[
                cy - half : cy + half,
                cx - half : cx + half
            ].copy()  # important to use .copy() so that original frame is not affected

            # get dominant color from the center region
            color = get_dominant_color_mean(center_roi).astype(np.uint8)

            client.send_message("/shutter", 1)

            setNeopixelColor(color)


    # ---------- display canvas ----------
    canvas_h = 220
    canvas_w = 120
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    # top: dominant color
    canvas[10:110, 10:110] = color

    # bottom: real camera image 
    canvas[120:220, 10:110] = center_roi

    cv2.imshow("Center + Color", canvas)

    # exit with 'ESC' key
    if key == 27:
        cap.release()
        cv2.destroyAllWindows()
        GPIO.cleanup()
        strip.set_all_pixels(Color(0, 0, 0))
        strip.show()
        exit(0)
        return False

    return True

def setNeopixelColor(bgr):
    b = int(bgr[0] * 0.2)
    g = int(bgr[1] * 0.2)
    r = int(bgr[2] * 0.2)

    strip.set_all_pixels(Color(r, g, b))
    strip.show()

# get dominant color using mean method
# Get the most common color on the screen

# ex. many apples on the white table
# it gets "red" as the dominant color
def get_dominant_color_mean(frame):
    # resize frame to speed up processing
    # Image consists of very small pixels
    # 50 x 50 = 2500 pixels
    small = cv2.resize(frame, (50, 50))  

    # calculate average color of the small image
    mean_color = small.mean(axis=(0, 1))  
    # change data type from float to int
    return mean_color.astype(int)  # (B, G, R)

# ex. when frame resize (2, 2)
# each pixel has 3 color values (B, G, R)
# small = [
#   [ [10, 20, 30],  [40, 50, 60] ],
#   [ [70, 80, 90],  [100,110,120] ]
# ]

# Blue
# (10 + 40 + 70 + 100) / 4
# = 220 / 4
# = 55

# Green
# (20 + 50 + 80 + 110) / 4
# = 260 / 4
# = 65

# Red
# (30 + 60 + 90 + 120) / 4
# = 300 / 4
# = 75
# mean_color = [55.0, 65.0, 75.0]

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
    try:
        while True:
            main()

    finally:
        strip.set_all_pixels(Color(0, 0, 0))
        strip.show()
        time.sleep(500)

        GPIO.cleanup()
        cv2.destroyAllWindows()