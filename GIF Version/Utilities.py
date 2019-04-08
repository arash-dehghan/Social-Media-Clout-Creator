import praw
import urllib.request
import subprocess
import shutil
import os
import tweepy
import datetime
import random
from moviepy.editor import VideoFileClip
import csv
import contextlib
import pandas as pd
from tweepy import OAuthHandler
from urllib.request import urlopen
import requests
import moviepy.editor as mp
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def File_Exists(filepath):
    """
    Return whether file exists in certain path
    """
    file_exists = os.path.exists(filepath)
    return file_exists

def Return_Length(clip):
    """
    Return length of the clip
    """
    vid = VideoFileClip(clip)
    return vid.duration

def RetrieveAndMerge(video_file,filename):
    """
    Merge video and audio
    """
    r = requests.get(video_file, stream=True)
    if r.status_code == 200:
        with open('videofile.gif', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    clip = mp.VideoFileClip("videofile.gif")
    clip.write_videofile("myvideo.mp4")
    #return theresaudio

def RandomMusic():
    """
    Randomly select a file from our BackgroundMusic folder, and return the path to it so that we can merge it with the video we have
    """
    from os import listdir
    from os.path import isfile, join
    import random

    mypath = "BackgroundMusic"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for filee in onlyfiles:
        if filee[0] == ".":
            onlyfiles.remove(filee)
    random_song_index = random.randint(0,len(onlyfiles) - 1)
    return mypath + "/" + str(onlyfiles[random_song_index])

def Thumbnail():
    """
    Screenshot/Grab first frame from video and save this as the thumbnail
    """
    import cv2
    vidcap = cv2.VideoCapture('myvideo.mp4')
    success,image = vidcap.read()
    count = 0
    success = True
    cv2.imwrite("thumbnail.jpg", image)


def Get_Videos():
    """
    Access and download the appropriate videos from our desired subreddit, add them to our CSV file, concatenate the video and audio of the clip, and store the clips metadata
    """
    reddit = praw.Reddit(client_id = 'YOUR CLIENT ID', client_secret = 'YOUR CLIENT SECRET', username = 'YOUR USERNAME', password = 'YOUR PASSWORD', user_agent = 'YOUR USER AGENT')
    subreddit = reddit.subreddit('YOUR DESIRED SUBREDDIT')
    hot_python = subreddit.hot(limit = INTEGER OF NUMBER OF POSTS TO PARSE THROUGH)

    #Write data to csv database
    MyFolder = 'Video_data.csv'
    does_it_exist = File_Exists(MyFolder)
    with open(MyFolder,'a') as resultFile:
        #If file doesn't exist, create it
        if does_it_exist == False:
            #Create headers for the data we are collecting
            templist = ['Reddit_Username', 'Reddit_Caption', 'Reddit_Filename']
            wr = csv.writer(resultFile, dialect='excel')
            #Write the row of header data into the csv file
            wr.writerow(templist)

    picked_one = False
    for submission in hot_python:
        if picked_one == False:
            sub_length = len(str(submission.title)+' (Via: '+str(submission.author)+')')
            df = pd.read_csv('Video_data.csv')
            not_in_dataframe = df[df['Reddit_Filename'].isin([str(submission.name)])].empty
            try:
                if not submission.stickied and not_in_dataframe == True and submission.ups >= 2000:
                    video_file = submission.media['oembed']['thumbnail_url']
                    filename = submission.name
                    title = submission.title
                    author = submission.author

                    do_it = RetrieveAndMerge(video_file,filename)

                    if os.path.exists('myvideo.mp4'):
                        #Check if file with reddit data exists
                        does_it_exist = File_Exists(MyFolder)
                        with open(MyFolder,'a') as resultFile:
                            #If file doesn't exist, create it
                            if does_it_exist == False:
                                #Create headers for the data we are collecting
                                templist = ['Reddit_Username', 'Reddit_Caption','Reddit_Filename']
                                wr = csv.writer(resultFile, dialect='excel')
                                #Write the row of header data into the csv file
                                wr.writerow(templist)
                            mylist = [author,title,filename]
                            wr = csv.writer(resultFile, dialect='excel')
                            wr.writerow(mylist)
                        if Return_Length('myvideo.mp4') <= 59:
                            InstagramPoster(title,author)
                        #Check if they exist and if they do, delete the videofile.mp4 and audiofile.m4a
                        if os.path.exists('myvideo.mp4'):
                            os.remove('myvideo.mp4')
                        if os.path.exists('thumbnail.jpg'):
                            os.remove('thumbnail.jpg')
                        if os.path.exists('videofile.gif'):
                            os.remove('videofile.gif')
                        if os.path.exists('myaudio.m4a'):
                            os.remove('myaudio.m4a')
                        if os.path.exists('videotopost.mp4'):
                            os.remove('videotopost.mp4')
                        picked_one = True
            except Exception as e:
                print(e)
                print(submission.title)

def AddMusic():
    """
    Add the background music we selected to our soundless GIF
    """
    length = Return_Length("myvideo.mp4")
    length = int(length)
    ffmpeg_extract_subclip(RandomMusic(), 0, length, targetname="myaudio.m4a")
    cmd = 'ffmpeg -i myvideo.mp4 -i myaudio.m4a -c:v copy -c:a aac -bsf:v h264_mp4toannexb -strict experimental videotopost.mp4'
    subprocess.call(cmd, shell=True)


def InstagramPoster(title, author):
    """
    Post to instagram and update the CSV file accordingly
    """
    import requests
    import json
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver
    import time
    from random import randint
    from InstagramAPI import InstagramAPI

    InstagramAPI = InstagramAPI("YOUR USERNAME", "YOUR PASSWORD")
    InstagramAPI.login()
    Thumbnail()
    AddMusic()
    mypath = "videotopost.mp4"
    photoPath = "thumbnail.jpg"
    mycaption = "ENTER YOUR CAPTION HERE"
    try:
        InstagramAPI.uploadVideo(mypath, thumbnail=photoPath, caption=mycaption)

    except Exception as e:
        print(e)
        print("Error...")
        exit(0)

Get_Videos()
