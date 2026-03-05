from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time, math, threading, cv2, numpy as np
import PCA, exel
from image_actions import *

# Глобальные переменные
roll = 0.0
pitch = 0.0
yaw = 0.0
EXEL_FILE = "Poseydon_telemetry.xlsx"
running = True
dron = None
mesurent = 0

def telemetry_worker():
    global running, roll, pitch, yaw, dron, mesurent
    mesurent +=1
    while running:
        if not dron:
            time.sleep(0.1)
            continue

        try:
            msg = dron.connection.recv_match(type='ATTITUDE', blocking=False)
            if msg:
                roll = math.degrees(msg.roll)
                pitch = math.degrees(msg.pitch)
                yaw = math.degrees(msg.yaw)
                print(f" {roll:6.1f}° | {pitch:6.1f}° | {yaw:6.1f}°")

                exel.add_data_to_excel(EXEL_FILE, mesurent, roll, pitch, yaw, 0, 0)

        except Exception as e:
            print(e)

        time.sleep(0.02)  # ~50 Гц


def camera_thread():
    """Камера независимо"""
    global running
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print()
        return

    cv2.namedWindow("raw frame", cv2.WINDOW_NORMAL)
    cv2.namedWindow("contours", cv2.WINDOW_NORMAL)

    while running:
        ret, frame = cap.read()
        if not ret: continue

        cv2.imshow("raw frame", frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            if 100 <= cv2.contourArea(c) <= 100000:
                cv2.drawContours(frame, [c], -1, (0, 0, 255), 2)
                angle = PCA.get_angle_pca(image_path=None, img=frame)
                print(f"Угол PCA: {angle}")
                PCA.draw_main_axis(frame, c)
                break

        cv2.imshow("contours", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

    cap.release()


if __name__ == "__main__":
    print()
    dron = Pioneer()
    time.sleep(2)

    try:
        dron.connection.wait_heartbeat(timeout=3)
        print("подключились")
    except:
        print("не подключились")

    try:
        dron.connection.mav.command_long_send(
            1, 1,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 50000, 0, 0, 0, 0, 0
        )
        print()
    except:
        print()

    threading.Thread(target=telemetry_worker, daemon=True).start()
    threading.Thread(target=camera_thread, daemon=True).start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("остановились")
        running = False
        cv2.destroyAllWindows()
