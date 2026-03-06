import cv2
import numpy as np
import PCA

def get_elipse_radius(img, conturs, draw=False):
    centers = []
    fcon = []
    for cnt in conturs:
        if cv2.contourArea(cnt) > 100000 and cv2.contourArea(cnt) < 350000:
            if len(cnt) >= 6:
                ellipse = cv2.fitEllipse(cnt)
                (cx, cy), (width, height), angle = ellipse
                if width / 2 > 50 and height / 2 > 50:
                    center = (int(cx), int(cy))
                    centers.append(center)
                    fcon.append(cnt)
                    if draw == True:
                        cv2.ellipse(img, ellipse, (0, 255, 0), 2)
                        cv2.circle(img, center, 5, (0, 0, 255), -1)
                    print(f"Найден эллипс: центр {center}, радиусы: {width/2:.1f}, {height/2:.1f}")
    return centers, img, fcon

def get_binary_image(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    blurred = cv2.medianBlur(hsv, 5)
    mask = cv2.inRange(blurred, (0, 0, 0), (180, 255, 100))
    kernel = np.ones((4, 4), np.uint8)

    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
    return closed

"""
img = cv2.imread("test_2.png")
cv2.imshow("img", img)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blurred = cv2.medianBlur(hsv, 5)
mask = cv2.inRange(blurred, (0, 0, 0), (180, 255, 100))
kernel = np.ones((4,4), np.uint8)
erode_mask = cv2.erode(mask, kernel, iterations=4)
cv2.imshow("erode", erode_mask)

kernel_dil = np.ones((4, 4), np.uint8)
dilate_mask = cv2.dilate(erode_mask, kernel_dil, iterations=1)
cv2.imshow("dilate", dilate_mask)

opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
erode_mask = cv2.erode(closed, kernel, iterations=1)
cv2.imshow('erode', erode_mask)
"""
img = cv2.imread("test_1.png")
closed = get_binary_image(img)

min_area = 200
filtered_mask = np.zeros_like(closed)
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)

for i in range(1, num_labels):  
    area = stats[i, cv2.CC_STAT_AREA]
    if area > min_area:
        filtered_mask[labels == i] = 255

contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
for c in contours:
    #print(cv2.contourArea(c))
    if cv2.contourArea(c) > 0 and cv2.contourArea(c) < 350000:
        cv2.drawContours(img, c, -1, (0, 255, 0), 3)
        center, img, fcon = get_elipse_radius(img, [c], draw=True)
        print(center)
        if len(center) > 0:
            angle = PCA.get_orientation_pca(cnt=c, center_coords=center, img_to_draw=img)
            print(angle)
cv2.imshow('Detected Ellipses', img)

cv2.waitKey(0)
cv2.destroyAllWindows() 
