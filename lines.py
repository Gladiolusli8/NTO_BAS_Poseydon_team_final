import cv2
import numpy as np

def find_two_main_lines(img):
    if img is None:
        print("Ошибка загрузки изображения")
        return None
    
    inverted = cv2.bitwise_not(img)
    
    contours, _ = cv2.findContours(inverted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_contours = []
    
    img_height = img.shape[0]
    min_height = img_height * 0.02  # линия должна занимать минимум 30% высоты
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        if h >= min_height:
            # Проверяем соотношение сторон (должно быть узким и длинным)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < 0.5:  # ширина меньше половины высоты
                valid_contours.append(contour)
    
    valid_contours = sorted(valid_contours, key=lambda c: cv2.boundingRect(c)[0])
    
    if len(valid_contours) >= 2:
        # Если мусор слева, берем два правых контура
        # Если мусор справа, берем два левых контура
        
        # Проверяем, есть ли крупные контуры слева и справа
        left_contours = valid_contours[:2]
        right_contours = valid_contours[-2:]
        
        # Вычисляем суммарную площадь для левых и правых
        left_area = sum(cv2.contourArea(c) for c in left_contours)
        right_area = sum(cv2.contourArea(c) for c in right_contours)
        
        # Выбираем те, у которых больше площадь (обычно основные линии крупнее мусора)
        if left_area > right_area:
            main_contours = left_contours
        else:
            main_contours = right_contours
    else:
        print("Найдено меньше двух линий")
        return None
    
    # Создаем маску для результатов
    result = np.zeros_like(img)
    
    # Рисуем только найденные линии
    for contour in main_contours:
        cv2.drawContours(result, [contour], -1, 255, -1)
    
    return result

def find_lines_by_position(img):
    
    if img is None:
        print("Ошибка загрузки изображения")
        return None
    
    # Инвертируем для анализа
    inverted = cv2.bitwise_not(img)
    
    # Вертикальная проекция (сумма черных пикселей по столбцам)
    vertical_projection = np.sum(inverted == 255, axis=0)
    
    # Нормализуем проекцию
    vertical_projection = vertical_projection / np.max(vertical_projection)
    
    # Находим пики (столбцы с большим количеством черных пикселей)
    threshold = 0.3
    peaks = []
    
    for i in range(1, len(vertical_projection) - 1):
        if (vertical_projection[i] > threshold and 
            vertical_projection[i] > vertical_projection[i-1] and 
            vertical_projection[i] > vertical_projection[i+1]):
            peaks.append(i)
    
    # Группируем близкие пики (принадлежащие одной линии)
    grouped_peaks = []
    current_group = []
    
    for peak in sorted(peaks):
        if not current_group or peak - current_group[-1] < 20:
            current_group.append(peak)
        else:
            grouped_peaks.append(current_group)
            current_group = [peak]
    
    if current_group:
        grouped_peaks.append(current_group)
    
    # Берем центры групп как позиции линий
    line_positions = [int(np.mean(group)) for group in grouped_peaks]
    
    # Если линий больше двух, выбираем две крайние
    if len(line_positions) > 2:
        # Проверяем, где мусор (слева или справа)
        if line_positions[0] < img.shape[1] / 3:  # мусор слева
            line_positions = line_positions[-2:]  # берем два правых
        else:  # мусор справа
            line_positions = line_positions[:2]   # берем два левых
    
    # Создаем результат
    result = np.zeros_like(img)
    
    # Выделяем области вокруг найденных позиций
    for pos in line_positions:
        # Создаем вертикальную полосу шириной 50 пикселей вокруг линии
        x_start = max(0, pos - 25)
        x_end = min(img.shape[1], pos + 25)
        
        # Копируем исходные линии в результат
        line_area = inverted[:, x_start:x_end]
        result[:, x_start:x_end] = cv2.bitwise_or(result[:, x_start:x_end], line_area)
    
    return result

def clean_and_isolate_lines(img, output_path=None):
    # Основная функция
    print("Анализ изображения...")
    
    # Пробуем первый метод
    result1 = find_two_main_lines(img)
    
    # Пробуем второй метод
    result2 = find_lines_by_position(img)
    
    # Выбираем лучший результат (с наибольшим количеством белых пикселей)
    if result1 is not None and result2 is not None:
        white_pixels1 = np.sum(result1 == 255)
        white_pixels2 = np.sum(result2 == 255)
        
        if white_pixels1 > white_pixels2:
            result = result1
            print("Использован метод контуров")
        else:
            result = result2
            print("Использован метод проекций")
    elif result1 is not None:
        result = result1
        print("Использован метод контуров")
    elif result2 is not None:
        result = result2
        print("Использован метод проекций")
    else:
        print("Не удалось выделить линии")
        return None
    
    # Инвертируем обратно (белый фон, черные линии)
    result = cv2.bitwise_not(result)
    
    # Сохраняем результат
    if output_path:
        cv2.imwrite(output_path, result)
        print(f"Результат сохранен в {output_path}")
    
    return result

"""
# Пример использования
if __name__ == "__main__":
    input_image = "lines.png"  # путь к вашему изображению
    output_image = "output.png"  # путь для сохранения результата
    
    result = clean_and_isolate_lines(input_image, output_image)
    
    if result is not None:
        # Показываем результат
        cv2.imshow("Original", cv2.imread(input_image))
        cv2.imshow("Filtered Lines", result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
"""

