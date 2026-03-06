#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Poseydon Autonomous Flight Mission
Схема: старт -> вперед 2.7м (m1) -> назад 2.7м (m3) -> вперед 2.7м (m1) -> назад 1.35м (m2) -> посадка
Высота: 1 метр
Поворотов нет, летим задом когда нужно назад
Коррекция по ArUco меткам для ровности
"""

from pioneer_sdk import Pioneer
from pymavlink import mavutil
import threading
import time
import math
import os

# ====================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ======================
roll = 0.0
pitch = 0.0
yaw = 0.0
running = True
dron = None
mission_phase = 0  # 0:взлет, 1:вперед к m1, 2:назад к m3, 3:вперед к m1, 4:назад к m2, 5:посадка

# Для измерения ветра (на этапе вперед к m3)
wind_speed_result = 0.0
max_roll_during_wind = 0.0
wind_measuring_active = False

# Для ArUco коррекции (значения будут обновляться из потока камеры)
aruco_visible = False
aruco_x_center = 0  # положение метки по X в пикселях
aruco_id = -1
aruco_distance = 0  # расстояние до метки в метрах


# ====================== ПОТОК ТЕЛЕМЕТРИИ ======================
def telemetry_worker():
    """Получение углов дрона в отдельном потоке"""
    global running, roll, pitch, yaw, dron, max_roll_during_wind, wind_measuring_active

    print("[TELEMETRY] Поток телеметрии запущен")

    while running:
        if not dron:
            time.sleep(0.1)
            continue

        try:
            msg = dron.connection.recv_match(type='ATTITUDE', blocking=False)
            if msg:
                current_roll = math.degrees(msg.roll)
                current_pitch = math.degrees(msg.pitch)
                current_yaw = math.degrees(msg.yaw)

                roll = current_roll
                pitch = current_pitch
                yaw = current_yaw

                if wind_measuring_active:
                    abs_roll = abs(current_roll)
                    if abs_roll > max_roll_during_wind:
                        max_roll_during_wind = abs_roll

        except Exception as e:
            print(f"[TELEMETRY] Ошибка: {e}")

        time.sleep(0.02)  # 50 Гц


# ====================== ПОТОК ARUCO (ЗАГЛУШКА) ======================
def aruco_worker():
    """
    ЗАГЛУШКА: здесь будет код для работы с камерой и ArUco
    Реальная реализация будет добавлена позже
    """
    global running, aruco_visible, aruco_x_center, aruco_id, aruco_distance

    print("[ARUCO] Поток ArUco запущен (ЗАГЛУШКА)")

    while running:
        # Здесь будет реальный код детекции ArUco
        # Пока просто заглушка
        time.sleep(0.1)


# ====================== ПИД-РЕГУЛЯТОР ======================
class PID:
    def __init__(self, kp, ki, kd, setpoint=0, output_limits=(-2.0, 2.0), integral_limit=5):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.integral_limit = integral_limit

        self.prev_error = 0
        self.integral = 0
        self.last_time = None

    def compute(self, current_value):
        error = self.setpoint - current_value

        current_time = time.time()

        if self.last_time is not None:
            dt = current_time - self.last_time
            if dt > 0 and dt < 0.1:
                self.integral += error * dt
                self.integral = max(min(self.integral, self.integral_limit), -self.integral_limit)
                derivative = (error - self.prev_error) / dt
            else:
                derivative = 0
        else:
            dt = 0
            derivative = 0

        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        output = max(min(output, self.output_limits[1]), self.output_limits[0])

        self.prev_error = error
        self.last_time = current_time

        return output

    def reset(self):
        self.integral = 0
        self.prev_error = 0


# ====================== ФУНКЦИИ УПРАВЛЕНИЯ ВЕТРОМ ======================
def start_wind_measurement():
    global wind_measuring_active, max_roll_during_wind
    wind_measuring_active = True
    max_roll_during_wind = 0
    print("[WIND] НАЧАЛО ИЗМЕРЕНИЯ ВЕТРА")


def stop_wind_measurement():
    global wind_measuring_active, max_roll_during_wind, wind_speed_result

    if wind_measuring_active:
        wind_measuring_active = False
        # Коэффициент 0.3 нужно подобрать экспериментально
        wind_speed_result = max_roll_during_wind * 0.3
        print("[WIND] ИЗМЕРЕНИЕ ЗАВЕРШЕНО")
        print(f"[WIND] Макс крен: {max_roll_during_wind:.2f}°, ветер: {wind_speed_result:.2f} м/с")


# ====================== ФУНКЦИЯ КОРРЕКЦИИ ПО ARUCO ======================
def get_aruco_correction():
    """
    Получение корректировки по ArUco метке
    Возвращает (correction_y, correction_yaw)
    """
    global aruco_visible, aruco_x_center, aruco_id, frame_width

    if not aruco_visible:
        return 0.0, 0.0

    # Предполагаем ширину кадра 640 пикселей
    frame_center = 320

    # Отклонение метки от центра (в пикселях)
    deviation = aruco_x_center - frame_center

    # Преобразуем в корректировку движения
    # Чем дальше метка от центра, тем сильнее корректируем
    correction_y = deviation / frame_center * 0.3  # максимум 0.3 м/с
    correction_yaw = deviation / frame_center * 0.2  # максимум 0.2 рад/с

    # Ограничиваем
    correction_y = max(min(correction_y, 0.5), -0.5)
    correction_yaw = max(min(correction_yaw, 0.3), -0.3)

    return correction_y, correction_yaw


# ====================== ФУНКЦИИ ДВИЖЕНИЯ ======================
def move_forward(distance, target_yaw=0, wind_measure=False, use_aruco=True):
    """
    Движение вперед на distance метров
    """
    global dron, roll, yaw, mission_phase

    direction = 1  # +1 вперед
    return _move_with_stabilization(distance, direction, target_yaw, wind_measure, use_aruco)


def move_backward(distance, target_yaw=0, wind_measure=False, use_aruco=True):
    """
    Движение назад на distance метров (дрон не разворачивается)
    """
    global dron, roll, yaw, mission_phase

    direction = -1  # -1 назад
    return _move_with_stabilization(distance, direction, target_yaw, wind_measure, use_aruco)


def _move_with_stabilization(distance, direction, target_yaw, wind_measure, use_aruco):
    """
    Внутренняя функция движения со стабилизацией
    direction: +1 вперед, -1 назад
    """
    print(f"[MOVE] {'ВПЕРЕД' if direction > 0 else 'НАЗАД'} на {distance} м, курс {target_yaw}°")

    # ПИД-регуляторы
    roll_pid = PID(kp=0.8, ki=0.03, kd=0.1, setpoint=0)
    yaw_pid = PID(kp=2.0, ki=0.05, kd=0.2, setpoint=target_yaw)

    roll_pid.reset()
    yaw_pid.reset()

    # Получаем начальную позицию
    start_pos = dron.get_local_position_lps(get_last_received=True)
    if start_pos is None:
        print("[MOVE] Нет позиции LPS, продолжаем по времени")
        use_lps = False
        move_time = distance * 2.5  # 2.5 сек на метр (скорость 0.4 м/с)
        start_time = time.time()
    else:
        use_lps = True
        start_x, start_y, start_z = start_pos
        target_x = start_x + distance * direction
        print(f"[MOVE] Старт X: {start_x:.2f}, цель X: {target_x:.2f}")

    # Запускаем измерение ветра
    if wind_measure:
        start_wind_measurement()

    # Движение
    move_start_time = time.time()
    timeout = distance * 4 + 5
    target_reached = False

    # Основной цикл движения
    while not target_reached and time.time() - move_start_time < timeout:
        # Определяем скорость
        if use_lps:
            current_pos = dron.get_local_position_lps(get_last_received=True)
            if current_pos:
                current_x, _, _ = current_pos
                remaining = abs(target_x - current_x)

                if remaining < 0.15:
                    target_reached = True
                    vx = 0
                else:
                    # Скорость пропорциональна оставшемуся расстоянию
                    speed = max(0.2, min(0.5, remaining))
                    vx = speed * direction
            else:
                # Если потеряли LPS, переходим в режим по времени
                vx = 0.4 * direction
        else:
            # Режим по времени
            elapsed = time.time() - move_start_time
            if elapsed >= move_time:
                target_reached = True
                vx = 0
            else:
                vx = 0.4 * direction

        # Получаем углы
        current_roll = roll
        current_yaw = yaw

        # ПИД-коррекции
        roll_correction = roll_pid.compute(current_roll)
        yaw_correction = yaw_pid.compute(current_yaw)

        # Базовая коррекция от ПИД
        vy_base = roll_correction * 0.15
        yaw_rate_base = yaw_correction * 0.08

        # ArUco коррекция
        vy_aruco, yaw_rate_aruco = 0, 0
        if use_aruco:
            vy_aruco, yaw_rate_aruco = get_aruco_correction()

        # Суммируем коррекции
        vy = vy_base + vy_aruco
        yaw_rate = yaw_rate_base + yaw_rate_aruco

        # Ограничиваем
        vy = max(min(vy, 0.8), -0.8)
        yaw_rate = max(min(yaw_rate, 0.5), -0.5)

        # Применяем управление
        dron.set_manual_speed_body_fixed(vx=vx, vy=vy, vz=0, yaw_rate=yaw_rate)

        # Статус каждые 0.5 сек
        if int(time.time() * 2) % 2 == 0:
            if use_lps and current_pos:
                print(f"[MOVE] X:{current_x:.2f} ост:{remaining:.2f} vx:{vx:.2f} vy:{vy:.2f} yaw_rate:{yaw_rate:.2f}")
            else:
                print(f"[MOVE] t:{time.time() - move_start_time:.1f} vx:{vx:.2f} vy:{vy:.2f}")

        time.sleep(0.05)

    # Останавливаемся
    dron.set_manual_speed_body_fixed(vx=0, vy=0, vz=0, yaw_rate=0)
    time.sleep(0.5)

    # Останавливаем измерение ветра
    if wind_measure:
        stop_wind_measurement()

    if target_reached:
        print(f"[MOVE] Цель достигнута")
        return True
    else:
        print(f"[MOVE] Таймаут!")
        return False


# ====================== ФУНКЦИИ МИССИИ ======================
def wait_for_connection(timeout=30):
    print("[INIT] Ожидание подключения...")
    start = time.time()
    while time.time() - start < timeout:
        if dron and dron.connected():
            print("[INIT] Подключено")
            return True
        time.sleep(1)
    print("[INIT] Не подключилось")
    return False


def execute_mission(attempt=1):
    global dron, mission_phase, wind_speed_result

    team = "Poseydon"

    print("\n" + "=" * 60)
    print(f"МИССИЯ {team}, попытка {attempt}")
    print("Схема: взлет(1м) -> вперед 2.7м -> назад 2.7м -> вперед 2.7м -> назад 1.35м -> посадка")
    print("=" * 60)

    # Подключение
    if not wait_for_connection():
        return False
    time.sleep(2)

    # ARM
    print("\n[1] АРМ")
    mission_phase = 0
    if not dron.arm():
        print("[ERROR] Арм не удался")
        return False
    print("[OK] Арм успешен")
    time.sleep(2)

    # TAKEOFF на 1 метр
    print("\n[2] ВЗЛЕТ НА 1м")
    dron.takeoff()
    time.sleep(3)
    dron.go_to_local_point(x=0, y=0, z=1.0, yaw=0)

    timeout = time.time() + 10
    while not dron.point_reached() and time.time() < timeout:
        time.sleep(0.1)
    print("[OK] Высота 1м достигнута")
    time.sleep(1)

    # ЭТАП 1: ВПЕРЕД 2.7м (к m1)
    print("\n[3] ЭТАП 1: ВПЕРЕД 2.7м (к m1)")
    mission_phase = 1
    if not move_forward(2.7, target_yaw=0, wind_measure=False, use_aruco=True):
        print("[ERROR] Этап 1 провален")
        return False
    time.sleep(1)

    # ЭТАП 2: НАЗАД 2.7м (к m3) - ЗДЕСЬ ВЕТЕР
    print("\n[4] ЭТАП 2: НАЗАД 2.7м (к m3) - ИЗМЕРЕНИЕ ВЕТРА")
    mission_phase = 2
    if not move_backward(2.7, target_yaw=0, wind_measure=True, use_aruco=True):
        print("[ERROR] Этап 2 провален")
        return False
    time.sleep(1)

    # ЭТАП 3: ВПЕРЕД 2.7м (к m1)
    print("\n[5] ЭТАП 3: ВПЕРЕД 2.7м (к m1)")
    mission_phase = 3
    if not move_forward(2.7, target_yaw=0, wind_measure=False, use_aruco=True):
        print("[ERROR] Этап 3 провален")
        return False
    time.sleep(1)

    # ЭТАП 4: НАЗАД 1.35м (к m2 - центр)
    print("\n[6] ЭТАП 4: НАЗАД 1.35м (к центру m2)")
    mission_phase = 4
    if not move_backward(1.35, target_yaw=0, wind_measure=False, use_aruco=True):
        print("[ERROR] Этап 4 провален")
        return False
    time.sleep(1)

    # ПОСАДКА
    print("\n[7] ПОСАДКА")
    mission_phase = 5
    dron.land()
    time.sleep(5)

    # РЕЗУЛЬТАТЫ
    print("\n" + "=" * 60)
    print("МИССИЯ ВЫПОЛНЕНА")
    print("=" * 60)
    print(f"Скорость ветра: {wind_speed_result:.2f} м/с")

    # Сохраняем в файл
    filename = f"{team}_speed_{attempt}.txt"
    try:
        with open(filename, 'w') as f:
            f.write(f"Wind speed = {wind_speed_result:.2f} m/s\n")
            f.write(f"Max roll = {max_roll_during_wind:.2f} degrees\n")
        print(f"[SAVE] Результаты в {filename}")
    except Exception as e:
        print(f"[ERROR] Не сохранилось: {e}")

    return True


# ====================== ОСНОВНАЯ ПРОГРАММА ======================
if __name__ == "__main__":
    print("=" * 60)
    print("Poseydon - Бесповоротный полет с ArUco коррекцией")
    print("Высота 1м, схема: вперед-назад-вперед-назад(в центр)")
    print("=" * 60)

    attempt = 1  # можно менять

    # Подключение к дрону
    dron = Pioneer()

    # Настройка телеметрии
    try:
        dron.connection.wait_heartbeat(timeout=5)
        dron.connection.mav.command_long_send(
            1, 1, mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 20000, 0, 0, 0, 0, 0
        )
    except Exception as e:
        print(f"[INIT] Ошибка: {e}")

    # Потоки
    threading.Thread(target=telemetry_worker, daemon=True).start()
    threading.Thread(target=aruco_worker, daemon=True).start()

    time.sleep(2)

    # Миссия
    success = False
    try:
        success = execute_mission(attempt)
    except KeyboardInterrupt:
        print("\n[MAIN] Прервано")
    except Exception as e:
        print(f"\n[MAIN] Ошибка: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n[MAIN] Завершение...")
        running = False
        time.sleep(1)

        if dron and dron.connected() and mission_phase < 5:
            dron.land()
            time.sleep(3)

        if dron:
            dron.close_connection()

        print("[MAIN] Конец")

    exit(0 if success else 1)