import cv2 as cv
import numpy as np
from math import atan2, cos, sin, sqrt, pi

def draw_direction_arrow(img, center, direction, color, scale):
    """Рисует стрелку направления из центра."""
    # Конечная точка основной линии
    endpoint = (int(center[0] + direction[0] * scale), 
                int(center[1] + direction[1] * scale))
    
    cv.line(img, center, endpoint, color, 2, cv.LINE_AA)
    
    # Рисуем наконечник стрелки
    angle = atan2(direction[1], direction[0])
    p1 = (int(endpoint[0] - 10 * cos(angle - pi / 4)),
          int(endpoint[1] - 10 * sin(angle - pi / 4)))
    p2 = (int(endpoint[0] - 10 * cos(angle + pi / 4)),
          int(endpoint[1] - 10 * sin(angle + pi / 4)))
    
    cv.line(img, endpoint, p1, color, 2, cv.LINE_AA)
    cv.line(img, endpoint, p2, color, 2, cv.LINE_AA)

def get_orientation_pca(cnt, center_coords, img_to_draw=None):
    """
    Принимает:
    - cnt: контур (точки)
    - center_coords: кортеж или список (x, y) - центр контура
    - img_to_draw: (опционально) изображение, на котором рисовать стрелки
    
    Возвращает:
    - angle_deg: угол в градусах относительно оси X
    """
    # 1. Подготовка точек контура
    data_pts = cnt.reshape(-1, 2).astype(np.float64)
    
    # 2. Подготовка центра для PCA (нужен формат numpy array)
    mean = np.array([center_coords], dtype=np.float64).reshape(1, 2)
    
    # 3. PCA анализ с использованием переданного центра
    # Используем PCACompute, передавая заранее вычисленное среднее
    _, eigenvectors, eigenvalues = cv.PCACompute2(data_pts, mean=mean)

    # Главный вектор (направление длины эллипса)
    v1 = eigenvectors[0] 
    
    # 4. Вычисление угла в градусах относительно оси X
    # В OpenCV Y направлен вниз, поэтому atan2(y, x) даст корректный угол
    angle_rad = atan2(v1[1], v1[0])
    angle_deg = np.degrees(angle_rad)

    # 5. Отрисовка (если передано изображение)
    if img_to_draw is not None:
        cx, cy = int(center_coords[0][0]), int(center_coords[0][1])
        
        # Длина стрелок на основе собственных чисел (eigenvalues)
        scale = 0.5 * np.sqrt(eigenvalues[0][0])
        
        # Конечная точка главной оси (зеленая)
        p1 = (int(cx + v1[0] * scale), int(cy + v1[1] * scale))
        cv.arrowedLine(img_to_draw, (cx, cy), p1, (0, 255, 0), 2, tipLength=0.3)
        
        # Вторая ось (синяя) для наглядности
        if len(eigenvectors) > 1:
            v2 = eigenvectors[1]
            scale2 = 0.5 * np.sqrt(eigenvalues[1][0])
            p2 = (int(cx + v2[0] * scale2), int(cy + v2[1] * scale2))
            cv.arrowedLine(img_to_draw, (cx, cy), p2, (255, 255, 0), 2, tipLength=0.3)

    return angle_deg
"""
# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    src = cv.imread('circles.png') # Ваше изображение с черными эллипсами
    if src is None:
        print("Ошибка: файл не найден")
        exit()

    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
    # Инвертируем, так как объекты черные
    _, bw = cv.threshold(gray, 127, 255, cv.THRESH_BINARY_INV)

    contours, _ = cv.findContours(bw, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    for c in contours:
        # Фильтр по площади и размеру (как вы просили ранее)
        if cv.contourArea(c) > 500:
            # Получаем угол и рисуем графику
            angle, center = get_contour_orientation(src, c)
            
            # Подписываем угол рядом с объектом
            cv.putText(src, f"{angle:.1f} deg", (center[0]-20, center[1]-20), 
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            print(f"Объект в {center}: угол {angle:.2f} градусов")

    cv.imshow('PCA Orientation', src)
    cv.waitKey(0)
    cv.destroyAllWindows()
"""