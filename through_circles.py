import cv2
import numpy as np
import PCA
import filters

img = cv2.imread('roi_example.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

video = cv2.VideoCapture("circles.mp4")

def get_pitch_roll(frame, get_back=False):
    closed = filters.get_binary_image(frame)
    min_area = 20000
    filtered_mask = np.zeros_like(closed)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=4)

    angles_x = []
    angles_y = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        #print(area)
        if area > min_area < 350000:
            # Создаём маску только для текущей компоненты
            component_mask = (labels == i).astype(np.uint8) * 255

            # Вычисляем моменты
            M = cv2.moments(component_mask)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                # Центральные моменты второго порядка
                mu20 = M['mu20']
                mu02 = M['mu02']
                mu11 = M['mu11']

                # Угол ориентации главной оси (в радианах)
                theta_x = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)
                angle_deg_x = np.degrees(theta_x)  # если нужен в градусах
                angles_x.append(angle_deg_x)

                angle_from_y = np.pi / 2 - theta_x
                angle_from_y_deg = np.degrees(angle_from_y)
                angles_y.append(angle_from_y_deg)

                # Рисуем центр
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                # Рисуем линию, показывающую ориентацию (длина 50 пикселей)
                length = 50
                x2 = int(cx + length * np.cos(theta_x))
                y2 = int(cy - length * np.sin(angle_from_y))
                cv2.line(frame, (cx, cy), (x2, y2), (255, 0, 0), 2)

                # Можно также нарисовать контур всей компоненты для наглядности
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
        else:
            angles_x.append(0.0)
            angles_y.append(90.0)
    if get_back == True: 
        return angles_x, angles_y, frame
    return angles_x, angles_y
"""
while video.isOpened():
    ret, frame = video.read()
    angle_x, angle_y, get_back = get_pitch_roll(frame=frame, get_back=True)
    print(f"{angle_x} {angle_y}")
    cv2.imshow("ellipses", get_back)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break
"""
"""
while video.isOpened():
    ret, frame = video.read()

    closed = filters.get_binary_image(frame)
    min_area = 20000
    filtered_mask = np.zeros_like(closed)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=4)

    angles_x = []
    angles_y = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        #print(area)
        if area > min_area < 350000:
            # Создаём маску только для текущей компоненты
            component_mask = (labels == i).astype(np.uint8) * 255

            # Вычисляем моменты
            M = cv2.moments(component_mask)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                # Центральные моменты второго порядка
                mu20 = M['mu20']
                mu02 = M['mu02']
                mu11 = M['mu11']

                # Угол ориентации главной оси (в радианах)
                theta_x = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)
                angle_deg_x = np.degrees(theta_x)  # если нужен в градусах
                angles_x.append(angle_deg_x)

                angle_from_y = np.pi / 2 - theta_x
                angle_from_y_deg = np.degrees(angle_from_y)
                angles_y.append(angle_from_y_deg)

                # Рисуем центр
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                # Рисуем линию, показывающую ориентацию (длина 50 пикселей)
                length = 50
                x2 = int(cx + length * np.cos(theta_x))
                y2 = int(cy - length * np.sin(angle_from_y))
                cv2.line(frame, (cx, cy), (x2, y2), (255, 0, 0), 2)

                # Можно также нарисовать контур всей компоненты для наглядности
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
        else:
            angles_x.append(0.0)
            angles_y.append(90.0)
    cv2.imshow('Detected Ellipses', frame)
    print(f"{angles_x[0]} {angles_y[0]}")
    
    # num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)

    # for i in range(1, num_labels):  
    #     area = stats[i, cv2.CC_STAT_AREA]
    #     if area > min_area:
    #         filtered_mask[labels == i] = 255

    # contours, _ = cv2.findContours(filtered_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # for c in contours:
    #     #print(cv2.contourArea(c))
    #     if cv2.contourArea(c) > 100000 and cv2.contourArea(c) < 350000:
    #         cv2.drawContours(frame, c, -1, (0, 255, 0), 3)
    #         center, img, fcon = filters.get_elipse_radius(frame, [c], draw=True)
    #         print(center)
    #         if len(center) > 0:
    #             angle = PCA.get_orientation_pca(cnt=c, center_coords=center, img_to_draw=img)
    #             print(angle)
    # cv2.imshow('Detected Ellipses', img)
    # contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # centers, img, fcon = filters.get_elipse_radius(frame, contours, draw=True)
    # angle = PCA.get_orientation_pca(cnt=contours[0], center_coords=centers[0], img_to_draw=frame)
    # print(angle)
    
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break
"""
video.release()
cv2.waitKey(0)
cv2.destroyAllWindows()
