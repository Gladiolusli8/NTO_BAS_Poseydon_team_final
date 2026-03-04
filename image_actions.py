import cv2


def resize_img(input_img, scale_percent):
    width = int(input_img.shape[1] * scale_percent / 100)
    height = int(input_img.shape[0] * scale_percent / 100)
    dimension = (width, height)
    resize_image = cv2.resize(input_img, dimension,
                              interpolation=cv2.INTER_AREA)
    return resize_image


def img_to_gray(input_img, a, b):  # a и b пороги
    input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
    se = cv2.getStructuringElement(cv2.MORPH_RECT, (a, b))
    bg = cv2.morphologyEx(input_img, cv2.MORPH_DILATE, se)
    out_gray = cv2.divide(input_img, bg, scale=255)
    return out_gray


# Моя функция бинаризации
# thresh - порог бинаризации, bright яркость
def img_to_binary(input_img, thresh, bright):
    gray = img_to_gray(input_img=input_img)
    out_binary = cv2.threshold(gray, thresh, bright, cv2.THRESH_OTSU)[1]
    return out_binary

# функция эрозии изображения
def make_dilate(img, iters=4):
    mask_di = cv2.dilate(img, None, iterations=iters)
    return mask_di

# функция диалатации изображения
def make_erosion(img, iters=2):
    mask_er = cv2.erode(img, None, iterations=iters)
    return mask_er

def get_contours(img, draw=False):
    contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    if draw == True:
        contours = contours[0]
        cv2.drawContours(img, contours, -1, (255, 0, 255), 3)
        return contours, img
    return contours

def nothing(x):
    pass

def get_mass_center(contours, draw=False, img=None):
    biggest_contour = max(contours, key=cv2.contourArea)
    M = cv2.moments(biggest_contour)
    cx, cy = -1, -1
    if draw == True and img is not None:
        cv2.drawContours(img, biggest_contour, -1, (0, 0, 255), 3)
    if M['m00'] != 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        cv2.circle(img, (cx, cy), 10, (255, 0, 0), 2)
    if draw == True and img is not None:
        return cx, cy, img
    return cx, cy

#cv2.namedWindow("trackbars")
"""
cv2.createTrackbar('minb', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('ming', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('minr', 'trackbars', 0, 255, nothing)

cv2.createTrackbar('maxb', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('maxg', 'trackbars', 0, 255, nothing)
cv2.createTrackbar('maxr', 'trackbars', 0, 255, nothing)
# далее в цикле программы или каком-нибудь image callback вставьте следующее:
minb = cv2.getTrackbarPos('minb', 'trackbars')
ming = cv2.getTrackbarPos('ming', 'trackbars')
minr = cv2.getTrackbarPos('minr', 'trackbars')
maxb = cv2.getTrackbarPos('maxb', 'trackbars')
maxg = cv2.getTrackbarPos('maxg', 'trackbars')
maxr = cv2.getTrackbarPos('maxr', 'trackbars')
# Вот бинаризация изображения по рекомендациям НТО
im = cv2.inRange(im, (minb, ming, minr), (maxb, maxg, maxr))
if cv2.waitKey(1) == 27:
    break
"""