from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time
import math

# Подключение
drone = Pioneer()
drone.connection.wait_heartbeat(timeout=10)

# Запрос ATTITUDE 10 Гц (100000 мкс)
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
    100000,   # 10 Гц
    0, 0, 0, 0, 0
)

while True:

    # Дальномер
    distance = drone.get_dist_sensor_data()

    # Батарея
    battery = drone.get_battery_status()

    # ATTITUDE (неблокирующее чтение!)
    msg = drone.connection.recv_match(
        type='ATTITUDE',
        blocking=False
    )

    if distance is not None:
        print(f"Distance: {distance}")

    if battery is not None:
        print(f"Battery: {battery}")

    if msg:
        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)

        print(f"Roll: {roll:.2f}° | "
              f"Pitch: {pitch:.2f}° | "
              f"Yaw: {yaw:.2f}°")

    time.sleep(0.1)