import numpy as np
import cv2

def detect(img, detector):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, rej = detector.detectMarkers(gray)
    return ids, corners, rej

