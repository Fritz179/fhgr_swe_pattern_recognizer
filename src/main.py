import cv2 as cv
img = cv.imread("./assets/test_image_00.png")

#Adjust image size to fit on screen

scale_percent = 60
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
dim = (width, height)

# resize image
img = cv.resize(img, dim, interpolation = cv.INTER_AREA)
cv.imshow("Display window", img)
k = cv.waitKey(0) # Wait for a keystroke in the window