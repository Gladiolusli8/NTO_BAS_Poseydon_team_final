import math
import time
from pioneer_sdk import Pioneer

drone = Pioneer()
drone.connection.wait_heartbeat(timeout=1)

# параметры дрона
MASS = 0.23
AIR_DENSITY = 1.225
CD = 1.1
AREA = 0.03
G = 9.81

Q = 0.05   # шум процесса
R = 0.5

x = 0.0    # текущее состояние (скорость ветра)
P = 1.0    # дисперсия ошибки


def kalman_filter(z):
    global x, P

    # prediction
    x_pred = x
    P_pred = P + Q

    # update
    K = P_pred / (P_pred + R)
    x = x_pred + K * (z - x_pred)
    P = (1 - K) * P_pred

    return x


def estimate_wind_speed(roll, pitch):
    theta = math.sqrt(roll**2 + pitch**2)

    force = MASS * G * math.tan(theta)

    v = math.sqrt(abs((2 * force) / (AIR_DENSITY * CD * AREA)))

    return v

drone.connection.mav.request_data_stream_send(
    1, 1, 30, 10, 1
)
print("Измерение скорости ветра с фильтром Калмана")

while True:
    msg = drone.connection.recv_match(type='ATTITUDE', blocking=True, timeout=1)
    if msg is None:
        continue

    roll = msg.roll
    pitch = msg.pitch

    raw_wind = estimate_wind_speed(roll, pitch)

    filtered_wind = kalman_filter(raw_wind)

    print(
        f"Сырая скорость: {raw_wind:.2f} м/с | "
        f"Фильтр Калмана: {filtered_wind:.2f} м/с"
    )

    time.sleep(0.2)