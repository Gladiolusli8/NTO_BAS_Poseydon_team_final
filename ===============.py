from pioneer_sdk import Pioneer
import time, math, threading, cv2, numpy as np
import PCA, exel
from image_actions import *
from datetime import datetime

# Глобальные переменные
roll, pitch, yaw = 0, 0, 0
EXEL_FILE = "Poseydon_telemetry.xlsx"
running = True
dron = None


def get_tel():
    """Читает телеметрию из глобального dron"""
    global roll, pitch, yaw, dron
    if not dron:
        return None

    try:
        msg = dron.connection.recv_match(type='ATTITUDE', blocking=True, timeout=1)
        if msg:

            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = math.degrees(msg.yaw)

            print(f"Крен: {roll:.2f}° | Тангаж: {pitch:.2f}° | Рысканье: {yaw:.2f}°")
            return roll, pitch, yaw
        return None
    except:
        pass


def tel_thread():
    """Поток телеметрии"""
    global running
    while running:
        try:
            get_tel()
            time.sleep(0.05)
        except:
            time.sleep(0.1)


def camera_thread():
    """Поток камеры"""
    global running
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Камера не найдена")
        return

    cv2.namedWindow("raw frame", cv2.WINDOW_NORMAL)
    cv2.namedWindow("contours", cv2.WINDOW_NORMAL)

    while running:
        ret, frame = cap.read()
        if not ret: continue

        cv2.imshow("raw frame", frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)
            if 100 <= area <= 100000:
                cv2.drawContours(frame, [c], -1, (0, 0, 255), 2)
                angle = PCA.get_angle_pca(image_path=None, img=frame)
                print(f"Угол: {angle}")
                PCA.draw_main_axis(frame, c)
                break

        cv2.imshow("contours", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def excel_thread():
    """Запись в Excel каждые 2 сек"""
    global running, roll, pitch, yaw
    next_save = time.time() + 2

    while running:
        if time.time() >= next_save:
            try:
                exel.add_data_to_excel(EXEL_FILE, roll, pitch, yaw, 0, 0)
                print(f"📊 Excel: {roll:.1f}, {pitch:.1f}, {yaw:.1f}")
                next_save = time.time() + 2
            except Exception as e:
                print(f"Excel: {e}")
        time.sleep(0.1)


if __name__ == "__main__":
    print("🚁 Создаём Pioneer...")
    dron = Pioneer()

    # ✅ ФИКС WinError 10022 — НЕ используем wait_heartbeat()
    print("🔄 Инициализация MAVLink соединения...")
    try:
        # Даём время SDK на инициализацию сокета
        time.sleep(2)

        # Пробуем получить первое сообщение БЕЗ blocking
        msg = dron.connection.recv_match(type='HEARTBEAT', blocking=False, timeout=1)
        if msg:
            print(f"✅ Сердцебиение получено: sys={msg.get_srcSystem()}, comp={msg.get_srcComponent()}")
        else:
            print("⚠️  Сердцебиение не получено, но продолжаем...")

    except Exception as e:
        print(f"⚠️  Ошибка heartbeat: {e} — продолжаем без проверки")

    # Запрос потока ATTITUDE
    try:
        dron.connection.mav.request_data_stream_send(1, 1, 30, 10, 1)  # 10 Гц
        print("📡 Запрошена телеметрия 10 Гц")
    except:
        print("⚠️  Не удалось запросить поток")

    # ✅ Запуск потоков
    threading.Thread(target=tel_thread, daemon=True).start()
    threading.Thread(target=camera_thread, daemon=True).start()
    threading.Thread(target=excel_thread, daemon=True).start()

    print("🎬 Камера + телеметрия + Excel запущены!")
    print("📹 'q' в окне камеры / Ctrl+C для выхода")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Завершение...")
        running = False
        cv2.destroyAllWindows()
        time.sleep(1)
