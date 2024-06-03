import os
import time
from datetime import datetime, timedelta
from glob import glob

import tweepy
import yaml
from loguru import logger
import traceback

from helper_functions import send_to_discord_webhook

if __name__ == "__main__":
    log_file = "twitter_upload.log"
    logger.add(log_file)
    start_time = time.time()
    logger.info("Start process: Upload to Twitter.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["TWITTER"]["USER"]
    consumer_key = config["TWITTER"]["CONSUMER_KEY"]
    consumer_secret = config["TWITTER"]["CONSUMER_SECRET"]
    access_token = config["TWITTER"]["ACCESS_TOKEN"]
    access_token_secret = config["TWITTER"]["ACCESS_TOKEN_SECRET"]
    bearer_token = config["TWITTER"]["BEARER_TOKEN"]

    data_path = config["DATA_PATH"]
    user_timezone = config["USER_TIMEZONE"]
    instagram_caption = config["CAPTION"]
    webhook_discord = config["DISCORD"]["WEBHOOK_TWITTER_UPLOAD"]
    webhook_discord_alert = config["DISCORD"]["WEBHOOK_ALERT"]

    try:
        # Convert local time to destination time
        local_timestamp_org = datetime.now()
        local_timestamp = local_timestamp_org - timedelta(hours=24)

        date_dir = local_timestamp.strftime('%Y-%m-%d')
        date_caption = local_timestamp.strftime('%d.%m.%Y')
        logger.info(f"Local timestamp minus 24 hours: {date_dir}")

        dir_path = f"{data_path}{date_dir}"

        fp_images = glob(f"{dir_path}/*.jpg")
        fp_videos = glob(f"{dir_path}/*.mp4")
        fp_images = [file for file in fp_images if "edit" not in file]

        fp_media = fp_images + fp_videos
        fp_media.sort()
        num_images = len(fp_images)
        num_videos = len(fp_videos)
        num_media = len(fp_media)

        logger.info(
            f"Select media files from date folder: {dir_path}. Found {num_media} media files. "
            f"Images: {num_images} | Videos: {num_videos}")

        if num_media > 0:
            logger.info("Login in to Twitter account.")
            auth = tweepy.OAuthHandler(consumer_key=consumer_key, consumer_secret=consumer_secret,
                                       access_token=access_token, access_token_secret=access_token_secret)
            api = tweepy.API(auth=auth)

            client = tweepy.Client(
                consumer_key=consumer_key, consumer_secret=consumer_secret,
                access_token=access_token, access_token_secret=access_token_secret
            )

            logger.info("Successfully logged in to account.")

            caption = f"{instagram_caption} | {date_caption}"
            logger.info(f"Caption for Twitter post: {caption}")

            logger.info(f"Start upload to twitter. Total number of posts: {num_media}.")
            for index, file in enumerate(fp_media):
                file_basename = os.path.basename(file)
                logger.info(f"Start upload for file {file_basename}.")
                media = api.media_upload(file)

                response = client.create_tweet(
                    text=caption,
                    media_ids=[media.media_id]
                )
                logger.success(f"Successfully uploaded media file {file_basename}. "
                               f"Upload status: {index + 1}/{num_media}. \n "
                               f" Link to post: https://twitter.com/{user}/status/{response.data['id']}")

        total_time = int(round((time.time() - start_time)))
        total_time = str(timedelta(seconds=total_time))
        logger.info(f"Finished process: Upload to Twitter. End script. Elapsed time: {total_time}")


    except Exception as e:
        logger.info("Script failed.")
        logger.exception(e)
        error_message = traceback.format_exc()
        send_to_discord_webhook(webhook_url=webhook_discord_alert,
                                input_text="ERROR: Twitter upload script failed.")
        send_to_discord_webhook(webhook_url=webhook_discord_alert,
                                input_text=error_message)

    finally:
        with open(log_file, 'r') as file:
            log_content = file.readlines()
            [send_to_discord_webhook(webhook_url=webhook_discord, input_text=line) for line in log_content]
