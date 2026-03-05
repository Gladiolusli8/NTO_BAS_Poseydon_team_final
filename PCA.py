from __future__ import print_function
from __future__ import division
import cv2 as cv
import numpy as np
import argparse
from math import atan2, cos, sin, sqrt, pi


def drawAxis(img, p_, q_, colour, scale):
    p = list(p_)
    q = list(q_)

    angle = atan2(p[1] - q[1], p[0] - q[0])  # angle from q to p
    hypotenuse = sqrt((p[1] - q[1])**2 + (p[0] - q[0])**2)
    # Here we lengthen the arrow by a factor of scale
    q[0] = p[0] - scale * hypotenuse * cos(angle)
    q[1] = p[1] - scale * hypotenuse * sin(angle)
    cv.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv.LINE_AA)

    # create the arrow hooks
    p[0] = q[0] + 9 * cos(angle + pi / 4)
    p[1] = q[1] + 9 * sin(angle + pi / 4)
    cv.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv.LINE_AA)

    p[0] = q[0] + 9 * cos(angle - pi / 4)
    p[1] = q[1] + 9 * sin(angle - pi / 4)
    cv.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv.LINE_AA)

def getOrientation(pts, img):

    sz = len(pts)
    data_pts = np.empty((sz, 2), dtype=np.float64)
    for i in range(data_pts.shape[0]):
        data_pts[i, 0] = pts[i, 0, 0]
        data_pts[i, 1] = pts[i, 0, 1]

    # Perform PCA analysis
    mean = np.empty((0))
    mean, eigenvectors, eigenvalues = cv.PCACompute2(data_pts, mean)

    # Store the center of the object
    cntr = (int(mean[0, 0]), int(mean[0, 1]))

    cv.circle(img, cntr, 3, (255, 0, 255), 2)
    p1 = (cntr[0] + 0.02 * eigenvectors[0, 0] * eigenvalues[0, 0],
          cntr[1] + 0.02 * eigenvectors[0, 1] * eigenvalues[0, 0])
    p2 = (cntr[0] - 0.02 * eigenvectors[1, 0] * eigenvalues[1, 0],
          cntr[1] - 0.02 * eigenvectors[1, 1] * eigenvalues[1, 0])
    drawAxis(img, cntr, p1, (0, 255, 0), 1)
    drawAxis(img, cntr, p2, (255, 255, 0), 5)

    # orientation in radians
    angle = atan2(eigenvectors[0, 1], eigenvectors[0, 0])
    
    return angle

def get_angle_pca(image_path=None, img=None):
    if image_path is not None:
        img = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
    contours, _ = cv.findContours(img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    if not contours:
        return None
    
    largest_contour = max(contours, key=cv.contourArea)
    points = largest_contour.reshape(-1, 2).astype(np.float32)
    mean, eigenvectors = cv.PCACompute(points, mean=None)
    main_direction = eigenvectors[0]
    angle = np.arctan2(main_direction[1], main_direction[0]) * 180 / np.pi
    return angle

def draw_main_axis(img, contour, color=(0, 255, 0), length=100):
    points = contour.reshape(-1, 2).astype(np.float32)
    
    mean, eigenvectors = cv.PCACompute(points, mean=None)
    center = (int(mean[0, 0]), int(mean[0, 1]))
    
    right_end = (int(center[0] + length), int(center[1]))
    cv.line(src, (int(center[0]), int(center[1])), right_end, (255, 255, 255), 2)
    
    return center

"""
src = cv.imread('drone.png')
if src is None:
    print('Could not open or find the image: ', src)
    exit(0)

cv.imshow('src', src)

gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
_, bw = cv.threshold(gray, 50, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)

contours, _ = cv.findContours(bw, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)

for i, c in enumerate(contours):
    area = cv.contourArea(c)
    if area < 1e2 or 1e5 < area:
        continue

    cv.drawContours(src, contours, i, (0, 0, 255), 2)
    src1 = src.copy()
    angle = getOrientation(c, src)
    angle1 = get_angle_pca('drone.png')
    print(angle)
    print(angle1)
    draw_main_axis(src, c)

cv.imshow('output', src)
cv.waitKey()
"""