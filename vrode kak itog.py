from pioneer_sdk import Pioneer
from pymavlink import mavutil
import time
import math

# =========================
# Параметры PID и челнока
# =========================
Kp_pos = 1.2       # коэффициент по позиции X (pitch)
Kp_wind = 0.5      # коэффициент по боковой скорости (roll)
max_angle = 10     # ограничение углов в градусах
thrust = 0.6       # постоянная тяга для удержания высоты

ch_len = 2.5       # длина челнока в метрах
num_runs = 3       # количество челночных проходов

# =========================
# Подключение к дрону
# =========================
print("Подключение к Pioneer...")

try:
    drone = Pioneer(connection_method='udp:192.168.4.1:14550')
    drone.connection.wait_heartbeat(timeout=15)
    print("✅ Соединение установлено.")
except Exception as e:
    print("❌ Ошибка подключения:", e)
    exit()

# =========================
# Запрос потоков 50 Гц
# =========================
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
    20000, 0, 0, 0, 0, 0
)
drone.connection.mav.command_long_send(
    drone.connection.target_system,
    drone.connection.target_component,
    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
    0,
    mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
    20000, 0, 0, 0, 0, 0
)

print("📡 Начало челночного полёта с PID...\n")

# =========================
# Инициализация переменных
# =========================
lps_initialized = False
start_x = 0
target_x = 0
direction = 1  # 1 = вперед, -1 = назад
run_count = 0

# =========================
# Основной цикл
# =========================
try:
    while run_count < num_runs:
        msg = drone.connection.recv_match(blocking=False)
        if not msg:
            time.sleep(0.01)
            continue

        # --- Получаем координаты и скорость ---
        if msg.get_type() == "LOCAL_POSITION_NED":
            x = msg.x
            y = msg.y
            z = msg.z
            vx = msg.vx
            vy = msg.vy
            vz = msg.vz

            if not lps_initialized:
                start_x = x
                target_x = start_x + ch_len
                lps_initialized = True
                print(f"Стартовая точка: X={start_x:.2f}")
                print(f"Первая цель: X={target_x:.2f}")

            # --- PID по позиции X (челночное движение) ---
            error_x = target_x - x
            pitch_cmd = Kp_pos * error_x
            pitch_cmd = max(min(pitch_cmd, max_angle), -max_angle)

            # --- PID по боковой скорости Y (компенсация ветра) ---
            error_y_speed = -vy
            roll_cmd = Kp_wind * error_y_speed
            roll_cmd = max(min(roll_cmd, max_angle), -max_angle)

            # --- Отправка команд на дрон ---
            drone.set_attitude(pitch=pitch_cmd, roll=roll_cmd, yaw=0, thrust=thrust)

            # --- Вывод телеметрии ---
            speed = math.sqrt(vx**2 + vy**2 + vz**2)
            print(f"X={x:.2f}, Y={y:.2f}, Z={z:.2f} | vx={vx:.2f}, vy={vy:.2f}, vz={vz:.2f} | speed={speed:.2f}")
            print(f"Pitch_cmd={pitch_cmd:.2f} | Roll_cmd={roll_cmd:.2f}")
            print("-"*60)

            # --- Проверка достижения цели ---
            if direction == 1 and x >= target_x - 0.05:  # достигли вперед
                target_x = start_x  # летим назад
                direction = -1
                run_count += 0.5  # один проход половина
                print(f"Достигли конца челнока → меняем направление назад")
            elif direction == -1 and x <= target_x + 0.05:  # достигли назад
                target_x = start_x + ch_len  # летим вперёд
                direction = 1
                run_count += 0.5
                print(f"Достигли начала челнока → меняем направление вперед")

        # --- Телеметрия углов ---
        if msg.get_type() == "ATTITUDE":
            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = math.degrees(msg.yaw)
            print(f"Крен={roll:.2f}° | Тангаж={pitch:.2f}° | Рысканье={yaw:.2f}°")

        time.sleep(0.02)  # 50 Гц

except KeyboardInterrupt:
    print("\nОстановка программы вручную.")

finally:
    print("Программа завершена. Дрон удерживает последний режим.")