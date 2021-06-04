import cv2
import os
import numpy as np
from matplotlib import pyplot as plt

def process_image(img_rgb, template, count):
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    w, h = template.shape[::-1]

    res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where( res >= threshold)
    for pt in zip(*loc[::-1]):
        return 1
    return 0


def getTimeStamp(video,image,startFrame=0):
    vidcap = cv2.VideoCapture(video)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    template = cv2.imread(image,0)
    count = startFrame
    while True:
      success,image = vidcap.read()
      if not success: break
      if(process_image(image, template, count)):
          return count/fps
          break
      vidcap.set(1,count)
      count += 15
    return None



def generateTimeStamps(seriesName,name="",startFrame=0):
    seriesPath=os.path.join("static","series",seriesName)
    templates=[]
    results=[]
    templatesPath=os.path.join("static","searchtemplates",seriesName)
    for template in os.listdir(templatesPath):
        if name in template:
            templates.append(os.path.join(templatesPath,template))
    for i in os.listdir(seriesPath):
        videoPath=os.path.join(seriesPath,i)
        for i in templates:
            res=getTimeStamp(videoPath,i,startFrame=startFrame)
            if res!=None:
                print(res)
                results.append({"video":videoPath,"timestamp":res})
    return results
