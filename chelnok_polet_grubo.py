import time

from pioneer_sdk import Pioneer

drun = Pioneer()
try:
    drun.takeoff()
    drun.go_to_local_point(0, 0, 1, 0)
    while not drun.point_reached():
        time.sleep(0.1)
    drun.go_to_local_point(0, 2.6, 1, 0)
    while not drun.point_reached():
        time.sleep(0.1)
    drun.go_to_local_point(0, 0, 1, 0)
    while not drun.point_reached():
        time.sleep(0.1)
    drun.go_to_local_point(0, 2.6, 1, 0)
    while not drun.point_reached():
        time.sleep(0.1)
    drun.land()
    time.sleep(3)
    drun.disarm()
except:
    drun.land()
    time.sleep(3)
    drun.disarm()
drun.close_connection()