import cv2
import numpy as np
import time
from pioneer_sdk import Camera  # камера Пионера[web:2]

# --- Параметры шахматной доски ---
CHESSBOARD_SIZE = (9, 6)   # количество внутренних углов по ширине и высоте[web:1]
SQUARE_SIZE = 20.0         # размер клетки в мм (для относительной метрики можно 1.0)[web:1]

# --- Подготовка 3D-точек (объектные точки) ---
objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0],
                       0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

objpoints = []  # 3D точки в мировой системе координат[web:1]
imgpoints = []  # 2D точки в изображении[web:1]

# --- Подключаемся к камере Пионера ---
cam = Camera()  # создаём объект камеры из pioneer_sdk[web:2]
cam.start_video_stream()  # запускаем видеопоток, если требуется в вашей версии SDK[web:2]

print("Нажимайте '1', чтобы сохранить кадр с шахматной доской, 'q' — завершить сбор кадров.")

while True:
    frame = cam.get_frame()  # получение кадра из камеры; имя функции зависит от SDK[web:2]
    if frame is None:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Поиск углов шахматной доски
    ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

    # Отрисовка найденных углов
    display = frame.copy()
    if ret:
        cv2.drawChessboardCorners(display, CHESSBOARD_SIZE, corners, ret)

    cv2.imshow('Drone Camera', display)
    key = cv2.waitKey(10) & 0xFF

    if key == ord('1') and ret:
        # Уточняем координаты углов[web:1]
        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                      30, 0.001)
        )
        objpoints.append(objp)
        imgpoints.append(corners2)
        print(f"Сохранён кадр #{len(objpoints)}")

    if key == ord('q'):
        break

cam.stop_video_stream()
cv2.destroyAllWindows()

# --- Проверяем, достаточно ли кадров ---
if len(objpoints) < 10:
    print("Недостаточно кадров для калибровки (минимум ~10). Сделайте больше снимков и запустите снова.")
    exit(0)

# --- Калибровка камеры ---
image_size = gray.shape[::-1]  # (width, height)[web:1]

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
    objpoints,
    imgpoints,
    image_size,
    None,
    None
)[web:1]

print("RMS ошибка калибровки:", ret)
print("Матрица камеры:\n", mtx)
print("Коэффициенты дисторсии:\n", dist)

# --- Сохранение коэффициентов в файл YAML (аналогично скрипту SDK)[web:2] ---
import yaml
calib_data = {
    "camera_matrix": mtx.tolist(),
    "dist_coeff": dist.tolist()
}

with open("calibration_matrix.yaml", "w") as f:
    yaml.dump(calib_data, f)

print("Калибровочные данные сохранены в calibration_matrix.yaml")