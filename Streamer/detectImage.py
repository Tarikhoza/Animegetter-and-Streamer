import cv2
import os
import numpy as np
from matplotlib import pyplot as plt

def process_img(img_rgb, template, count):
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    w, h = template.shape[::-1]

    res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        return 1

def detect(video,template,fps=24):
    vidcap = cv2.VideoCapture(video)
    template = cv2.imread(template,0)
    count = 0
    frame = 0
    while True:
      success,image = vidcap.read()
      if not success: break
      if process_img(image, template, count):
          return frame/fps
          break
      vidcap.set(1, frame-1)
      frame+=5
    return None

def extractTemplate(templateName,series,video,time,fps=24):
    vidcap = cv2.VideoCapture(video)
    vidcap.set(1,time*fps)
    success,image = vidcap.read()
    if ~os.path.exists(f"static/searchtemplates/{series}"):
        os.mkdir(f"static/searchtemplates/{series}")
    cv2.imwrite(f"static/searchtemplates/{series}/{templateName}.jpg",image)




#extractTemplate("intro","horimiya","static/series/horimiya/2.mp4",92)

#print(detect("static/series/horimiya/2.mp4", "static/searchtemplates/horimiya/intro.png"))
