import cv2
import numpy as np
from pioneer_sdk import Pioneer, Camera
import detect__aruco
import threading
import time
import lines

dron = Pioneer()

center_x, center_y = None, None
b_min = np.array([0, 0, 106])
b_max = np.array([180, 255, 255])  

test = cv2.imread("image.png")

def move_to_center(center_x, center_y, drone):
    cur_x, cur_y, z = dron.get_local_position_lps(True)
    dx = center_x - cur_x
    dy = center_y - cur_y

    k_p = 0.5

    vx = dx * k_p
    vy = dy * k_p

    max_speed = 2.0
    if (dx >=30):
        vx = dx * k_p
        vx = max(-max_speed, min(max_speed, vx))
    if (dy >= 30):
        vy = dy * k_p
        vy = max(-max_speed, min(max_speed, vy))
    if (dx < 30 and dy < 30):
        vy = 0
        vx = 0

    drone.set_manual_speed(vx, vy, 0, 0)

set_target = False
find_line = False
go_to_line = False
target = (0, 2.5, 1.5)
cv_target = None

def camera_thread():
    global set_target, cv_target
    camera = Camera()
    camera.connect()
    
    while True:
        img = test
        cv2.imshow("img", img)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, b_min, b_max)
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(mask, kernel, iterations=2)
        eroded_mask = cv2.erode(dilated_mask, kernel, iterations=1)
        
        # Получаем изображение только с линиями
        lines_img = lines.clean_and_isolate_lines(eroded_mask)
        cv2.imshow("clean", lines_img)
        
        # Ищем контуры на инвертированном изображении
        # Так как линии черные на белом фоне, инвертируем для поиска контуров
        inverted_lines = cv2.bitwise_not(lines_img)
        contours, _ = cv2.findContours(inverted_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Копируем оригинальное изображение для отрисовки результатов
        img_with_contours = img.copy()
        centers = []
        
        for c in contours:
            perimeter = cv2.arcLength(c, True)

            if perimeter > 100: 
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                box = box.astype(int)
                center = (int(rect[0][0]), int(rect[0][1]))
                cv2.drawContours(img_with_contours, [box], 0, (0, 255, 0), 3)
                cv2.circle(img_with_contours, center, 10, (0, 0, 255), -1)
                print(f"Найден объект. Центр: X={center[0]}, Y={center[1]}")
                centers.append(center)
        """
        if len(centers) > 0:
            if cv_target is not None:
                set_target = False
                cv_target = (centers[0][0], centers[0][0], centers[0][2])
            dron.go_to_local_point(0, 2.5, 1.5)
            dron.go_to_local_point(target[0], target[1], target[2], 0)


            dron.go_to_local_point(yaw=0)
            dron.go_to_local_point(0, 0, 1.5)


            dron.go_to_local_point(yaw=0)
            dron.go_to_local_point(0, 1.25, 1.5)
        """

        cv2.imshow("lines with contours", img_with_contours)
        cv2.waitKey(0)
        break  

    #camera.disconnect()

if __name__ == "__main__":
    cam_thread = threading.Thread(target=camera_thread)
    cam_thread.start()

    dron.arm()
    dron.go_to_local_point(0, 0, 1.5)
    dron.go_to_local_point(0, 2.5, 1.5)
    time.sleep(3)
    set_target = True

    while set_target == True:
        time.sleep(0.1)
    #time.sleep(1)
    if cv_target is not None: 
        dron.go_to_local_point(yaw=0)
        set_target = True
        while not dron.point_reached:
            time.sleep(0.1)
        dron.go_to_local_point(0, 0, 1.5)
        while not dron.point_reached:
            time.sleep(0.1)

    
    while set_target == True:
        time.sleep(0.1)

    dron.go_to_local_point(0, 2.5, 1.5)
    set_target = True

    while set_target == True:
        time.sleep(0.1)
    #time.sleep(1)
    if cv_target is not None: 
        dron.go_to_local_point(yaw=0)
        set_target = True
        while not dron.point_reached:
            time.sleep(0.1)
        dron.go_to_local_point(0, 1.25, 1.5)
        while not dron.point_reached:
            time.sleep(0.1)
    
    while not dron.point_reached:
        time.sleep(0.1)    
    dron.land()
    dron.disarm()

    # dron.go_to_local_point(yaw=0)
    # dron.go_to_local_point(0, 1.25, 1.5)