#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Poseydon Autonomous Flight Mission
Схема: старт -> вперед 2.7м -> назад 2.7м -> вперед 2.7м -> назад 1.35м -> посадка
Высота: 1 метр
Поворотов нет, летим задом когда нужно назад
Коррекция по черным линиям (удержание между ними) и синему кресту (точная посадка)
"""

from pioneer_sdk import Pioneer
from pymavlink import mavutil
import threading
import time
import math
import cv2
import numpy as np

# ====================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ======================
roll = 0.0
pitch = 0.0
yaw = 0.0
running = True
dron = None
mission_phase = 0  # 0:взлет, 1:вперед к m1, 2:назад к m3, 3:вперед к m1, 4:назад к m2, 5:посадка

# Для измерения ветра (на этапе назад к m3)
wind_speed_result = 0.0
max_roll_during_wind = 0.0
wind_measuring_active = False

# Для vision (черные линии и синий крест)
frame_width = 640
frame_height = 480
line_detected = False
line_offset = 0.0           # отклонение центра между линиями от центра кадра (пиксели)
target_visible = False      # виден ли синий крест
target_x = 0.0              # центр креста по x (пиксели)
target_y = 0.0              # центр креста по y
target_area = 0.0           # площадь креста (для оценки расстояния)

# События для синхронизации (опционально)
# lock = threading.Lock()

# ====================== ПОТОК ТЕЛЕМЕТРИИ ======================
def telemetry_worker():
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
        time.sleep(0.02)

# ====================== ПОТОК VISION (ЧЕРНЫЕ ЛИНИИ И СИНИЙ КРЕСТ) ======================
def vision_worker():
    global running, line_detected, line_offset, target_visible, target_x, target_y, target_area, frame_width, frame_height
    print("[VISION] Поток vision запущен")
    # Подключение к камере (пример, может отличаться)
    cap = cv2.VideoCapture(0)  # или использовать pioneer_sdk.Camera()
    if not cap.isOpened():
        print("[VISION] Не удалось открыть камеру")
        return

    # Установка разрешения (если поддерживается)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    while running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        # Обновляем реальные размеры кадра (на случай изменения)
        frame_height, frame_width = frame.shape[:2]

        # ---- Детекция черных линий ----
        # Конвертируем в grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Бинаризация: черное на белом (инвертируем, чтобы линии были белыми)
        _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        # Морфология для удаления шума
        kernel = np.ones((3,3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        # Поиск контуров
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Отбираем контуры, которые могут быть линиями (большая площадь, вытянутая форма)
        line_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:  # отсекаем мелкий мусор
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / h if h != 0 else 0
            # Линии обычно длинные и горизонтальные (или вертикальные) – здесь уточнить ориентацию
            # Предположим, линии горизонтальные (ширина много больше высоты)
            if aspect_ratio > 3 and w > 100:
                line_contours.append(cnt)

        if len(line_contours) >= 2:
            # Сортируем контуры по положению центра по x
            centers_x = []
            for cnt in line_contours:
                M = cv2.moments(cnt)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    centers_x.append(cx)
            centers_x.sort()
            # Берём два крайних как левую и правую линии
            left_line = centers_x[0]
            right_line = centers_x[-1]
            # Центр между ними
            line_center = (left_line + right_line) / 2
            # Отклонение от центра кадра
            frame_center_x = frame_width / 2
            line_offset = line_center - frame_center_x
            line_detected = True
        else:
            line_detected = False
            line_offset = 0.0

        # ---- Детекция синего креста ----
        # Конвертируем в HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Диапазон синего цвета (нужно подобрать под условия)
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        # Морфология
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)
        # Поиск контуров синего
        contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Ищем контур креста (по форме, площади и т.п.)
        target_found = False
        for cnt in contours_blue:
            area = cv2.contourArea(cnt)
            if area < 100:  # слишком маленький
                continue
            # Аппроксимируем контур
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            # Крест обычно имеет много углов, но мы можем использовать bounding rect
            x, y, w, h = cv2.boundingRect(cnt)
            # Проверяем соотношение сторон (не слишком вытянутый)
            if 0.5 < w/h < 2.0 and area > 300:
                # Считаем центр
                M = cv2.moments(cnt)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    target_x = cx
                    target_y = cy
                    target_area = area
                    target_visible = True
                    target_found = True
                    break
        if not target_found:
            target_visible = False

        # Для отладки можно показывать кадры (раскомментировать при необходимости)
        # cv2.imshow("Lines", cleaned)
        # cv2.imshow("Blue", mask_blue)
        # if cv2.waitKey(1) == 27: break

        time.sleep(0.03)  # ~30 fps

    cap.release()
    cv2.destroyAllWindows()
    print("[VISION] Поток завершён")

# ====================== ФУНКЦИИ КОРРЕКЦИИ ======================
def get_line_correction():
    """Коррекция по черным линиям (удержание между ними)"""
    global line_detected, line_offset, frame_width
    if not line_detected:
        return 0.0, 0.0
    frame_center_x = frame_width / 2
    # Преобразуем отклонение в пикселях в скорость (коэффициенты подбираются)
    # Нормируем отклонение к [-1..1]
    norm_offset = line_offset / frame_center_x
    vy = norm_offset * 0.3          # движение вбок
    yaw_rate = norm_offset * 0.2     # поворот
    # Ограничиваем
    vy = max(min(vy, 0.8), -0.8)
    yaw_rate = max(min(yaw_rate, 0.5), -0.5)
    return vy, yaw_rate

def get_target_correction():
    """Коррекция по синему кресту (точное наведение при посадке)"""
    global target_visible, target_x, target_y, frame_width, frame_height
    if not target_visible:
        return 0.0, 0.0
    frame_center_x = frame_width / 2
    frame_center_y = frame_height / 2
    dx = (target_x - frame_center_x) / frame_center_x
    dy = (target_y - frame_center_y) / frame_center_y
    vy = dx * 0.2
    yaw_rate = dx * 0.15
    # dy можно использовать для коррекции высоты или скорости вперёд, пока не используем
    vy = max(min(vy, 0.5), -0.5)
    yaw_rate = max(min(yaw_rate, 0.3), -0.3)
    return vy, yaw_rate

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
        # Коэффициент 0.3 эмпирический, подбирается
        wind_speed_result = max_roll_during_wind * 0.3
        print("[WIND] ИЗМЕРЕНИЕ ЗАВЕРШЕНО")
        print(f"[WIND] Макс крен: {max_roll_during_wind:.2f}°, ветер: {wind_speed_result:.2f} м/с")

# ====================== ФУНКЦИИ ДВИЖЕНИЯ ======================
def move_forward(distance, target_yaw=0, wind_measure=False, use_vision=True):
    return _move_with_stabilization(distance, 1, target_yaw, wind_measure, use_vision)

def move_backward(distance, target_yaw=0, wind_measure=False, use_vision=True):
    return _move_with_stabilization(distance, -1, target_yaw, wind_measure, use_vision)

def _move_with_stabilization(distance, direction, target_yaw, wind_measure, use_vision):
    """
    direction: +1 вперед, -1 назад
    """
    print(f"[MOVE] {'ВПЕРЕД' if direction>0 else 'НАЗАД'} на {distance} м, курс {target_yaw}°")

    # ПИД-регуляторы для стабилизации углов
    roll_pid = PID(kp=0.8, ki=0.03, kd=0.1, setpoint=0)
    yaw_pid = PID(kp=2.0, ki=0.05, kd=0.2, setpoint=target_yaw)
    roll_pid.reset()
    yaw_pid.reset()

    # Получаем начальную позицию (если доступна)
    start_pos = dron.get_local_position_lps(get_last_received=True)
    if start_pos is None:
        print("[MOVE] Нет LPS, используем режим по времени")
        use_lps = False
        move_time = distance * 2.5  # 2.5 сек на метр (скорость 0.4 м/с)
        start_time = time.time()
    else:
        use_lps = True
        start_x, start_y, start_z = start_pos
        target_x = start_x + distance * direction
        print(f"[MOVE] Старт X: {start_x:.2f}, цель X: {target_x:.2f}")

    if wind_measure:
        start_wind_measurement()

    move_start_time = time.time()
    timeout = distance * 4 + 5
    target_reached = False

    while not target_reached and time.time() - move_start_time < timeout:
        # Определяем скорость по X
        if use_lps:
            current_pos = dron.get_local_position_lps(get_last_received=True)
            if current_pos:
                current_x, _, _ = current_pos
                remaining = abs(target_x - current_x)
                if remaining < 0.15:
                    target_reached = True
                    vx = 0
                else:
                    speed = max(0.2, min(0.5, remaining))
                    vx = speed * direction
            else:
                # Потеряли LPS, переходим в режим по времени
                vx = 0.4 * direction
        else:
            elapsed = time.time() - move_start_time
            if elapsed >= move_time:
                target_reached = True
                vx = 0
            else:
                vx = 0.4 * direction

        # Получаем углы
        current_roll = roll
        current_yaw = yaw

        # ПИД-коррекции углов
        roll_correction = roll_pid.compute(current_roll)
        yaw_correction = yaw_pid.compute(current_yaw)

        vy_base = roll_correction * 0.15
        yaw_rate_base = yaw_correction * 0.08

        # Коррекция по vision (линии или крест)
        vy_vision, yaw_rate_vision = 0.0, 0.0
        if use_vision:
            if mission_phase == 5:  # этап посадки - используем крест
                vy_vision, yaw_rate_vision = get_target_correction()
            else:
                vy_vision, yaw_rate_vision = get_line_correction()

        # Суммируем
        vy = vy_base + vy_vision
        yaw_rate = yaw_rate_base + yaw_rate_vision

        # Ограничения
        vy = max(min(vy, 0.8), -0.8)
        yaw_rate = max(min(yaw_rate, 0.5), -0.5)

        # Применяем управление
        dron.set_manual_speed_body_fixed(vx=vx, vy=vy, vz=0, yaw_rate=yaw_rate)

        # Статус
        if int(time.time() * 2) % 2 == 0:
            if use_lps and current_pos:
                print(f"[MOVE] X:{current_x:.2f} ост:{remaining:.2f} vx:{vx:.2f} vy:{vy:.2f} yaw_rate:{yaw_rate:.2f}")
            else:
                print(f"[MOVE] t:{time.time()-move_start_time:.1f} vx:{vx:.2f} vy:{vy:.2f}")

        time.sleep(0.05)

    # Останавливаем
    dron.set_manual_speed_body_fixed(vx=0, vy=0, vz=0, yaw_rate=0)
    time.sleep(0.5)

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

    print("\n" + "="*60)
    print(f"МИССИЯ {team}, попытка {attempt}")
    print("Схема: взлет(1м) -> вперед 2.7м -> назад 2.7м -> вперед 2.7м -> назад 1.35м -> посадка")
    print("="*60)

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

    # ЭТАП 1: ВПЕРЕД 2.7м (к первой линии)
    print("\n[3] ЭТАП 1: ВПЕРЕД 2.7м (к m1)")
    mission_phase = 1
    if not move_forward(2.7, target_yaw=0, wind_measure=False, use_vision=True):
        print("[ERROR] Этап 1 провален")
        return False
    time.sleep(1)

    # ЭТАП 2: НАЗАД 2.7м (к третьей линии) - ИЗМЕРЕНИЕ ВЕТРА
    print("\n[4] ЭТАП 2: НАЗАД 2.7м (к m3) - ИЗМЕРЕНИЕ ВЕТРА")
    mission_phase = 2
    if not move_backward(2.7, target_yaw=0, wind_measure=True, use_vision=True):
        print("[ERROR] Этап 2 провален")
        return False
    time.sleep(1)

    # ЭТАП 3: ВПЕРЕД 2.7м (к первой линии)
    print("\n[5] ЭТАП 3: ВПЕРЕД 2.7м (к m1)")
    mission_phase = 3
    if not move_forward(2.7, target_yaw=0, wind_measure=False, use_vision=True):
        print("[ERROR] Этап 3 провален")
        return False
    time.sleep(1)

    # ЭТАП 4: НАЗАД 1.35м (к центру, где синий крест)
    print("\n[6] ЭТАП 4: НАЗАД 1.35м (к центру m2) - подготовка к посадке")
    mission_phase = 4
    if not move_backward(1.35, target_yaw=0, wind_measure=False, use_vision=True):
        print("[ERROR] Этап 4 провален")
        return False
    time.sleep(1)

    # ЭТАП 5: ПОСАДКА с коррекцией по кресту
    print("\n[7] ПОСАДКА с наведением на синий крест")
    mission_phase = 5
    # Начинаем снижение, используя коррекцию по кресту
    landing_start = time.time()
    landing_timeout = 15
    while time.time() - landing_start < landing_timeout:
        # Получаем коррекцию по кресту
        vy, yaw_rate = get_target_correction()
        # Плавно снижаемся
        vz = 0.3  # скорость снижения
        dron.set_manual_speed_body_fixed(vx=0, vy=vy, vz=vz, yaw_rate=yaw_rate)
        time.sleep(0.05)
        # Можно проверять касание земли (по высоте или акселерометру), но пока просто таймер
    dron.set_manual_speed_body_fixed(vx=0, vy=0, vz=0, yaw_rate=0)
    dron.land()
    time.sleep(5)

    # РЕЗУЛЬТАТЫ
    print("\n" + "="*60)
    print("МИССИЯ ВЫПОЛНЕНА")
    print("="*60)
    print(f"Скорость ветра: {wind_speed_result:.2f} м/с")

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
    print("="*60)
    print("Poseydon - Полет с коррекцией по линиям и синему кресту")
    print("Высота 1м, схема: вперед-назад-вперед-назад(в центр)")
    print("="*60)

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
    threading.Thread(target=vision_worker, daemon=True).start()

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