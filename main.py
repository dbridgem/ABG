# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 18:40:30 2019

@author: Devon Bridgeman

This is a script to generate an animated bar graph from a csv input
"""
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw,ImageFont
import os
import cv2
from cv2 import VideoWriter, VideoWriter_fourcc
import shutil

colors = [(256,0,256,200),(256,0,0,200),(0,256,0,200),(0,0,256,200),
          (128,128,128,200),(128,0,0,200),(0,128,0,200),(0,0,128,200),
          ]
#Optional Inputs
titlefont = ImageFont.truetype("arial.ttf", 18)
standardfont = ImageFont.truetype("arial.ttf", 14)
height = 600
width = 600

#Open csv
data = pd.read_csv('Input.csv',header = None,dtype = str)
settings = data.iloc[:7,1]
data = data.iloc[8:,:]
ylabels = data.iloc[1:,0]
ylabels = ylabels.reset_index(drop = True)
timevals = data.iloc[0,:]
[m,n] = data.shape
m = m - 1
while len(colors) < m:
    colors = colors + colors
colors = colors[:m] #Trim colors to match number of rows

fillerframes = int(settings.iloc[4]) #number of frames between each time point given
staticframes = int(settings.iloc[3]) #how long to stay on static points
FPS = int(settings.iloc[2]) #Frames per second in final video
title = settings.iloc[0]
xlabel = settings.iloc[1]
rightnums = settings.iloc[5] #Option for numbers displayed to the right of bars
numbars = int(settings.iloc[6])
titlesize = titlefont.getsize(title)
xlabelsize = standardfont.getsize(xlabel)

#Determine font size/locations for Y-Labels
ylabelsize = np.empty([m,2])
for i in range(m):
    ylabelsize[i,:] = standardfont.getsize(ylabels.iloc[i])

#Get time values
timelabel = timevals[0] + ': '
timevals = timevals[1:]
timelabeldist = standardfont.getsize(timelabel)
timelabeldist = timelabeldist[0]

#Determine widths of bars
#bar_separation = np.floor(450 / (m))
#bar_thickness = np.floor(bar_separation*0.5)
bar_separation = np.floor(450 / (numbars))
bar_thickness = np.floor(bar_separation*0.5)

#See if temporary folder exists. If so, delete it
dircheck = os.path.exists('Images_AnimatedBarGraph')
if dircheck == True:
    shutil.rmtree('Images_AnimatedBarGraph')
    
#Make Temporary Folder for Frames    
os.mkdir('Images_AnimatedBarGraph')    

#Scale bar sizes so that 1 is max value / full bar
data_bar = data.iloc[1:,1:].astype(float)
data_bar = data_bar / np.max(np.max(data_bar))

#X-Axis labels / positions
xmax = np.max(np.max(data.iloc[1:,1:]))
xmax_tick =  np.round(xmax,1-(1+int((np.log10(abs(xmax))))))
xticks = np.dot([0.25,0.5,0.75,1],xmax_tick)
xtick_locations = np.divide(xticks,xmax)
xtick_locations = xtick_locations*400 + 100

#determine positions
orderinglist = list(range(m))
positions = np.zeros([m,n-1])
for i in range(n-1):
    temp = (data_bar.iloc[:,i])
    temp = temp.sort_values(ascending = False)
    tempindex = temp.index.tolist()
    templist = pd.DataFrame([tempindex,orderinglist]).T
    templist = templist.sort_values(0,ascending = True)
    positions[:,i] = templist.iloc[:,1]
    del temp

#Make first static portion
for i in range(staticframes):
    if i == 0:
        X_final = pd.DataFrame(data_bar.iloc[:,0])
        Y_final = pd.DataFrame(positions[:,0])
        T_final = pd.Series(timevals.iloc[0])
    else:
        X_final = pd.concat([X_final,data_bar.iloc[:,0]],axis = 1,ignore_index = True)
        Y_final = pd.concat([Y_final,pd.DataFrame(positions[:,0])],axis = 1,ignore_index = True)
        T_final = pd.concat([T_final,pd.Series(timevals.iloc[0])])
        
#determine intermediate locations. Make matrices for x and y values at all times
for i in range(n-2):
    x_starts = data_bar.iloc[:,i]
    y_starts = positions[:,i]
    x_ends = data_bar.iloc[:,i+1]
    y_ends = positions[:,i+1]
    for j in range(fillerframes):
        x_temp = x_starts*((fillerframes - j)/fillerframes) + x_ends*((j)/fillerframes)
        y_temp = y_starts*((fillerframes - j)/fillerframes) + y_ends*((j)/fillerframes)
        X_final = pd.concat([X_final,pd.DataFrame(x_temp)],axis = 1,ignore_index = True)
        Y_final = pd.concat([Y_final,pd.DataFrame(y_temp)],axis = 1,ignore_index = True)
        T_final = pd.concat([T_final,pd.Series(timevals.iloc[i+1])])
    for j in range(staticframes):
        X_final = pd.concat([X_final,data_bar.iloc[:,i+1]],axis = 1,ignore_index = True)
        Y_final = pd.concat([Y_final,pd.DataFrame(positions[:,i+1])],axis = 1,ignore_index = True)
        T_final = pd.concat([T_final,pd.Series(timevals.iloc[i+1])])

Y_final = Y_final*bar_separation+80
X_final = X_final*400+100

[m,num_frames] = Y_final.shape

#From Positions generate graph frames
for i in range(num_frames):
    framenum = str(i)
    while len(framenum) < 5:
        framenum = '0' + framenum
    filename = 'Images_AnimatedBarGraph/' + 'Frame' + framenum + '.png'
    
    img = Image.new('RGB', (width, height), color = (256, 256, 256))
    d = ImageDraw.Draw(img,'RGBA')
    
    for j in range(m):
        if Y_final.iloc[j,i] < 530:
            temp_polygonbound = [(100,Y_final.iloc[j,i]),
                                 (X_final.iloc[j,i],Y_final.iloc[j,i]),
                                 (X_final.iloc[j,i],Y_final.iloc[j,i] + bar_thickness+5),
                                 (100,Y_final.iloc[j,i] + bar_thickness+5)]
            d.polygon(temp_polygonbound,fill = colors[j])
            dispval = str(round(xmax*(X_final.iloc[j,i]-100)/400,0))
            if rightnums == 'TRUE':
                d.text((X_final.iloc[j,i]+3,Y_final.iloc[j,i] + bar_thickness/2 - 5),dispval, fill = colors[j],font = standardfont)
            d.text((100-ylabelsize[j,0],Y_final.iloc[j,i] + bar_thickness/2 - 5), ylabels.iloc[j], fill = colors[j],font = standardfont)
    lazy_bottomcover = [(0,530),(600,530),(600,600),(0,600)]
    d.polygon(lazy_bottomcover,fill = (256, 256, 256))
    d.line((100,60) + (100,530), fill=(0,0,0),width = 2)
    d.line((100,530) + (500,530), fill=(0,0,0),width = 2)
    
    d.text(((600-titlesize[0])/2,titlesize[1]), title, fill=(0,0,0),font = titlefont)
    d.text(((600-xlabelsize[0])/2,560), xlabel, fill=(0,0,0),font = standardfont)
    d.text((20,20), timelabel, fill=(0,0,0),font = standardfont)
    d.text((timelabeldist+22,20), str(T_final.iloc[i]), fill=(0,0,0),font = standardfont)
    
    
    for j in range(4):
        d.line((xtick_locations[j],530) + (xtick_locations[j],535), fill=(0,0,0),width = 2)
        d.text((xtick_locations[j]-5,540), str(xticks[j]), fill=(0,0,0),font = standardfont)
    
    img.save(filename)
    
numframes = i + 1

#Make Video from Frames
framelist = os.listdir('Images_AnimatedBarGraph')
seconds = numframes/FPS

fourcc = VideoWriter_fourcc(*'MP42')
video = VideoWriter('./Graph.AVI', fourcc, float(FPS), (width, height))

for _ in range(numframes):
    filename = 'Images_AnimatedBarGraph/' + framelist[_]
    frame = cv2.imread(filename)
    
    video.write(frame)

video.release()

#Delete Directory
shutil.rmtree('Images_AnimatedBarGraph')
    