import praw
import pandas as pd
from urllib.request import urlopen
import requests
import shutil
import os
import csv
import os, sys
from PIL import Image


'------------------------------------------------------------------------'
#Instagram sign-in information
instagram_username = "INSTAGRAM USERNAME"
instagram_password = "INSTAGRAM PASSWORD"
'------------------------------------------------------------------------'
#Reddit information
reddit_client_id = "YOUR REDDIT CLIENT ID"
reddit_client_secret = "YOUR REDDIT CLIENT SECRET"
reddit_username = "YOUR REDDIT USERNAME"
reddit_password = "YOUR REDDIT PASSWORD"
reddit_user_agent = "YOUR USER AGENT"
reddit_subreddit = "YOUR SUBREDDIT"
reddit_number_of_posts = 50
'------------------------------------------------------------------------'
#Instagram hashtags
insta_hashtags = "#Your #Hashtags #Here"
'------------------------------------------------------------------------'
#Iterations Tracking
max_iterations = 5
global_count = 0
time_to_sleep = 10 #Optimally should be 60
'------------------------------------------------------------------------'



def File_Exists(filepath):
    file_exists = os.path.exists(filepath)
    return file_exists

def NumberOfPosts(username):
    import requests
    from bs4 import BeautifulSoup

    html = requests.get('https://www.instagram.com/{}/'.format(username))
    soup = BeautifulSoup(html.text, 'lxml')
    item = soup.select_one("meta[property='og:description']")

    posts = item.get("content").split(",")[2]
    number_of_posts = posts.split(" ")[1]

    return int(number_of_posts)

def Get_Photo():
    """
    Get_Photo function signs into reddit, goes to your selected subreddit, and grabs data regarding a selected number of posts. If a certain post meets the required criteria, then it downloads, writing it into the database.
    """
    global reddit_client_id, reddit_client_secret, reddit_username, reddit_password, reddit_user_agent, reddit_subreddit, reddit_number_of_posts

    reddit = praw.Reddit(client_id = reddit_client_id, client_secret = reddit_client_secret, username = reddit_username, password = reddit_password, user_agent = reddit_user_agent)
    subreddit = reddit.subreddit(reddit_subreddit)
    hot_python = subreddit.hot(limit = reddit_number_of_posts)

    MyFolder = 'Photo_data.csv'
    does_it_exist = File_Exists(MyFolder)
    with open(MyFolder,'a') as resultFile:
        #If file doesn't exist, create it
        if does_it_exist == False:
            #Create headers for the data we are collecting
            templist = ['Reddit_Username', 'Reddit_Caption', 'Reddit_Filename','Posted_To_Instagram']
            wr = csv.writer(resultFile, dialect='excel')
            #Write the row of header data into the csv file
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
    import time
    from random import randint
    from InstagramAPI import InstagramAPI
    from PIL import Image

    global instagram_username, instagram_password, insta_hashtags, max_iterations, global_count, time_to_sleep

    print("########################################")
    InstagramAPI = InstagramAPI(instagram_username, instagram_password)
    InstagramAPI.login()

    try:
        im = Image.open('picture_to_post.jpg')
        rgb_im = im.convert('RGB')
        rgb_im.save('picture_to_post.jpg')

        mycaption = '"' + description + '"' + " (Via: " + credit + ")\n\n.\n.\n.\n.\n.\n.\n"+insta_hashtags
        try:
            post_before = NumberOfPosts(instagram_username)

            InstagramAPI.uploadPhoto('picture_to_post.jpg', caption=mycaption)
            global_count += 1
            if NumberOfPosts(instagram_username) == post_before:
                if max_iterations != global_count:
                    print("Nothing was posting due to an error, trying next post")
                    time.sleep(time_to_sleep)
                    Post()
                else:
                    print("Max iterations reached! Stopping now!")
            else:
                print("Photo posted!")
                print("########################################")

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
