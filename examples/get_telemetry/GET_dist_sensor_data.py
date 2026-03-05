from pioneer_sdk import Pioneer
import time

mini = Pioneer()

print("Начало координат установлено в точке старта.")
print("Вывод текущих координат дрона (X, Y, Z) относительно старта:\n")

while True:
    position = mini.get_local_position()  # или mini.get_position()

    if position is not None:
        x, y, z = position
        print(f"X: {x:6.2f} м, Y: {y:6.2f} м, Z: {z:6.2f} м")
    else:
        print("Данные о позиции недоступны. Проверьте подключение сенсоров или LPS.")

    time.sleep(1)