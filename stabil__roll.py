def error_roll(roll):
    kp = 0.7
    ki = 0.02
    kd = 0.1

    # Сохраняем предыдущие значения между вызовами функции
    if not hasattr(error_roll, "prev_error"):
        error_roll.prev_error = 0
        error_roll.integral = 0
        error_roll.last_time = None

    # Текущая ошибка
    error = 0 - roll

    import time
    current_time = time.time()

    if error_roll.last_time is not None:
        dt = current_time - error_roll.last_time
        if dt > 0:
            error_roll.integral += error * dt
            if error_roll.integral > 10:
                error_roll.integral = 10
            elif error_roll.integral < -10:
                error_roll.integral = -10

            derivative = (error - error_roll.prev_error) / dt
        else:
            derivative = 0
    else:
        dt = 0
        derivative = 0

    output = kp * error + ki * error_roll.integral + kd * derivative

    # # Ограничение выхода
    # if output > 500:
    #     output = 500
    # elif output < -500:
    #     output = -500

    # Сохраняем значения
    error_roll.prev_error = error
    error_roll.last_time = current_time

    # УПРАВЛЕНИЕ МОТОРАМИ ЗДЕСЬ:
    if output > 5:  # небольшой гистерезис, чтобы не дрожать около нуля
        set_manual_speed_body_fixed(5, 0, 0, 0)  # крутим влево
    elif output < -5:
        set_manual_speed_body_fixed(-5, 0, 0, 0)  # крутим вправо
    else:
        set_manual_speed_body_fixed(0, 0, 0, 0)  # держим горизонт

    return output