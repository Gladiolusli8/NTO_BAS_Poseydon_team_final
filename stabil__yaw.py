def error_yaw(yaw):
    kp = 2.5
    ki = 0.1
    kd = 0.2

    # Сохраняем предыдущие значения между вызовами функции
    if not hasattr(error_yaw, "prev_error"):
        error_yaw.prev_error = 0
        error_yaw.integral = 0
        error_yaw.last_time = None

    # Текущая ошибка
    error = 0 - yaw

    import time
    current_time = time.time()

    if error_yaw.last_time is not None:
        dt = current_time - error_yaw.last_time
        if dt > 0:
            error_yaw.integral += error * dt
            if error_yaw.integral > 10:
                error_yaw.integral = 10
            elif error_yaw.integral < -10:
                error_yaw.integral = -10

            derivative = (error - error_yaw.prev_error) / dt
        else:
            derivative = 0
    else:
        dt = 0
        derivative = 0

    output = kp * error + ki * error_yaw.integral + kd * derivative

    # Ограничение выхода
    # if output > 500:
    #     output = 500
    # elif output < -500:
    #     output = -500

    # Сохраняем значения
    error_yaw.prev_error = error
    error_yaw.last_time = current_time

    # УПРАВЛЕНИЕ МОТОРАМИ ЗДЕСЬ:
    if output > 5:  # небольшой гистерезис, чтобы не дрожать около нуля
        set_manual_speed_body_fixed(0, 5, 0, 0)  # крутим влево
    elif output < -5:
        set_manual_speed_body_fixed(0, -5, 0, 0)  # крутим вправо
    else:
        set_manual_speed_body_fixed(0, 0, 0, 0)  # держим горизонт

    #return output