import cv2
from pioneer_sdk import *
import threading
from image_actions import *

cv2.createTrackbar('minb', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('ming', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('minr', 'trackbars', 0, 255, nothing)

cv2.createTrackbar('maxb', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('maxg', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('maxr', 'trackbars', 0, 255, nothing)

minb = 0
ming = 61
minr = 60
maxb = 255
maxg = 255
maxr = 234

def camera_thread():
    stream = VideoStream()
    stream.start()

    while True:
        try:
            frame = stream.get_frame()
            if frame is not None:
                #minb = cv2.getTrackbarPos('minb', 'trackbars')
                #ming = cv2.getTrackbarPos('ming', 'trackbars')
                #minr = cv2.getTrackbarPos('minr', 'trackbars')
                #maxb = cv2.getTrackbarPos('maxb', 'trackbars')
                #maxg = cv2.getTrackbarPos('maxg', 'trackbars')
                #maxr = cv2.getTrackbarPos('maxr', 'trackbars')
                im = cv2.inRange(frame, (minb, ming, minr), (maxb, maxg, maxr))
                cv2.imshow("img from piioneer", frame)
                cv2.imshow("binary image", im)
                contours, conimg = get_contours(im, draw=True)
                cv2.imshow("img with contours", conimg)
                cx, cy, cimg = get_mass_center(contours=contours, draw=True, img=im)
                print(f"{cx}, {cy}")
                cv2.imshow("img with cx cy", cimg)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"{e}")
        

if __name__ == "__main__":
    cam_thread = threading.Thread(target=camera_thread)
    cam_thread.start()
    cam_thread.join()
    print("exiting")
    cv2.destroyAllWindows()