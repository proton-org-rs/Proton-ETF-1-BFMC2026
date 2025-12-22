import cv2
import numpy as np
from picamera2 import Picamera2
import threading

prev_left_fit_average = None
prev_right_fit_average = None

def canny(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    canny = cv2.Canny(blur, 170, 200)
    return canny

def region_of_interest(image):
    height = image.shape[0]
    width = image.shape[1]
    crop = image[50:300, 0:width]
    return crop

def make_coordinates(image, line_parameters):
    slope, intercept = line_parameters
    y1 = 50
    y2 = 180
    x1 = int((y1 - intercept + 1800) / slope)
    x2 = int((y2 - intercept + 1800) / slope)
    return np.array([x1, y1, x2, y2])

def average_slope_intercept(image, lines):
    global prev_left_fit_average, prev_right_fit_average
    left_fit = []
    right_fit = []
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        parameters = np.polyfit((x1, x2), (y1, y2), 1)
        slope = parameters[0]
        intercept = parameters[1]
        if slope < -0.1:
            left_fit.append((slope, intercept))
        elif slope > 0.1:
            right_fit.append((slope, intercept))
    left_fit_average = np.average(left_fit, axis=0)
    right_fit_average = np.average(right_fit, axis=0)
    try:
        left_line = make_coordinates(image, left_fit_average)
        right_line = make_coordinates(image, right_fit_average)
        prev_left_fit_average = left_fit_average
        prev_right_fit_average = right_fit_average
    except:
        left_line = make_coordinates(image, prev_left_fit_average)
        right_line = make_coordinates(image, prev_right_fit_average)
    return np.array([left_line, right_line])

def display_lines(image, lines):
    line_image = np.zeros_like(image)
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1 + 50), (x2, y2 + 50), (0, 255, 0), 20)
    return line_image

picam2 = Picamera2()
videoconfig = picam2.create_video_configuration(
    main={"size": (640, 480)},
    lores={"size": (640, 480)},
    display="lores"
)
picam2.configure(videoconfig)
picam2.start()

while True:
    frame = picam2.capture_array()
    canny_image = canny(frame)
    cropped_image = region_of_interest(canny_image)
    lines = cv2.HoughLinesP(
        cropped_image,
        1,
        np.pi / 180,
        15,
        np.array([]),
        minLineLength=10,
        maxLineGap=5
    )
    if lines is not None:
        line_image = display_lines(frame, lines)
        combo_image = cv2.addWeighted(frame, 1, line_image, 1, 1)
        slika = combo_image
    else:
        slika = frame
    if slika is not None:
        slika = cv2.cvtColor(slika, cv2.COLOR_RGB2BGR)
        cv2.imshow("prikaz", slika)
    if cv2.waitKey(1) & 0xFF == 27:
        break

picam2.stop()
cv2.destroyAllWindows()