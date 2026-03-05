from pioneer_sdk import Pioneer
import time
import math

dron = Pioneer()

print("Connecting...")

time.sleep(1)

dron.connection.wait_heartbeat(timeout=1)
print("Connected")

dron.connection.mav.request_data_stream_send(
    1, 1, 30, 5, 1
)

while True:

    # array_of_coordinates = dron.get_local_position_lps()
    # distance = dron.get_dist_sensor_data()

    msg = dron.connection.recv_match(type='ATTITUDE', blocking=True, timeout=0.5)

    # if array_of_coordinates:
    #     print(f'x={array_of_coordinates[0]}, y={array_of_coordinates[1]}, z={array_of_coordinates[2]}')
    #
    # if distance:
    #     print(f'distance={distance}')


    if msg:
        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)

        print(f"Крен: {roll:.2f}°, Тангаж: {pitch:.2f}°, Рысканье: {yaw:.2f}°")
        time.sleep(2)