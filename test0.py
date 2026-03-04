from pioneer_sdk import Pioneer
import time
pioneer = Pioneer()
try:
    pioneer.arm()
    pioneer.takeoff()
    pioneer.go_to_local_point(x=0, y=0, z=1, yaw=0)
    while not pioneer.point_reached():
        time.sleep(0.1)
    pioneer.land()
    pioneer.disarm()
except KeyboardInterrupt:
    print("Остановка программы, производится посадка")
    pioneer.land()
pioneer.close_connection()