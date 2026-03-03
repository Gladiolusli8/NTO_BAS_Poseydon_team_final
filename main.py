from pioneer_sdk import Pioneer
import time
import math
dron = Pioneer()
while True:
    array_of_coordinates = dron.get_local_position_lps() # koordy
    distance = dron.get_dist_sensor_data() # dalnomer
    battery_voltage = dron.get_battery_status() # zaryd
    attitude = dron.get_attitude()
    if array_of_coordinates: # ne pusto
        print(f'x={array_of_coordinates[0]} , y={array_of_coordinates[1]}, z={array_of_coordinates[2]}')
    if distance: # ne pusto
        print(f'distance={distance}')
    if battery_voltage: # ne pusto
        print(f'battery_voltage={battery_voltage}')
    if attitude:
        print(f'attitude={attitude}')
    # Проверяем, что данные получены (не None)
    if attitude is not None:
        # Преобразуем радианы в градусы для удобства восприятия
        roll_deg = math.degrees(attitude[0])
        pitch_deg = math.degrees(attitude[1])
        yaw_deg = math.degrees(attitude[2])

        # Выводим значения в консоль
        print(f'Крен: {roll_deg:.2f}°, Тангаж: {pitch_deg:.2f}°, Рысканье: {yaw_deg:.2f}°')
    time.sleep(2)