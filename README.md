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

![контуры и окружности](https://github.com/Gladiolusli8/poseydon_nto/blob/main/conturs_with_circles.png)

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

## Блок схема 

---
ДОПИСАТЬ!!!
---

