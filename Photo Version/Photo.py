import praw
import pandas as pd
from urllib.request import urlopen
import requests
import shutil
import os
import csv
import os, sys
from PIL import Image

def File_Exists(filepath):
    """
    Simple function to check if file exists, overkill? Probably. Oh Well.
    """
    file_exists = os.path.exists(filepath)
    return file_exists

def Get_Photo():
    """
    Get_Photo function signs into reddit, goes to your selected subreddit, and grabs data regarding a selected number of posts. If a certain post meets the required criteria, then it downloads, writing it into the database.
    """
    reddit = praw.Reddit(client_id = 'YOUR REDDIT CLIENT ID', client_secret = 'YOUR REDDIT CLIENT SECRET', username = 'YOUR USERNAME', password = 'YOUR PASSWORD', user_agent = 'YOUR USER AGENT')
    subreddit = reddit.subreddit('SUBREDDIT YOU WANT TO PARSE THROUGH')
    hot_python = subreddit.hot(limit = INTEGER OF NUMBER OF POSTS TO SWIFT THROUGH)

    MyFolder = 'Photo_data.csv'
    does_it_exist = File_Exists(MyFolder)
    with open(MyFolder,'a') as resultFile:
        if does_it_exist == False:
            templist = ['Reddit_Username', 'Reddit_Caption', 'Reddit_Filename','Posted_To_Instagram']
            wr = csv.writer(resultFile, dialect='excel')
            wr.writerow(templist)
    for submission in hot_python:
        df = pd.read_csv('Photo_data.csv')
        not_in_dataframe = df[df['Reddit_Filename'].isin([str(submission.name)])].empty
        if not submission.stickied and not_in_dataframe == True:
            if str(submission.url[-3:]) == 'jpg' or str(submission.url[-3:]) == 'png':
                filename = submission.name
                author = submission.author
                title = submission.title
                myurl = submission.url

                r = requests.get(str(myurl), stream=True)
                if r.status_code == 200:
                    with open('picture_to_post.jpg', 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)

                #Check if file with reddit data exists
                does_it_exist = File_Exists(MyFolder)
                with open(MyFolder,'a') as resultFile:
                    #If file doesn't exist, create it
                    if does_it_exist == False:
                        #Create headers for the data we are collecting
                        templist = ['Reddit_Username', 'Reddit_Caption', 'Reddit_Filename', 'Posted_To_Instagram']
                        wr = csv.writer(resultFile, dialect='excel')
                        #Write the row of header data into the csv file
                        wr.writerow(templist)
                    mylist = [author,title,filename,False]
                    wr = csv.writer(resultFile, dialect='excel')
                    wr.writerow(mylist)
                break

def InstagramPoster(photo,description,credit):
    import requests
    import json
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver
    import time
    from random import randint
    from InstagramAPI import InstagramAPI
    from PIL import Image

    InstagramAPI = InstagramAPI("YOUR INSTAGRAM USERNAME", "YOUR INSTAGRAM PASSWORD")
    InstagramAPI.login()
    try:
        im = Image.open('picture_to_post.jpg')
        rgb_im = im.convert('RGB')
        rgb_im.save('picture_to_post.jpg')
        mycaption = '"' + description + '"' + " (Via: " + credit + ")\n\n.\n.\n.\n.\n.\n.\n#YOURHASHTAGS"
        try:
            InstagramAPI.uploadPhoto('picture_to_post.jpg', caption=mycaption)

        except Exception as e:
            print(e)
            print("Error...")
            Post()
            exit(0)

    except Exception as e:
        print(e)

def Insta():
    df = pd.read_csv('Photo_data.csv')
    posted_df = df.loc[df['Posted_To_Instagram'] == False]
    if len(posted_df) != 0:
        name = posted_df['Reddit_Filename'].iloc[0]
        description = posted_df['Reddit_Caption'].iloc[0]
        credit = posted_df['Reddit_Username'].iloc[0]
        df.loc[df['Reddit_Filename'] == name, 'Posted_To_Instagram'] = True
        df.to_csv('Photo_data.csv', index=False)
        InstagramPoster(name,description,credit)

def Post():
    Get_Photo()
    Insta()

Post()
