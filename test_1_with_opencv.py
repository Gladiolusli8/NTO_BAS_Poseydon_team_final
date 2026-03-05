from pioneer_sdk import Pioneer
import time
import math
import threading
import cv2
import numpy as np
import PCA
import exel 
from image_actions import *

roll, pitch, yaw = None, None, None
cv2.namedWindow("raw frame")
cv2.namedWindow("contours")
EXEL_FILE = "Poseydon_telemetry.xlsx"

def get_tel(dron):
    msg = dron.connection.recv_match(type='ATTITUDE', blocking=True, timeout=0.5)
    if msg:
        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)

        print(f"Крен: {roll:.2f}°, Тангаж: {pitch:.2f}°, Рысканье: {yaw:.2f}°")
        return roll, pitch, yaw
    return None

def tel_thread(dron):
    while True:
        try:
            global roll, pitch, yaw
            roll, pitch, yaw = get_tel(dron=dron)
        except Exception as e:
            print(f"{e}")

def camera_thread():
    stream = cv2.VideoCapture(0)
    if not stream.isOpened():
        print("Unable to open camera")
        exit(0)

    while True:
        try:
            frame = stream.get_frame()
            if frame is not None:
                cv2.imshow("raw frame", frame)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, bw = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                contours, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                for i, c in enumerate(contours):
                    area = cv2.contourArea(c)
                    if area < 1e2 or 1e5 < area:
                        continue

                    cv2.drawContours(frame, contours, i, (0, 0, 255), 2)
                    angle = PCA.get_angle_pca(image_path=None, img=frame)
                    print(angle)
                    PCA.draw_main_axis(frame, c)
                    cv2.imshow("contours", frame)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"{e}")

if __name__ == "__main__":
    dron = Pioneer()
    print("Connecting...")
    time.sleep(1)
    dron.connection.wait_heartbeat(timeout=1)
    print("Connected")

    dron.connection.mav.request_data_stream_send(1, 1, 30, 5, 1)

    tel_thread = threading.Thread(target=tel_thread, args=(dron))
    cam_thread = threading.Thread(target=camera_thread)

    cam_thread.start()
    tel_thread.start()


    if roll is not None and pitch is not None and yaw is not None:
        exel.add_data_to_excel(EXEL_FILE, roll, pitch, yaw, 0, 0)

    cam_thread.join()
    tel_thread.join()