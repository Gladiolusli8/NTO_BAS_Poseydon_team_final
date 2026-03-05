from pioneer_sdk import Pioneer
import time
import math

dron = Pioneer()

print("Connecting...")

time.sleep(1)

dron.connection.wait_heartbeat(timeout=1)
print("Connected")

dron.connection.mav.request_data_stream_send(
    1, 1, 30, 10, 1
)
while True:
    try:
        msg = dron.connection.recv_match(type='ATTITUDE', blocking=True, timeout=1)
        if msg is None:
            continue

        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)

        print(f"Крен: {roll:.2f}° | Тангаж: {pitch:.2f}° | Рысканье: {yaw:.2f}°")
    except KeyboardInterrupt:
        print("\nОстановка программы.")
        break

