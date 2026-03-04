import numpy as np
import cv2 as cv

img1 = cv.imread("video/image_l/square.png")
img = cv.cvtColor(img1, cv.COLOR_BGR2GRAY)
assert img is not None, "file could not be read, check with os.path.exists()"
ret, thresh = cv.threshold(img, 127, 255, 0)
contours, hierarchy = cv.findContours(thresh, 1, 2)

biggest_contur = max(contours, key=cv.contourArea)
cv.drawContours(img1, contours, -1, (0, 0, 255), 3)
M = cv.moments(contours[0])
cx, cy = -1, -1
if M['m00'] != 0:
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    cv.circle(img1, (cx, cy), 10, (255, 0, 0), 2)

cv.imshow('res', img1)
k = cv.waitKey(0)
if k == 27:
    cv.destroyAllWindows()
