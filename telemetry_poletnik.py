from pioneer_sdk import Pioneer
import time
import math
dron = Pioneer()
dron.connection.wait_heartbeat(timeout=10)# Запрашиваем поток ATTITUDE (сообщение с углами)
# 1 = система, 30 = MAVLINK_MSG_ID_ATTITUDE, 10 = 10 Гц, 1 = старт
dron.connection.mav.request_data_stream(1, 30, 10, 1)
while True:
    array_of_coordinates = dron.get_local_position_lps() # koordy
    distance = dron.get_dist_sensor_data() # dalnomer
    battery_voltage = dron.get_battery_status() # zaryad
    msg = dron.connection.recv_match(type='ATTITUDE', blocking=True, timeout=0.5)
    if array_of_coordinates: # ne pusto
        print(f'x={array_of_coordinates[0]} , y={array_of_coordinates[1]}, z={array_of_coordinates[2]}')
    if distance: # ne pusto
        print(f'distance={distance}')
    if battery_voltage: # not pusto
        print(f'battery_voltage={battery_voltage}')
    # Проверяем, что данные получены (не None)
    if msg:
        # MAVLink отдаёт углы в радианах — конвертируем в градусы
        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)
        print(f"Крен: {roll:.2f}°, Тангаж: {pitch:.2f}°, Рысканье: {yaw:.2f}°")
    time.sleep(2)