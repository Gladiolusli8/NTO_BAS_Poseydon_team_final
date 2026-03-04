from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time
import math

print("Подключение к Pioneer...")

try:
    # Явно указываем правильный UDP-адрес
    drone = Pioneer(connection_method='udp:192.168.4.1:14550')

    drone.connection.wait_heartbeat(timeout=15)
    print("✅ Heartbeat получен. Соединение установлено.")

except Exception as e:
    print("❌ Не удалось подключиться к дрону.")
    print("Проверь Wi-Fi подключение к Pioneer.")
    print("Ошибка:", e)
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
        distance = drone.get_dist_sensor_data()
        battery_voltage = drone.get_battery_status()

        msg = drone.connection.recv_match(type='ATTITUDE', blocking=False)

        if distance is not None:
            print(f"Дальномер: {distance}")

        if battery_voltage is not None:
            print(f"Батарея: {battery_voltage} В")

        if msg:
            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = math.degrees(msg.yaw)

            print(f"Крен: {roll:.2f}° | "
                  f"Тангаж: {pitch:.2f}° | "
                  f"Рысканье: {yaw:.2f}°")

        print("-" * 40)

        time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nОстановка программы.")
        break

    except Exception as e:
        print("Ошибка в цикле:", e)
        time.sleep(1)