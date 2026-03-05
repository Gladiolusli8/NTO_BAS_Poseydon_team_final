import time

from pioneer_sdk import Pioneer

dron = Pioneer()


try:
    dron.takeoff()
    dron.go_to_local_point(0, 0, 1, 0)
    while not dron.point_reached():
        time.sleep(0.1)
    dron.go_to_local_point(0, 2.6, 1, 0)
    while not dron.point_reached():
        time.sleep(0.1)
    dron.go_to_local_point(0, 0, 1, 0)
    while not dron.point_reached():
        time.sleep(0.1)
    dron.go_to_local_point(0, 2.6, 1, 0)
    while not dron.point_reached():
        time.sleep(0.1)
    dron.land()
    time.sleep(3)
    dron.disarm()
except:
    dron.land()
    time.sleep(3)
    dron.disarm()
dron.close_connection()