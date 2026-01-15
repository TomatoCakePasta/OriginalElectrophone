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
# (GPIO14, GPIO15, GPIO18, GPIO23) 
# = (switch 4, 3, 2, 1 from right) 
# PINS = [14, 15, 18, 23, 24]
PINS = [23, 18, 15, 14, 24]
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
selected_color = np.array([0, 0, 0], dtype=np.uint8) 
center_roi = np.zeros((100, 100, 3), dtype=np.uint8)

LED_NUMS = 8

# color_array = [
#     # red
#     Color(80, 0, 0),
#     # orange
#     Color(60, 20, 0),
#     # yellow
#     Color(40, 40, 0),
#     # green
#     Color(0, 80, 0),
#     #blue
#     Color(0, 0, 80),
#     #white
#     Color(23, 23, 23)
# ]

color_array = [
    Color(255, 0, 0),
    Color(255, 165, 0),
    Color(255, 255, 0),
    Color(0, 128, 0),
    Color(0, 0, 255),
    Color(255, 255, 255)
]

base_colors = [
    Color(255, 0, 0),
    Color(255, 165, 0),
    Color(255, 255, 0),
    Color(0, 128, 0),
    Color(0, 0, 255),
    Color(255, 255, 255)
]

isScaned = False
gl_led_idx_pingpong = 0
gl_led_pingpong_direction = 0.1

# setup function
# it runs once at the beginning
def setup():
    setupWebCamera()
    setupNeopixel()
    test_seven_colors()

# main loop
# it runs every frame
def main():
    global isScaned
    runWebCamera()
    readSwitch()

    # if isScaned:
    #     animateLedPingPong()


def setupWebCamera():
    global cap
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

def setupNeopixel():
    global strip 
    strip = WS2812SpiDriver(spi_bus=0, spi_device=0, led_count=LED_NUMS).get_strip()

    setNeopixelColor(np.array([40, 40, 40], dtype=np.uint8) )

def test_seven_colors():
    global color_array
    for i in range(len(color_array)):
        strip.set_all_pixels(color_array[i])
        strip.show()
        time.sleep(0.4)

def runWebCamera():
    global selected_color, center_roi, isScaned

    key = cv2.waitKey(1)

    # update with 's' key
    if key == ord('s'):
        takePicture()

    # ---------- display canvas ----------
    canvas_h = 220
    canvas_w = 120
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    # top: dominant color
    canvas[10:110, 10:110] = selected_color

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

def takePicture():
    global selected_color, center_roi, isScaned

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
        selected_color = get_dominant_color_mean(center_roi).astype(np.uint8)

        isScaned = True

        client.send_message("/shutter", 1)

        setNeopixelColor(selected_color)

def setNeopixelColor(bgr):
    # FIX Does it need global?
    global selected_color

    b = int(bgr[0])
    g = int(bgr[1])
    r = int(bgr[2])

    converted_color = get_nearest_color(Color(r, g, b))

    # update selected_color(g, b, r) -> nearest_color(r, g, b)
    selected_color = converted_color
    print("Selected Color", selected_color.r, selected_color.g, selected_color.b)

    # strip.set_all_pixels(Color(r, g, b))
    strip.set_all_pixels(converted_color)
    strip.show()

def get_nearest_color(input_color):
    """
    input_color : Color(r, g, b)
    return      : Color (most similar)
    """

    brightness = input_color.r + input_color.g + input_color.b
    if brightness < 30:
        return scale_color(Color(255, 255, 255), 0.1)

    def distance(c1, c2):
        return (
            (c1.r - c2.r) ** 2 +
            (c1.g - c2.g) ** 2 +
            (c1.b - c2.b) ** 2
        )

    nearest = min(
        base_colors,
        key=lambda c: distance(input_color, c)
    )

    nearest = scale_color(nearest, 1)

    return nearest

def scale_color(color, scale):
    print("Scaling color:", color.r, color.g, color.b, "by", scale)
    return Color(
        int(color.r * scale),
        int(color.g * scale),
        int(color.b * scale)
    )

def animateLedPingPong():
    global gl_led_idx_pingpong
    global gl_led_pingpong_direction
    global isScaned
    global strip
    converted_led_idx = int(gl_led_idx_pingpong)

    strip.set_all_pixels(Color(0, 0, 0))

    for i in range(converted_led_idx):
        # FIX
        strip.set_pixel_color(i, bgr_to_color(selected_color))
    strip.show()

    gl_led_idx_pingpong += gl_led_pingpong_direction
    converted_led_idx = int(gl_led_idx_pingpong)

    if converted_led_idx == LED_NUMS:
        converted_led_idx = LED_NUMS - 1
        gl_led_pingpong_direction *= -1

    # end process
    if (converted_led_idx == 0) and (gl_led_pingpong_direction < 0):
        gl_led_pingpong_direction *= -1
        gl_led_idx_pingpong = 0
        isScaned = False

def bgr_to_color(bgr):
    return Color(int(bgr[2]), int(bgr[1]), int(bgr[0]))

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

    send_message = None

    # ★ 初回ガード
    if prev_states is None:
        prev_states = states
        return

    # --- ★ GPIO24 が押された瞬間を検出 ---
    gpio24_idx = 4  # PINS の中での位置

    if prev_states[gpio24_idx] == 1 and states[gpio24_idx] == 0:
        print("GPIO24 pressed → takePicture()")
        takePicture()

    # send only when state changes
    # e.x.
    # (0, 0, 0, 0)  --> (1, 0, 0, 0) --> send
    # (1, 0, 0, 0)  --> (1, 0, 0, 0) --> no send
    if states != prev_states:
        converted = tuple(
            2 if s == p else s
            for s, p in zip(states, prev_states)
        )

        # whether switch[2], [3] is pushed
        # pressed_23 = any(
        #     prev_states[i] == 1 and states[i] == 0
        #     for i in (2, 3)
        # )

        # if pressed_23:
        #     converted = tuple(
        #         2 if (i in (2, 3) and s == p) else s
        #         for i, (s, p) in enumerate(zip(states, prev_states))
        #     )

        #     print("raw      :", states)
        #     print("converted:", converted)
        #     send_message = converted
        # else:
        #     send_message = states

        send_message = converted

        prev_states = states

        client.send_message("/btns", send_message)
    

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
        time.sleep(1)

        GPIO.cleanup()
        cv2.destroyAllWindows()