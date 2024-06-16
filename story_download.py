import random
import time
import traceback

import instaloader
import pytz
import yaml
from loguru import logger
from instagrapi import Client
import os

from helper_functions import send_to_discord_webhook

if __name__ == "__main__":
    log_file = "insta-download.log"
    logger.add(log_file)
    logger.info("Start process: Download Instagram stories.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    users = config["INSTA"]["USER"]
    pw = config["INSTA"]["PASSWORD"]
    data_path = config["DATA_PATH"]
    instagram_profile = "gryffin"
    user_timezone = config["USER_TIMEZONE"]
    webhook_discord = config["DISCORD"]["WEBHOOK_INSTA_DOWNLOAD"]
    webhook_discord_alert = config["DISCORD"]["WEBHOOK_ALERT"]

    try:
        user = random.choice(list(users.values()))

        cl = Client()

        # adds a random delay between 1 and 3 seconds after each request
        cl.delay_range = [3, 10]
        try:
            logger.info("Try to login via session file.")
            cl.load_settings(f"session_instagrapi_{user}")
            cl.login(user, pw)
            logger.info(f"Successfully logged in to account: {user} via session file.")
        except:
            logger.info("Login via session file failed. Session file expired.")
            try:
                logger.info("Login in via credentials and save session file.")
                cl.login(user, pw)
                cl.dump_settings(f"session_instagrapi_{user}")
                logger.info(f"Successfully logged in to account: {user} via credentials and saved session file to disk.")
            except Exception as e:
                logger.exception(e)

            user_info = cl.user_info_by_username_v1('gryffin')  # user_info_by_username_v1

            user_id = user_info.pk
            user_stories = cl.user_stories(user_id=user_id)
            num_stories = len(user_stories)
            logger.info(f"Number of stories found: {num_stories}")

            downloaded_items = 0

            for story in user_stories:
                local_timestamp = story.taken_at
                local_timestamp = local_timestamp.replace(tzinfo=None)

                # Convert it to GMT-6
                denver_timezone = pytz.timezone('US/Mountain')
                local_timestamp = local_timestamp.astimezone(denver_timezone)

                date = local_timestamp.strftime('%Y-%m-%d-%H-%M-%S')
                dir_name = local_timestamp.strftime('%Y-%m-%d')

                media_type = story.media_type
                if media_type == 1:
                    extension = ".jpg"
                else:
                    extension = ".mp4"

                data_path = "test/"
                dirname = f"{data_path}{dir_name}/"
                filename = f'{date}'

                if not os.path.exists(dirname):
                    os.makedirs(dirname)

                if os.path.isfile(dirname + filename + extension):
                    continue

                cl.story_download(story.pk, filename=filename, folder=dirname)
                downloaded_items += 1
                logger.info(f"Download progress: {downloaded_items} of {num_stories} items downloaded.")

            logger.success(f"Successfully downloaded {num_stories} stories.")


            if downloaded_items == 0:
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
            [send_to_discord_webhook(webhook_url=webhook_discord, input_text=line) for line in log_content]