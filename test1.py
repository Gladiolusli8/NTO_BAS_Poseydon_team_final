from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time
import math
try:
    drone = Pioneer()
    drone.connection.wait_heartbeat(timeout=15)

except Exception as e:
    print(e)
    exit()
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
    100000,  # 10 Гц
    0, 0, 0, 0, 0
)

while True:
    try:
        msg = drone.connection.recv_match(type='ATTITUDE', blocking=False)
        if msg:
            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = math.degrees(msg.yaw)
            print(f"Крен: {roll:.2f}° | ", f"Тангаж: {pitch:.2f}° | ", f"Рысканье: {yaw:.2f}°")
            print("-" * 40)
    except Exception as e:
        print(e)
        time.sleep(1)
    time.sleep(1)