import os
import random
import time
import traceback

import pytz
import yaml
from instagrapi import Client
from loguru import logger

from helper_functions import send_to_discord_webhook

if __name__ == "__main__":
    log_file = "insta-download.log"
    logger.add(log_file)
    logger.info("Start process: Download Instagram stories.")

    delay = random.randint(0, 60)
    logger.info(f"Process will sleep for {delay} seconds.")
    time.sleep(delay)

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["INSTA"]["USER"]
    pw = config["INSTA"]["PASSWORD"]
    data_path = config["DATA_PATH"]
    instagram_profile = config["INSTAGRAM_PROFILE"]
    profile_id = config["INSTAGRAM_PROFILE_ID"]
    user_timezone = config["USER_TIMEZONE"]
    webhook_discord = config["DISCORD"]["WEBHOOK_INSTA_DOWNLOAD"]
    webhook_discord_alert = config["DISCORD"]["WEBHOOK_ALERT"]

    session_filename_user = user.replace('.', '_')
    session_filename = f"session_instagrapi_{session_filename_user}.json"

    try:

        cl = Client()
        cl.delay_range = [3, 10]

        try:
            logger.info("Try to login via session file.")
            cl.load_settings(session_filename)
            cl.login(user, pw)
            cl.get_timeline_feed()
            logger.info(f"Successfully logged in to account: {user} via session file.")
        except:
            logger.info("Login via session file failed. Session file expired.")
            try:
                logger.info("Login in via credentials and save session file.")
                cl.login(user, pw)
                cl.dump_settings(session_filename)
                logger.info(f"Successfully logged in to account: {user} via credentials and saved session file to disk.")
            except Exception as e:
                logger.exception(e)

            # user_info = cl.user_info_by_username_v1(instagram_profile)  # user_info_by_username_v1
            # user_id = user_info.pk

        logger.info(f"Fetch stories from user {instagram_profile}.")
        user_stories = cl.user_stories(user_id=profile_id)
        num_stories = len(user_stories)
        logger.info(f"Number of stories found: {num_stories}")

        downloaded_items = 0
        skipped_items = []

        for story in user_stories:
            utc_timestamp = story.taken_at

            # Convert it to GMT-6
            denver_timezone = pytz.timezone('US/Mountain')
            local_timestamp = utc_timestamp.astimezone(denver_timezone)

            date = local_timestamp.strftime('%Y-%m-%d-%H-%M-%S')
            dir_name = local_timestamp.strftime('%Y-%m-%d')

            media_type = story.media_type
            if media_type == 1:
                extension = ".jpg"
            else:
                extension = ".mp4"

            dirname = f"{data_path}{dir_name}/"
            filename = f'{date}'
            filename_with_ext = filename + extension
            file_path = dirname + filename_with_ext

            if not os.path.exists(dirname):
                os.makedirs(dirname)

            if os.path.isfile(file_path):
                logger.info(f"File already exists. Skip file: {file_path}")
                skipped_items.append(filename_with_ext)
                continue

            cl.story_download(story.pk, filename=filename, folder=dirname)
            downloaded_items += 1
            logger.info(f"Downloaded story: {file_path}. Download progress: {downloaded_items}/{num_stories}")

        logger.success(f"Successfully downloaded {downloaded_items}/{num_stories} stories. "
                       f"Skipped files ({len(skipped_items)}): {', '.join(skipped_items)}")


        if downloaded_items == 0 and len(skipped_items) == 0:
            logger.info("No stories found.")
        logger.info("Finished process: Download Instagram stories. End script.")

    except Exception as e:
        logger.info("Script failed.")
        logger.exception(e)
        error_message = traceback.format_exc()
        send_to_discord_webhook(webhook_url=webhook_discord_alert,
                                input_text="ERROR: Instagram download script failed.")
        send_to_discord_webhook(webhook_url=webhook_discord_alert,
                                input_text=error_message)

    finally:
        with open(log_file, 'r') as file:
            log_content = file.readlines()
            [send_to_discord_webhook(webhook_url=webhook_discord, input_text=line) for line in log_content
             if line != "\n"]
