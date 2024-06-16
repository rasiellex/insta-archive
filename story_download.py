import random
import time
import traceback

import instaloader
import pytz
import yaml
from loguru import logger

from helper_functions import send_to_discord_webhook

if __name__ == "__main__":
    log_file = "insta-download.log"
    logger.add(log_file)
    logger.info("Start process: Download Instagram stories.")

    # delay = random.randint(0, 60)
    # logger.info(f"Process will sleep for {delay} seconds.")
    # time.sleep(delay)

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["INSTA"]["USER"]
    pw = config["INSTA"]["PASSWORD"]
    data_path = config["DATA_PATH"]
    instagram_profile = config["INSTAGRAM_PROFILE"]
    user_timezone = config["USER_TIMEZONE"]
    webhook_discord = config["DISCORD"]["WEBHOOK_INSTA_DOWNLOAD"]
    webhook_discord_alert = config["DISCORD"]["WEBHOOK_ALERT"]

    try:
        loader = instaloader.Instaloader(
            download_video_thumbnails=False
        )
        try:
            logger.info("Try to login via session file.")
            loader.load_session_from_file(username=user, filename="session_instaloader")
            logger.info(f"Successfully logged in to account: {user} via session file.")
            loader.test_login()
        except:
            logger.info("Login via session file failed. Session file expired.")
            try:
                logger.info("Login in via credentials and save session file.")
                loader.login(user=user, passwd=pw)
                loader.save_session_to_file("session_instaloader")
                loader.test_login()
                logger.info(f"Successfully logged in to account: {user} via credentials and saved session file to disk.")
            except Exception as e:
                raise

        # Retrieve the profile metadata
        profile = instaloader.Profile.from_username(loader.context, instagram_profile)

        stories = loader.get_stories(userids=[profile.userid])

        downloaded_items = 0

        for story in stories:

            num_stories = story.itemcount
            logger.info(f"Number of stories found: {num_stories}")
            for item in story.get_items():
                local_timestamp = item.date_utc

                # Convert it to GMT-6
                denver_timezone = pytz.timezone('US/Mountain')
                local_timestamp = local_timestamp.astimezone(denver_timezone)

                date = local_timestamp.strftime('%Y-%m-%d-%H-%M-%S')
                dir_name = local_timestamp.strftime('%Y-%m-%d')

                loader.dirname_pattern = f"{data_path}{dir_name}/"
                loader.filename_pattern = f'{date}'
                loader.download_storyitem(item, target='')

                downloaded_items += 1
                logger.info(f"Download progress: {downloaded_items} of {num_stories} items downloaded.")
                delay = random.randint(4, 10)
                time.sleep(delay)
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
            [send_to_discord_webhook(webhook_url=webhook_discord, input_text=line) for line in log_content
             if line != "\n"]
