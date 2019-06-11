import praw
import pandas as pd
from urllib.request import urlopen
import requests
import shutil
import os
import csv
import os, sys
from PIL import Image
import re
import io

'------------------------------------------------------------------------'
#Instagram sign-in information
instagram_username = "YOUR USERNAME"
instagram_password = "YOUR PASSWORD"
'------------------------------------------------------------------------'
#Reddit information
reddit_client_id = "YOUR CLIENT ID"
reddit_client_secret = "YOUR CLIENT SECRET"
reddit_username = "USERNAME"
reddit_password = "PASSWORD"
reddit_user_agent = "USERAGENT"
reddit_subreddit = "SUBREDDIT"
reddit_number_of_posts = 50
'------------------------------------------------------------------------'
#Instagram hashtags
insta_hashtags = "#Your #Hashtags #Here"
'------------------------------------------------------------------------'


def calc_resize(max_size, curr_size, min_size=(0, 0)):
    max_width, max_height = max_size or (0, 0)
    min_width, min_height = min_size or (0, 0)

    if (max_width and min_width > max_width) or (max_height and min_height > max_height):
        raise ValueError('Invalid min / max sizes.')

    orig_width, orig_height = curr_size
    if max_width and max_height and (orig_width > max_width or orig_height > max_height):
        resize_factor = min(
            1.0 * max_width / orig_width,
            1.0 * max_height / orig_height)
        new_width = int(resize_factor * orig_width)
        new_height = int(resize_factor * orig_height)
        return new_width, new_height

    elif min_width and min_height and (orig_width < min_width or orig_height < min_height):
        resize_factor = max(
            1.0 * min_width / orig_width,
            1.0 * min_height / orig_height
        )
        new_width = int(resize_factor * orig_width)
        new_height = int(resize_factor * orig_height)
        return new_width, new_height

def resize_image(input_image_path,
                 output_image_path,
                 size):
    original_image = Image.open(input_image_path)
    width, height = original_image.size
    print('The original image size is {wide} wide x {height} '
          'high'.format(wide=width, height=height))

    resized_image = original_image.resize(size)
    width, height = resized_image.size
    print('The resized image size is {wide} wide x {height} '
          'high'.format(wide=width, height=height))
    # resized_image.show()
    resized_image.save(output_image_path)


def calc_crop(aspect_ratios, curr_size):
    try:
        if len(aspect_ratios) == 2:
            min_aspect_ratio = float(aspect_ratios[0])
            max_aspect_ratio = float(aspect_ratios[1])
        else:
            raise ValueError('Invalid aspect ratios')
    except TypeError:
        # not a min-max range
        min_aspect_ratio = float(aspect_ratios)
        max_aspect_ratio = float(aspect_ratios)

    curr_aspect_ratio = 1.0 * curr_size[0] / curr_size[1]
    if not min_aspect_ratio <= curr_aspect_ratio <= max_aspect_ratio:
        curr_width = curr_size[0]
        curr_height = curr_size[1]
        if curr_aspect_ratio > max_aspect_ratio:
            # media is too wide
            new_height = curr_height
            new_width = max_aspect_ratio * new_height
        else:
            # media is too tall
            new_width = curr_width
            new_height = new_width / min_aspect_ratio
        left = int((curr_width - new_width)/2)
        top = int((curr_height - new_height)/2)
        right = int((curr_width + new_width)/2)
        bottom = int((curr_height + new_height)/2)
        return left, top, right, bottom

def is_remote(media):
    if re.match(r'^https?://', media):
        return True
    return False

def prepare_image(img, max_size=(1080, 1350),
                  aspect_ratios=(4.0 / 5.0, 90.0 / 47.0),
                  save_path=None, **kwargs):
    min_size = kwargs.pop('min_size', (320, 167))
    if is_remote(img):
        res = requests.get(img)
        im = Image.open(io.BytesIO(res.content))
    else:
        im = Image.open(img)

    if aspect_ratios:
        crop_box = calc_crop(aspect_ratios, im.size)
        if crop_box:
            im = im.crop(crop_box)

    new_size = calc_resize(max_size, im.size, min_size=min_size)
    if new_size:
        im = im.resize(new_size)

    if im.mode != 'RGB':
        # Removes transparency (alpha)
        im = im.convert('RGBA')
        im2 = Image.new('RGB', im.size, (255, 255, 255))
        im2.paste(im, (0, 0), im)
        im = im2
    if save_path:
        im.save(save_path)

    b = io.BytesIO()
    im.save(b, 'JPEG')
    return b.getvalue(), im.size

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
    global reddit_client_id, reddit_client_secret, reddit_username, reddit_password, reddit_user_agent, reddit_subreddit, reddit_number_of_posts, instagram_username

    reddit = praw.Reddit(client_id = reddit_client_id, client_secret = reddit_client_secret, username = reddit_username, password = reddit_password, user_agent = reddit_user_agent)
    subreddit = reddit.subreddit(reddit_subreddit)
    hot_python = subreddit.hot(limit = reddit_number_of_posts)

    MyFolder = instagram_username+'_Photo_data.csv'
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
        df = pd.read_csv(MyFolder)
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
    # from instagram_private_api import Client, MediaRatios
    # from instagram_private_api_extensions import media
    from InstagramAPI import InstagramAPI
    from PIL import Image

    global instagram_username, instagram_password, insta_hashtags

    # InstagramAPI = Client(instagram_username, instagram_password)
    InstagramAPI = InstagramAPI(instagram_username, instagram_password)
    InstagramAPI.login()

    try:
        mycaption = '"' + description + '"' + " (Via: u/" + credit + ")\n\n.\n.\n.\n.\n.\n.\n"+insta_hashtags
        try:
            post_before = NumberOfPosts(instagram_username)
            # photo_data, photo_size = media.prepare_image('picture_to_post.jpg', aspect_ratios=MediaRatios.standard)
            # InstagramAPI.post_photo(photo_data, photo_size, caption=mycaption)
            image,size = prepare_image('picture_to_post.jpg')
            resize_image('picture_to_post.jpg','new_photo.jpg',size)

            InstagramAPI.uploadPhoto('new_photo.jpg', caption=mycaption)

            if NumberOfPosts(instagram_username) == post_before:
                print("ERROR: It did not post, please try again!")
            else:
                print("Photo posted!")

        except Exception as e:
            print("Error...")
            print(e)
            exit(0)

    except Exception as e:
        print(e)

def Insta():
    global instagram_username
    df = pd.read_csv(instagram_username+'_Photo_data.csv')
    posted_df = df.loc[df['Posted_To_Instagram'] == False]
    if len(posted_df) != 0:
        name = posted_df['Reddit_Filename'].iloc[0]
        description = posted_df['Reddit_Caption'].iloc[0]
        credit = posted_df['Reddit_Username'].iloc[0]
        df.loc[df['Reddit_Filename'] == name, 'Posted_To_Instagram'] = True
        df.to_csv(instagram_username+'_Photo_data.csv', index=False)
        InstagramPoster(name,description,credit)

def Post():
    Get_Photo()
    Insta()

Post()
