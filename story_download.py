import random
import time

import instaloader
import pytz
import yaml
from loguru import logger

if __name__ == "__main__":
    logger.add("insta-upload.log")
    logger.info("Start script to download instagram stories.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["USER"]
    pw = config["PASSWORD"]
    data_path = config["DATA_PATH"]
    instagram_profile = config["INSTAGRAM_PROFILE"]
    user_timezone = config["USER_TIMEZONE"]

    loader = instaloader.Instaloader(
        download_video_thumbnails=False
    )

    # If you want to download stories from private profiles, you need to login with your Instagram credentials.
    loader.login(user=user, passwd=pw)

    # Retrieve the profile metadata
    profile = instaloader.Profile.from_username(loader.context, instagram_profile)

    stories = loader.get_stories(userids=[profile.userid])

    for story in stories:
        logger.info(f"Number of stories found: {story.itemcount}")
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

            delay = random.randint(4, 10)
            time.sleep(delay)

    logger.success("Successfully downloaded stories.")
