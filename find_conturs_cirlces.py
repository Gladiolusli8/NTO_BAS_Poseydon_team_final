import cv2
import numpy as np
from math import atan2, cos, sin, sqrt, pi
import PCA

def nothing(x):
    pass

def drawAxis(img, p_, q_, colour, scale):
    p = list(p_)
    q = list(q_)
    angle = atan2(p[1] - q[1], p[0] - q[0])
    hypotenuse = sqrt((p[1] - q[1])**2 + (p[0] - q[0])**2)
    q[0] = p[0] - scale * hypotenuse * cos(angle)
    q[1] = p[1] - scale * hypotenuse * sin(angle)
    cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv2.LINE_AA)
    p[0] = q[0] + 9 * cos(angle + pi / 4)
    p[1] = q[1] + 9 * sin(angle + pi / 4)
    cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv2.LINE_AA)
    p[0] = q[0] + 9 * cos(angle - pi / 4)
    p[1] = q[1] + 9 * sin(angle - pi / 4)
    cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv2.LINE_AA)

def getOrientation(pts, img, manual_center):
    data_pts = pts.reshape(-1, 2).astype(np.float64)
    mean = np.array([manual_center], dtype=np.float64)
    _, eigenvectors, eigenvalues = cv2.PCACompute2(data_pts, mean=mean)

    cntr = (int(manual_center[0]), int(manual_center[1]))
    cv2.circle(img, cntr, 3, (255, 0, 255), 2)

    # Рисуем стрелки точно как в туториале (0.02 - коэффициент масштаба)
    p1 = (cntr[0] + 0.02 * eigenvectors[0, 0] * eigenvalues[0, 0],
          cntr[1] + 0.02 * eigenvectors[0, 1] * eigenvalues[0, 0])
    p2 = (cntr[0] - 0.02 * eigenvectors[1, 0] * eigenvalues[1, 0],
          cntr[1] - 0.02 * eigenvectors[1, 1] * eigenvalues[1, 0])
    
    drawAxis(img, cntr, p1, (0, 255, 0), 1)   # Главная ось
    drawAxis(img, cntr, p2, (255, 255, 0), 5) # Поперечная ось

    angle = atan2(eigenvectors[0, 1], eigenvectors[0, 0])
    return np.rad2deg(angle)

def get_elipse_radius(img, conturs, draw=False):
    centers = []
    fcon = []
    for cnt in conturs:
        if cv2.contourArea(cnt) > 100:
            if len(cnt) >= 6:
                ellipse = cv2.fitEllipse(cnt)
                (cx, cy), (width, height), angle = ellipse
                if width / 2 > 150 and height / 2 > 150:
                    center = (int(cx), int(cy))
                    centers.append(center)
                    fcon.append(cnt)
                    if draw == True:
                        cv2.ellipse(img, ellipse, (0, 255, 0), 2)
                        cv2.circle(img, center, 5, (0, 0, 255), -1)
                    print(f"Найден эллипс: центр {center}, радиусы: {width/2:.1f}, {height/2:.1f}")
    return centers, img, fcon

# Настройка окон
cv2.namedWindow('controls')
cv2.createTrackbar('min_h', 'controls', 0, 179, nothing)
cv2.createTrackbar('min_s', 'controls', 0, 255, nothing)
cv2.createTrackbar('min_v', 'controls', 0, 255, nothing)
cv2.createTrackbar('max_h', 'controls', 179, 179, nothing)
cv2.createTrackbar('max_s', 'controls', 255, 255, nothing)
cv2.createTrackbar('max_v', 'controls', 255, 255, nothing)

im = cv2.imread("circles1.png") # Убедитесь, что файл существует

video = cv2.VideoCapture("circles.mp4")

while video.isOpened():
    ret, frame = video.read()

    min_h = cv2.getTrackbarPos('min_h', 'controls')
    min_s = cv2.getTrackbarPos('min_s', 'controls')
    min_v = cv2.getTrackbarPos('min_v', 'controls')
    max_h = cv2.getTrackbarPos('max_h', 'controls')
    max_s = cv2.getTrackbarPos('max_s', 'controls')
    max_v = cv2.getTrackbarPos('max_v', 'controls')

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    lower = np.array([min_h, min_s, min_v])
    upper = np.array([max_h, max_s, max_v])
    mask = cv2.inRange(hsv, lower, upper)
    
    # Очистка маски
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=4)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    centers, img, fcon = get_elipse_radius(frame, contours, draw=True)
    if len(centers) > 0 and contours is not None:
        angle = PCA.get_orientation_pca(cnt=contours[0], center_coords=centers[0], img_to_draw=frame)
        print(angle)
    cv2.imshow('Detected Ellipses', frame)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

#cv2.imshow('Detected Ellipses', img)
video.release()

cv2.destroyAllWindows()
