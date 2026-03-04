import time
import math
import statistics
from pioneer_sdk import Pioneer

# ================== КОНФИГУРАЦИЯ ==================
# Частота цикла управления (сек)
DT = 0.05

# PID-коэффициенты (XY - горизонт, Z - высота)
# Для LPS нужны более "жесткие" настройки, чем для оптического потока
PID_XY = {'kp': 1.2, 'ki': 0.05, 'kd': 0.15}
PID_Z = {'kp': 0.8, 'ki': 0.02, 'kd': 0.1}

# Ограничения скорости (м/с)
MAX_SPEED_XY = 1.1
MAX_SPEED_Z = 0.6

# Точность миссии (метры)
ARRIVAL_RADIUS = 0.15  # Считаем точку достигнутой
LANDING_ALT = 0.4  # Высота начала точного снижения
LANDING_RADIUS = 0.05  # Точность посадки (5 см)

# Маршрут (X, Y, Z) в метрах от точки взлета
# TODO: perepisat
WAYPOINTS = [
    (0.0, 0.0, 1.5),
    (1.0, 0.0, 1.5),
    (1.0, 1.0, 1.5),
    (0.0, 1.0, 1.5),
    (0.0, 0.0, 1.5),
]


# ================== PID-КОНТРОЛЛЕР ==================
class PID:
    def __init__(self, kp, ki, kd, limit=1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.limit = limit
        self.reset()

    def reset(self):
        self.i = 0
        self.prev_err = 0
        self.last_t = time.time()

    def update(self, err):
        now = time.time()
        dt = now - self.last_t
        if dt <= 0: dt = 0.01
        self.last_t = now

        # Интеграл с защитой от переполнения (Anti-windup)
        self.i += err * dt
        self.i = max(-self.limit, min(self.limit, self.i))

        # Дифференциал
        d = (err - self.prev_err) / dt
        self.prev_err = err

        out = self.kp * err + self.ki * self.i + self.kd * d
        return max(-self.limit, min(self.limit, out))


# ================== МЕНЕДЖЕР ПОЛЕТА ==================
class FlightManager:
    def __init__(self, drone):
        self.drone = drone
        self.pid_x = PID(**PID_XY, limit=MAX_SPEED_XY)
        self.pid_y = PID(**PID_XY, limit=MAX_SPEED_XY)
        self.pid_z = PID(**PID_Z, limit=MAX_SPEED_Z)

        # Для оценки скорости и ветра
        self.prev_pos = None
        self.prev_t = None
        self.wind_vx = 0.0
        self.wind_vy = 0.0

    def get_pos(self):
        """Безопасное получение позиции LPS"""
        pos = self.drone.get_local_position_lps()
        if pos is None:
            return None
        # Проверка на валидность (иногда SDK может вернуть (0,0,0) при ошибке)
        if pos == (0.0, 0.0, 0.0) and self.prev_pos is not None:
            # Если вдруг вернуло нули, а мы уже летали - это подозрительно
            # Но для LPS (0,0,0) - это просто точка старта, так что строго не фильтруем
            pass
        return pos

    def estimate_velocity(self, pos):
        """Расчет скорости по смещению позиции"""
        now = time.time()
        if self.prev_pos is None or self.prev_t is None:
            self.prev_pos = pos
            self.prev_t = now
            return [0.0, 0.0, 0.0]

        dt = now - self.prev_t
        if dt < 0.01: dt = 0.01  # Защита от деления на ноль

        vx = (pos[0] - self.prev_pos[0]) / dt
        vy = (pos[1] - self.prev_pos[1]) / dt
        vz = (pos[2] - self.prev_pos[2]) / dt

        self.prev_pos = pos
        self.prev_t = now
        return [vx, vy, vz]

    def fly_to(self, target, timeout=40):
        """Полет в точку с компенсацией ветра"""
        print(f"\n🎯 Цель: {target}")
        self.pid_x.reset()
        self.pid_y.reset()
        self.pid_z.reset()
        self.prev_pos = None
        self.prev_t = None

        start = time.time()

        while time.time() - start < timeout:
            pos = self.get_pos()

            # Если LPS потерялся - зависаем
            if pos is None:
                print("\n⚠️ Потеря LPS! Зависание...")
                self.drone.set_manual_speed(0, 0, 0, 0)
                time.sleep(DT)
                continue

            # Расчет скорости
            vel = self.estimate_velocity(pos)

            # Ошибки
            ex = target[0] - pos[0]
            ey = target[1] - pos[1]
            ez = target[2] - pos[2]

            # PID + Компенсация скорости (D-составляющая часто дублирует гашение скорости)
            # Здесь мы явно гасим скорость, чтобы дрон не пролетал точку по инерции
            vx = self.pid_x.update(ex) - vel[0] * 0.5
            vy = self.pid_y.update(ey) - vel[1] * 0.5
            vz = self.pid_z.update(ez) - vel[2] * 0.5

            # Ограничение скорости (Safety clip)
            vx = max(-MAX_SPEED_XY, min(MAX_SPEED_XY, vx))
            vy = max(-MAX_SPEED_XY, min(MAX_SPEED_XY, vy))
            vz = max(-MAX_SPEED_Z, min(MAX_SPEED_Z, vz))

            # Отправка команды
            self.drone.set_manual_speed(vx, vy, vz, 0)

            # Отладка
            dist = math.hypot(ex, ey)
            print(f"\r📍 Dist: {dist:.2f}м | Z: {pos[2]:.2f}м | V: {vel[0]:.1f},{vel[1]:.1f}", end="")

            # Проверка достижения
            if dist < ARRIVAL_RADIUS and abs(ez) < 0.1:
                print("\n✅ Точка достигнута")
                self.drone.set_manual_speed(0, 0, 0, 0)
                time.sleep(0.5)  # Стабилизация
                return True

            time.sleep(DT)

        print("\n⚠️ Таймаут")
        return False

    def land_precise(self, x=0.0, y=0.0):
        """Точная посадка"""
        print(f"\n🛬 Посадка в ({x}, {y})")

        # 1. Снижение до высоты LANDING_ALT
        temp_target = (x, y, LANDING_ALT)
        self.fly_to(temp_target, timeout=20)

        # 2. Вертикальное снижение с микро-коррекцией XY
        while True:
            pos = self.get_pos()
            if pos is None:
                break

            # Коррекция по XY (очень важная для точности)
            dx = x - pos[0]
            dy = y - pos[1]
            vx = dx * 1.5  # Пропорциональный коэффициент для посадки
            vy = dy * 1.5
            vx = max(-0.2, min(0.2, vx))
            vy = max(-0.2, min(0.2, vy))

            # Снижение
            vz = -0.15 if pos[2] > 0.1 else 0

            self.drone.set_manual_speed(vx, vy, vz, 0)

            # Касание
            if pos[2] <= 0.15 and math.hypot(dx, dy) < LANDING_RADIUS:
                break
            time.sleep(DT)

        # 3. Финальное касание
        print("🎯 Касание...")
        self.drone.set_manual_speed(0, 0, -0.05, 0)
        time.sleep(1.5)
        self.drone.set_manual_speed(0, 0, 0, 0)
        print("✅ Посадка завершена")


# ================== ГЛАВНАЯ ФУНКЦИЯ ==================
def main():
    drone = Pioneer()
    time.sleep(2)  # Инициализация

    # Проверка связи
    print("🔍 Проверка LPS...")
    for i in range(30):
        pos = drone.get_local_position_lps()
        if pos:
            print(f"✅ LPS OK: {pos}")
            break
        time.sleep(0.1)
    else:
        print("❌ LPS не найден! Проверьте маяки.")
        return

    try:
        print("🚀 Взлет...")
        drone.takeoff()
        time.sleep(4)

        manager = FlightManager(drone)

        # Полет по точкам
        for wp in WAYPOINTS:
            if not manager.fly_to(wp):
                print("⚠️ Ошибка на маршруте, продолжаю...")

        # Посадка в начало координат
        manager.land_precise(x=0.0, y=0.0)

        print("🏁 Миссия выполнена")

    except KeyboardInterrupt:
        print("\n⚠️ Стоп по кнопке")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        drone.set_manual_speed(0, 0, 0, 0)
        time.sleep(0.2)
        # Если дрон еще в воздухе - садим
        if drone.get_local_position_lps() and drone.get_local_position_lps()[2] > 0.2:
            drone.land()


if __name__ == "__main__":
    main()