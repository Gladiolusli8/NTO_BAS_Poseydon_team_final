from pioneer_sdk import Pioneer
import time
import math
drun = Pioneer()
def wait_for_state(drone, target_state, timeout=30):
    start = time.time()
    while drone.get_autopilot_state() != target_state:
        if time.time() - start > timeout:
            return False
        time.sleep(0.1)
    return True
drun.connection.wait_heartbeat(timeout=10)
drun.connection.mav.request_data_stream(1, 30, 10, 1)
drun.arm()
drun.takeoff()


drun.land()
drun.disarm()