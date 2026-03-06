from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time, math, threading, cv2, numpy as np
import PCA, exel
from image_actions import *
import through_circles

# Глобальные переменные
roll = 0.0
pitch = 0.0
yaw = 0.0
cv_roll = 0
cv_pitch = 0
msg = None
EXEL_FILE = "Poseydon_telemetry.xlsx"
running = True
dron = None
mesurent = 0

def telemetry_worker():
    global running, roll, pitch, yaw, dron, mesurent, msg
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
        except Exception as e:
            print(e)

        time.sleep(0.02)  # ~50 Гц


def camera_thread():
    """Камера независимо"""
    global running, cv_roll, cv_pitch
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

        anglex, angley, getback = through_circles.get_pitch_roll(frame=frame, get_back=True)
        if len(anglex) > 0:
            cv_roll = anglex[0]
        if len(angley) > 0:
            cv_pitch = angley[0]
            
        cv2.imshow("contours", getback)
        if len(anglex) > 0 and len(angley) > 0:
            print(f"{anglex}, {angley}")

        key = cv2.waitKey(1)
        if key == 112:
            print("p pressed")
            exel.add_data_to_excel(EXEL_FILE, mesurent, roll, pitch, yaw, cv_roll, cv_pitch)

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
