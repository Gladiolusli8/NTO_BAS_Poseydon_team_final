# Команда «Посейдон»

## Состав команды

1. Сапрыкин Александр Сергеевич — капитан, программист, разработчик алгоритмов, контентмейкер.
2. Сердюк Иван Николаевич — программист, разработчик алгоритмов компьютерного зрения.
3. Ефремов Елисей Алексеевич — программист, физик, разработчик алгоритмов, создатель ауры.
4. Герасимов Роман Сергеевич — программист, главный оператор дрона, разработчик алгоритмов, создатель ауры.

---

# Задание 1

## Файл

`telemetry_poletnik.py`

## Описание

Первое задание это просто тест работы дрона. Просто взлететь и взять телеметрию. Далее нужно сесть вниз.

---

# Задание 2

## Файл

`test2.py`

## Описание

Первое задание просто было как тест работы дрона, второе ззаключалось в том, что необходимо было определить крен, тангаж, рыскание от данных с телеметрии, а также по OpenCV опреелить тангаж и крен по изображению.
Изображение с камеры выгляит так: 
![фото со стенда](https://github.com/Gladiolusli8/poseydon_nto/blob/main/roi_example.png)

Программа выполняет следующие действия:

1. Читает иззображение с камеры ноутбука
2. Накладывает фильтры на него
3. Ищет контуры
4. Пытается сделать из контуров элипсы и кргуи
5. По полученным окружностям вычисляет оглы поворота относительно оси x и y
6. Запыисывает в Excel файл углы

Бинарное изображение после фильтров:
![фильтры](https://github.com/Gladiolusli8/poseydon_nto/blob/main/binary_circles.png)
Выделенные контуры окружностей и отмеченная ориентации на изображении:
![контуры и окружности](https://github.com/Gladiolusli8/poseydon_nto/blob/main/conturs_with_circles.png)

Для нахождения углов использовался алгоритм метод главных компонент. Он описан в файле `PCA.py`, а также в файле `through_circles.py`, т.к. для кругов было проще сделать немного по другому.
Отрывок из `PCA.py`:
```python
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
```
И из `through_circles.py`:
```python
def get_pitch_roll(frame, get_back=False):
    closed = filters.get_binary_image(frame)
    min_area = 20000
    filtered_mask = np.zeros_like(closed)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=4)

    angles_x = []
    angles_y = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        #print(area)
        if area > min_area < 350000:
            # Создаём маску только для текущей компоненты
            component_mask = (labels == i).astype(np.uint8) * 255

            # Вычисляем моменты
            M = cv2.moments(component_mask)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                # Центральные моменты второго порядка
                mu20 = M['mu20']
                mu02 = M['mu02']
                mu11 = M['mu11']

                # Угол ориентации главной оси (в радианах)
                theta_x = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)
                angle_deg_x = np.degrees(theta_x)  # если нужен в градусах
                angles_x.append(angle_deg_x)

                angle_from_y = np.pi / 2 - theta_x
                angle_from_y_deg = np.degrees(angle_from_y)
                angles_y.append(angle_from_y_deg)

                # Рисуем центр
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                # Рисуем линию, показывающую ориентацию (длина 50 пикселей)
                length = 50
                x2 = int(cx + length * np.cos(theta_x))
                y2 = int(cy - length * np.sin(angle_from_y))
                cv2.line(frame, (cx, cy), (x2, y2), (255, 0, 0), 2)

                # Можно также нарисовать контур всей компоненты для наглядности
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
        else:
            angles_x.append(0.0)
            angles_y.append(90.0)
    if get_back == True: 
        return angles_x, angles_y, frame
    return angles_x, angles_y
```
В каждом из файлов есть примеры изпользования.
Но такой подход имеет большой минус: окружность может повернуться так, что будет мёртвая зона. И в целом задача решена не правильно. Этот подход определяет не крен и тангаж, а рысканье и крен.

---

# Задание 3

В третьем задании необходимо было выполнить целночный полет.
![условие третей задачи](https://github.com/Gladiolusli8/poseydon_nto/blob/main/statement.png)

Написать программу автономного полёта, которая должна обеспечить челночный пролёт расстояния в (2,5 + 2,5 + 2,5) метров и + 1,25 метра на высоте 1-2 м для посадки в середине лётного поля. Размеры сетки 3х3х3 м 3.

Поле, сфотографированное сверху 
![поле](https://github.com/Gladiolusli8/poseydon_nto/blob/main/image.png)

Поле, после фильтров
![поле с фильтрами](https://github.com/Gladiolusli8/poseydon_nto/blob/main/lines.png)

Поле, после фильтров и функции удалении все, кроме линии
![поле с фильтрами](https://github.com/Gladiolusli8/poseydon_nto/blob/main/output.png)


Поле, после фильтров и функции удалении все, кроме линии, а также с bounding boxes и найденными центрами линий
![поле с фильтрами](https://github.com/Gladiolusli8/poseydon_nto/blob/main/conturs_with_centers.png)

Кроме этого программа должна определить скорость бокового ветра и записать её в файл .txt (скорость ветра = … м/с).
Мы придумали решить эту задачу при помощи фильтра Калмана. Эта решение описано в файле `wind_opr.py`.

```python
def estimate_wind_speed(roll, pitch):
    theta = math.sqrt(roll**2 + pitch**2)
    force = MASS * G * math.tan(theta)
    v = math.sqrt(abs((2 * force) / (AIR_DENSITY * CD * AREA)))
    return v
```

## Структура работы

Программа разделена на несколько потоков:

### 1. Поток сбора данных.
Отвечает за сбор телеметрии с внутренних датчиков дрона.

### 2. Поток работы с камерой  
Считывает кадры и выполняет распознавание положения дрона.

### 3. Основной поток  
Запускает остальные потоки, группирует все данные и завершает работу при загрузке в таблицу.

## Основная логика программы

Сбор телеметрии с датчиков:

```python
 msg = dron.connection.recv_match(type='ATTITUDE', blocking=True, timeout=0.5)
    if msg:
        roll = math.degrees(msg.roll)
        pitch = math.degrees(msg.pitch)
        yaw = math.degrees(msg.yaw)
```

Обработка OpenCV:

```python
def camera_thread():
    global set_target, cv_target
    camera = Camera()
    camera.connect()
    
    while True:
        img = test
        cv2.imshow("img", img)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, b_min, b_max)
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(mask, kernel, iterations=2)
        eroded_mask = cv2.erode(dilated_mask, kernel, iterations=1)

        lines_img = lines.clean_and_isolate_lines(eroded_mask)
        cv2.imshow("clean", lines_img)
        
        inverted_lines = cv2.bitwise_not(lines_img)
        contours, _ = cv2.findContours(inverted_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_with_contours = img.copy()
        centers = []
        
        for c in contours:
            perimeter = cv2.arcLength(c, True)

            if perimeter > 100: 
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                box = box.astype(int)
                center = (int(rect[0][0]), int(rect[0][1]))
                cv2.drawContours(img_with_contours, [box], 0, (0, 255, 0), 3)
                cv2.circle(img_with_contours, center, 10, (0, 0, 255), -1)
                print(f"Найден объект. Центр: X={center[0]}, Y={center[1]}")
                centers.append(center)
```

Запись данных в таблицу:

```python
# Загружаем книгу
wb = load_workbook(filename)
ws = wb.active

ws.cell(row=row, column=1).value = measure_id  # Номер измерения
ws.cell(row=row, column=2).value = round(roll, 2)  # Крен
ws.cell(row=row, column=3).value = round(pitch, 2)  # Тангаж
ws.cell(row=row, column=4).value = round(yaw, 2)  # Рысканье
ws.cell(row=row, column=5).value = val1  # Доп столбец 1
ws.cell(row=row, column=6).value = val2  # Доп столбец 2
```

# Итог

---

Из-за плохой организации финала, нам даже leaderboard не скинули, не скинули, за что поставили балы, а за что сняли. Мы не ззнаем на каком мы месте.
