import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

img = cv.imread("photo.jpeg")

if img is None:
    print("Ошибка: изображение не найдено!")
    exit()

print(f"Тип данных изображения: {img.dtype}")
print(f"Форма изображения: {img.shape}")

if img.dtype != np.uint8:
    img = img.astype(np.uint8)

dst = cv.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

cv.imwrite('2.jpg', dst)

img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
dst_rgb = cv.cvtColor(dst, cv.COLOR_BGR2RGB)

plt.subplot(121), plt.imshow(img_rgb)
plt.title('Original Image')
plt.xticks([]), plt.yticks([])

plt.subplot(122), plt.imshow(dst_rgb)
plt.title('Denoised Image')
plt.xticks([]), plt.yticks([])

plt.show()