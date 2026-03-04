from pioneer_sdk import Pioneer
import time
import math
drun = Pioneer()
def wait_for_state(drone, target_state, timeout=30):
    start = time.time()
    if drone.get_autopilot_state() != target_state:
        return False
    return True
try:
    drun.arm()
    drun.takeoff()
    while not wait_for_state(drun, "MISSION"):
        time.sleep(0.1)
    time.sleep(10)
    drun.land()
    drun.disarm()
except:
    drun.land()
    drun.disarm()