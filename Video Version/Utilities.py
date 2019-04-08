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


def Return_Length(clip):
    """
    Return the length of the clip selected
    """
    vid = VideoFileClip(clip)
    return vid.duration

def Check_Length(clip):
    """
    Make sure that the length of the clip is a minute or less (So it can be posted as one video onto Instagram)
    """
    vid = VideoFileClip(clip)
    if vid.duration <= 59:
        return True
    else:
        return False

def Number_of_Files(path):
    """
    Return the number of files in a directory
    """
    numfiles = len([f for f in os.listdir(path) if f[0] != '.'])
    return numfiles

def DateValue():
    """
    Return a string which contains a concatenation of the year, month, day, and hour. This is used to add onto the YouTube video name we store (To create unique video labels)
    """
    now = datetime.datetime.now()
    mystring = str(now.year)+str(now.month)+str(now.day)+str(now.hour)
    return mystring


def Ready_For_YouTube(mylist):
    """
    Check to make sure that the concatenation of the number of videos not posted yet to YouTube are greater than 480 seconds in length
    """
    total_length = 0
    for item in mylist:
        total_length += item
    if total_length>=480:
        return True
    else:
        return False

def RetrieveAndMerge(video_file,audio_file,filename):
    """
    Since Reddit stores video and audio seperately (DASH method), we grab the video and audio portion of the clip seperately and merge them into a single audio-playing video here
    """
    r = requests.get(video_file, stream=True)
    if r.status_code == 200:
        with open('videofile.mp4', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    r2 = requests.get(audio_file, stream=True)
    if r2.status_code == 200:
        with open('audiofile.m4a', 'wb') as f:
            r2.raw.decode_content = True
            shutil.copyfileobj(r2.raw, f)
    if os.path.exists('audiofile.m4a'):
        theresaudio = True
        cmd = 'ffmpeg -i videofile.mp4 -i audiofile.m4a -c:v copy -c:a aac -bsf:v h264_mp4toannexb -strict experimental MyVideos/Videos/'+filename+".mp4"
        subprocess.call(cmd, shell=True)
    else:
        theresaudio = False
    return theresaudio

def File_Exists(filepath):
    """
    Return whether or not the file exists
    """
    file_exists = os.path.exists(filepath)
    return file_exists

def List_of_Videos():
    """
    Returns a list of video names in a certain file
    """
    mypath = 'MyVideos/Videos'
    f = []
    for (dirpath, dirnames, filenames) in os.walk(mypath):
        f.extend(filenames)
    f.pop(0)
    return f

def CreateSmall_CSV(name,description,credit):
    """
    Create a CSV file where we can store all of our data
    """
    MyFolder = 'MyVideos/Tweet_Taken.csv'
    does_it_exist = File_Exists(MyFolder)
    with open(MyFolder,'a') as resultFile:
        if does_it_exist == False:
            templist = ['Name','Description','Credit']
            wr = csv.writer(resultFile, dialect='excel')
            wr.writerow(templist)
        mylist = [name,description,credit]
        wr = csv.writer(resultFile, dialect='excel')
        wr.writerow(mylist)

def Thumbnail(video):
    """
    Screenshots/Captures the first frame from our video file and saves it as thumbnail.jpg (This is used as a thumbnail for the video)
    """
    import cv2
    vidcap = cv2.VideoCapture('MyVideos/Videos/'+str(video)+'.mp4')
    success,image = vidcap.read()
    count = 0
    success = True
    cv2.imwrite("thumbnail.jpg", image)

def Tweet():
    """
    Tweets the most recent video which has not been posted to Twitter yet
    """
    df = pd.read_csv('MyVideos/Video_data.csv')
    posted_df = df.loc[df['Posted_To_Twitter'] == False]
    if len(posted_df) != 0:
        name = posted_df['Reddit_Filename'].iloc[0]
        description = posted_df['Reddit_Caption'].iloc[0]
        credit = posted_df['Reddit_Username'].iloc[0]
        CreateSmall_CSV(name,description,credit)
        try:
            os.system('python3 async-upload.py')
            if os.path.exists('MyVideos/Tweet_Taken.csv'):
                os.remove('MyVideos/Tweet_Taken.csv')
            df.loc[df['Reddit_Filename'] == name, 'Posted_To_Twitter'] = True
            df.to_csv('MyVideos/Video_data.csv', index=False)
        except:
            print("Tweeting Error!")

def Get_Videos():
    """
    Access and download the appropriate videos from our desired subreddit, add them to our CSV file, concatenate the video and audio of the clip, and store the clips metadata
    """
    reddit = praw.Reddit(client_id = 'YOUR CLIENT ID', client_secret = 'YOUR CLIENT SECRET', username = 'YOUR USERNAME', password = 'YOUR PASSWORD', user_agent = 'YOUR USER AGENT')
    subreddit = reddit.subreddit('YOUR DESIRED SUBREDDIT')
    hot_python = subreddit.hot(limit = INTEGER VALUE OF NUMBER OF POSTS TO PARSE)

    MyFolder = 'MyVideos/Video_data.csv'
    does_it_exist = File_Exists(MyFolder)
    with open(MyFolder,'a') as resultFile:
        if does_it_exist == False:
            templist = ['Reddit_Username', 'Reddit_Caption', 'Reddit_Filename','Reddit_Length', 'Posted_To_YouTube', 'Posted_To_Instagram', 'Posted_To_Twitter']
            wr = csv.writer(resultFile, dialect='excel')
            wr.writerow(templist)
    picked_one = False
    for submission in hot_python:
        if picked_one == False:
            sub_length = len(str(submission.title)+' (Via: '+str(submission.author)+')')
            df = pd.read_csv('MyVideos/Video_data.csv')
            not_in_dataframe = df[df['Reddit_Filename'].isin([str(submission.name)])].empty
            if not submission.stickied and submission.is_video == True and Check_Length(submission.media['reddit_video']['scrubber_media_url']) == True and sub_length <=280 and not_in_dataframe == True and submission.ups >= 250:

                mystring = submission.media['reddit_video']['scrubber_media_url']
                video_file = submission.media['reddit_video']['fallback_url']
                audio_file = mystring.replace("DASH_240","audio")

                filename = submission.name
                title = submission.title
                author = submission.author
                length = Return_Length(submission.media['reddit_video']['scrubber_media_url'])

                do_it = RetrieveAndMerge(video_file,audio_file,filename)

                if do_it == True:
                    does_it_exist = File_Exists(MyFolder)
                    with open(MyFolder,'a') as resultFile:
                        if does_it_exist == False:
                            templist = ['Reddit_Username', 'Reddit_Caption', 'Reddit_Filename','Reddit_Length', 'Posted_To_YouTube', 'Posted_To_Instagram', 'Posted_To_Twitter']
                            wr = csv.writer(resultFile, dialect='excel')
                            wr.writerow(templist)
                        mylist = [author,title,filename,length,False,False,False]
                        wr = csv.writer(resultFile, dialect='excel')
                        wr.writerow(mylist)
                    if os.path.exists('videofile.mp4'):
                        os.remove('videofile.mp4')
                    if os.path.exists('audiofile.m4a'):
                        os.remove('audiofile.m4a')
                    picked_one = True

def YouTubeIt():
    """
    Check to see if we have enough content saved up, if so, concatenate all of our videos and post them onto YouTube with our desired title and description, giving credit to all users. As well, we update our CSV file to say that the videos have been posted to YouTube
    """
    df = pd.read_csv('MyVideos/Video_data.csv')
    posted_df = df.loc[df['Posted_To_YouTube'] == False]
    nameslist = []
    lengthslist = []
    intslist = []
    mykeeperlist = []
    userslist = []
    descriptionlist = []
    count = 0
    mystring = ''
    if len(posted_df) != 0:
        for item in range(0,len(posted_df)):
            name = posted_df['Reddit_Filename'].iloc[item]
            author = posted_df['Reddit_Username'].iloc[item]
            length = posted_df['Reddit_Length'].iloc[item]
            description = posted_df['Reddit_Caption'].iloc[item]
            nameslist.append(name)
            lengthslist.append(length)
            userslist.append(author)
            descriptionlist.append(description)
        if Ready_For_YouTube(lengthslist) == True:
            prefix = 'MyVideos/Videos/'
            for name in nameslist:
                string = 'ffmpeg -i '+prefix+name+'.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts intermediate'+str(count)+'.ts'
                intslist.append('intermediate'+str(count)+'.ts')
                mykeeperlist.append('intermediate'+str(count)+'.ts')
                os.system(string)
                count+=1
            while len(intslist) != 1:
                if os.path.exists('output.mp4'):
                    os.remove('output.mp4')
                mystring = 'ffmpeg -i "concat:'+intslist[0]+'|'+intslist[1]+'" -c copy -bsf:a aac_adtstoasc output.mp4'
                os.system(mystring)
                intslist.pop(0)
                intslist.pop(0)
                if os.path.exists('output.ts'):
                    os.remove('output.ts')
                os.system('ffmpeg -i output.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts output.ts')
                intslist = ['output.ts']+intslist
            if os.path.exists('output.ts'):
                os.remove('output.ts')
            newname = 'YouTubeVideo'+DateValue()+".mp4"
            os.rename("output.mp4", "MyVideos/YouTube Videos/"+newname)
            for value in mykeeperlist:
                if os.path.exists(value):
                    os.remove(value)
            video_number = int(Number_of_Files("MyVideos/YouTube Videos"))
            my_filepath = "MyVideos/YouTube Videos/"+newname
            my_filetitle = "YOUR VIDEO TITLE"+str(video_number)
            my_description = "YOUR VIDEO DESCRIPTION"
            user_counter = 1
            for user in userslist:
                my_description += 'Clip '+str(user_counter)+' Via: '+user+'\n'
                user_counter +=1
            os.system('python3 YouTube_Upload.py --file="'+my_filepath+'" --title="'+my_filetitle+'" --description="'+my_description+'" --keywords="YOUR KEYWORDS" --category="YOUR CATEGORY" --privacyStatus="public"')

            for name in userslist:
                df.loc[df['Reddit_Username'] == name, 'Posted_To_YouTube'] = True
            df.to_csv('MyVideos/Video_data.csv', index=False)
        else:
            print("Video too short")

def InstagramPoster(video,description,credit):
    """
    Posts the video onto Instagram with our desired description and thumbnail
    """
    import requests
    import json
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver
    import time
    from random import randint
    from InstagramAPI import InstagramAPI

    InstagramAPI = InstagramAPI("YOUR INSTAGRAM USERNAME", "YOUR PASSWORD")
    InstagramAPI.login()
    mypath = 'MyVideos/Videos/'+video+'.mp4'
    photoPath = "thumbnail.jpg"
    mycaption = description + " (Via: " + credit + ")\n\n.\n.\n.\n.\n.\n.\nYOUR HASHTAGS HERE"
    try:
        InstagramAPI.uploadVideo(mypath, thumbnail=photoPath, caption=mycaption)
        print("It should be posted")

    except Exception as e:
        print(e)
        print("Error...")
        exit(0)

def Insta():
    """
    Update our CSV file to show that our video has been posted and post the video to Instagram
    """
    df = pd.read_csv('MyVideos/Video_data.csv')
    posted_df = df.loc[df['Posted_To_Instagram'] == False]
    if len(posted_df) != 0:
        name = posted_df['Reddit_Filename'].iloc[0]
        description = posted_df['Reddit_Caption'].iloc[0]
        credit = posted_df['Reddit_Username'].iloc[0]
        Thumbnail(name)
        InstagramPoster(name,description,credit)
        df.loc[df['Reddit_Filename'] == name, 'Posted_To_Instagram'] = True
        df.to_csv('MyVideos/Video_data.csv', index=False)

def Eraser():
    """
    Finds all video files that have been posted both to Instagram and YouTube and deletes them from our computer
    """
    df = pd.read_csv('MyVideos/Video_data.csv')
    posted_df = df.loc[df['Posted_To_Instagram'] == True]
    postedfinal = posted_df.loc[posted_df['Posted_To_YouTube'] == True]
    for item in range(0,len(postedfinal)):
        name = postedfinal['Reddit_Filename'].iloc[item]
        filename = 'MyVideos/Videos/'+str(name)+'.mp4'
        if os.path.exists(filename):
            os.remove(filename)
