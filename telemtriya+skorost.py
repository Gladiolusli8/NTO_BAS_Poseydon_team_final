from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time
import math

print("Подключение к Pioneer...")

try:
    drone = Pioneer(connection_method='udp:192.168.4.1:14550')
    drone.connection.wait_heartbeat(timeout=15)
    print("✅ Соединение установлено.")
except Exception as e:
    print("❌ Ошибка подключения:", e)
    exit()

# ===============================
# Запрос потоков 50 Гц
# ===============================

# ATTITUDE
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
    20000,  # 50 Гц
    0, 0, 0, 0, 0
)

# LOCAL_POSITION_NED (там есть скорость)
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
    20000,  # 50 Гц
    0, 0, 0, 0, 0
)

print("📡 Приём телеметрии и скорости...\n")

while True:
    try:
        msg = drone.connection.recv_match(blocking=False)

        if not msg:
            time.sleep(0.01)
            continue

        # -------- УГЛЫ --------
        if msg.get_type() == "ATTITUDE":
            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = math.degrees(msg.yaw)

            print(f"Крен: {roll:.2f}° | "
                  f"Тангаж: {pitch:.2f}° | "
                  f"Рысканье: {yaw:.2f}°")

        # -------- СКОРОСТЬ --------
        if msg.get_type() == "LOCAL_POSITION_NED":
            vx = msg.vx
            vy = msg.vy
            vz = msg.vz

            speed = math.sqrt(vx**2 + vy**2 + vz**2)

            print(f"Скорость X: {vx:.2f} м/с | "
                  f"Y: {vy:.2f} м/с | "
                  f"Z: {vz:.2f} м/с")

            print(f"Общая скорость: {speed:.2f} м/с")

        print("-" * 50)

        time.sleep(0.02)  # 50 Гц

    except KeyboardInterrupt:
        print("\nОстановка.")
        break

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(1)