from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time
import math
try:
    # Явно указываем правильный UDP-адрес
    drone = Pioneer()
    drone.connection.wait_heartbeat(timeout=15)

except Exception as e:
    print(e)
    exit()

# Запрашиваем поток ATTITUDE 10 Гц
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
    100000,  # 10 Гц
    0, 0, 0, 0, 0
)

print("Начинаем приём телеметрии...\n")

while True:
    try:
        a = int(input())
        if a == 1:
            msg = drone.connection.recv_match(type='ATTITUDE', blocking=False)

            if msg:
                roll = math.degrees(msg.roll)
                pitch = math.degrees(msg.pitch)
                yaw = math.degrees(msg.yaw)

                print(f"Крен: {roll:.2f}° | "
                      f"Тангаж: {pitch:.2f}° | "
                      f"Рысканье: {yaw:.2f}°")

            print("-" * 40)
        if a == 0:
            break

    except Exception as e:
        print(e)
        time.sleep(1)