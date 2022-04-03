import cv2 as cv
import pytesseract
import imutils
import numpy as np
import math

#img = cv.imread('images/image3.jpg')

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract"

def processTheImage(img):
    imgSize = tuple(map(lambda x: x//5, img.shape[:2]))[::-1]
    imgSizeT = tuple(map(lambda x: x//2, img.shape[:2]))[::-1]
    img = cv.resize(img, imgSizeT)

    imgray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    imgray = cv.GaussianBlur(imgray, (13,13), 0)
    thresh = cv.adaptiveThreshold(imgray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 7, 2)

    kernel = np.ones((7, 7), np.uint8)
    opened = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel=kernel)

    dst = cv.Canny(img, 40, 200, None, 3)
    cnts, _ = cv.findContours(opened, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    lines = []
    for cnt in cnts[1:]:
        x,y,w,h = cv.boundingRect(cnt)
        if w > h and w/h > 18:
            lines.append(cnt)

    def sortKey(x):
        return x[0][0]

    alpha = 0

    ls, rs = 0,0

    for line in lines:
        minim = min(line, key=sortKey)
        maxim = max(line, key=sortKey)

        diffy = abs(minim[0][1]-maxim[0][1])
        diffx = abs(minim[0][0]-maxim[0][0])

        if minim[0][1]<maxim[0][1]:
            ls += 1
        else:
            rs += 1
        
        alpha += diffy/diffx

    alpha = alpha/len(lines)
    alphaDeg = math.degrees(math.atan(alpha))

    sign = -1 if ls > rs else 1

    img = imutils.rotate_bound(img, alphaDeg*sign)

    imageString = pytesseract.image_to_string(img, lang="hrv")

    lines = imageString.split("\n")

    itemState = False
    itemStateT = True
    items = []
    out = []
    ukupno = 0
    for i in lines[::-1]:
        if ("Cijena" in i) or ("cijena" in i) or ("CIJENA" in i):itemState=False
        if itemState:
            items.append(i)
        if (("Ukupno" in i) or ("ukupno" in i) or ("UKUPNO" in i)) and itemStateT:
            ukupno = float(i.split(" ")[-2].replace(",","."))
            itemState=True
            itemStateT=False
    items = items[::-1]
    for item in items:
        item.split(" ")
        try:
            int(item[0])
        except:
            if item.replace(" ", "") not in [""]:
                out.append(item)
    return ukupno, out
