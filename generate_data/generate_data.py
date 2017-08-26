#coding=utf-8
import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import cv2
import numpy as np
import random
import os
from math import *
import pickle
import re

with open('../chinesechars.txt') as to_read:chars = list(to_read.read().strip())

def r(val):
    return int(np.random.random() * val)

def random_pick(some_list, probabilities):
    x = random.uniform(0,1)
    cumulative_probability = 0.0
    for item, item_probability in zip(some_list, probabilities):
        cumulative_probability += item_probability
        if x < cumulative_probability:break
    return item

def rot(img,angel,shape,max_angel,bg_gray):
    size_o = [shape[1],shape[0]]

    size = (shape[1] + int(shape[0]*cos((float(max_angel )/180) * 3.14)),shape[0])


    interval = abs(int(sin((float(angel) /180) * 3.14)* shape[0]))

    pts1 = np.float32([[0,0], [0,size_o[1]], [size_o[0],0], [size_o[0], size_o[1]]])
    if(angel>0):

        pts2 = np.float32([[interval,0],[0,size[1]  ],[size[0],0  ],[size[0]-interval,size_o[1]]])
    else:
        pts2 = np.float32([[0,0],[interval,size[1]  ],[size[0]-interval,0  ],[size[0],size_o[1]]])

    M  = cv2.getPerspectiveTransform(pts1,pts2)
    dst = cv2.warpPerspective(img,M,size,borderValue=bg_gray)

    return dst

def rotRandrom(img, factor, size, bg_gray):
    shape = size
    pts1 = np.float32([[0, 0], [0, shape[0]], [shape[1], 0], [shape[1], shape[0]]])
    pts2 = np.float32([[r(factor), r(factor)], [ r(factor), shape[0] - r(factor)], [shape[1] - r(factor),  r(factor)],
                       [shape[1] - r(factor), shape[0] - r(factor)]])
    M = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(img, M, size, borderValue=bg_gray)
    return dst

def tfactor(img):

    img[:,:] = img[:,:]*(0.8+ np.random.random()*0.2)
    return img


def random_scale(x,y):
    gray_out = r(y+1-x) + x
    return gray_out

def text_Gengray(bg_gray, line):
    gray_flag = np.random.randint(2)
    if bg_gray < line:
        text_gray = random_scale(bg_gray + line, 255)
    elif bg_gray > (255 - line):
        text_gray = random_scale(0, bg_gray - line)
    else:
        text_gray = gray_flag*random_scale(0, bg_gray - line) + (1 - gray_flag)*random_scale(bg_gray+line, 255)
    return text_gray

def GenCh(f,val, data_shape1, data_shape2, bg_gray, text_gray, text_position):
    img=Image.new("L", (data_shape1,data_shape2),bg_gray)
    draw = ImageDraw.Draw(img)
    draw.text((0, text_position),val,text_gray,font=f)
    #draw.text((0, text_position),val.decode('utf-8'),0,font=f)
    A = np.array(img)
    return A

def AddNoiseSingleChannel(single):
    diff = 255-single.max()
    noise = np.random.normal(0,1+r(6),single.shape)
    noise = (noise - noise.min())/(noise.max()-noise.min())
    noise= diff*noise
    noise= noise.astype(np.uint8)
    dst = single + noise
    return dst

def Addblur(img, val):
    blur_kernel = r(val) + 1
    #print blur_kernel
    img = cv2.blur(img, (blur_kernel,blur_kernel))
    return img

class GenText:
    def __init__(self, font, font_size, counter):
        self.font = ImageFont.truetype(font,font_size)
        self.counter = counter

    def draw(self,val,data_shape1, data_shape2):
        bg_gray = r(256)
        text_gray = text_Gengray(bg_gray, 60)
        text_position = random_scale(4,12)
        offset_left = int(np.random.random() * 30)
        offset_right = int(np.random.random() * 30)
        offset_middle = 17
        add_position = -1
        if self.counter > 4:
            add_number = np.random.randint(2)
        else:
            add_number = 0
        if add_number == 1:
            add_position = np.random.randint(self.counter-1)
        offset = offset_left + offset_right + offset_middle*add_number
        img = np.array(Image.new("L", (self.counter * data_shape1 + offset, data_shape2), bg_gray))
        base = offset_left
        for i in range(counter):
            #offset_middle_add = random_pick([0,1],[0.8,0.2])*offset_middle
            img[0: data_shape2, base : base + data_shape1]= GenCh(self.font,val[i], data_shape1, data_shape2, bg_gray, text_gray, text_position)
            base += data_shape1
            if add_position == i:
                base += offset_middle
        return img, bg_gray

    def generate(self,text, data_shape1, data_shape2):
        fg, bg_gray = self.draw(text,data_shape1, data_shape2)
        com = rot(fg,r(60)-30,fg.shape,30, bg_gray)
        com = rotRandrom(com,10,(com.shape[1],com.shape[0]), bg_gray)
        com = tfactor(com)
        com = Addblur(com, 8)
        #com = AddNoiseSingleChannel(com)
        return com
    
    def genTextString(self, counter):
        textStr = ""
        for idx in range(counter):
            textStr += chars[r(len(chars))]

        return textStr
        

if __name__ == '__main__':
    import sys
    # In my option,i know i can generate data in multiprocess mode,but i'd like to run this program with different parameter.
    all_outputPath = ["../data/val","../data/test","../data/train"]
    all_num = [30000,1000,70000]
    outputPath,num = all_outputPath[int(sys.argv[1])],all_num[int(sys.argv[1])]
    gt = []
    imgaePath = os.path.join('..',outputPath, 'text')
    font_size = 35
    data_shape1 = 30
    data_shape2 = 80

    if (not os.path.exists(imgaePath)):
        os.mkdir(imgaePath)
    sum = 0
    for counter in range(2,10):
        # I collect many fonts,pick which you like
        G = GenText("./fonts/经典宋体简.TTF", font_size, counter)
        for i in range(num):
            textStr = G.genTextString(counter)
            # print(textStr)
            img =  G.generate(textStr, data_shape1, data_shape2)
            #print img.shape
            cv2.imwrite(os.path.join(imgaePath, str(i + sum) + ".jpg"), img)
            gt.append(textStr)
        sum += num
        print(counter,'finish!')
    gt_file = open(os.path.join('..',outputPath, 'gt.pkl'), 'wb')
    pickle.dump(gt, gt_file)
    gt_file.close()
