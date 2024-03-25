import random
import time

import instaloader
import pytz
import yaml
from loguru import logger

if __name__ == "__main__":
    logger.add("insta-archive.log")
    logger.info("Start script to download instagram stories.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["USER"]
    pw = config["PASSWORD"]

    loader = instaloader.Instaloader(
        download_video_thumbnails=False
    )

    # If you want to download stories from private profiles, you need to login with your Instagram credentials.
    loader.login(user=user, passwd=pw)

    # Define the profile name
    profile_name = "illenium"

    # Retrieve the profile metadata
    profile = instaloader.Profile.from_username(loader.context, profile_name)

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

            loader.dirname_pattern = f"stories/{dir_name}/"
            loader.filename_pattern = f'{date}'
            loader.download_storyitem(item, target='')

            delay = random.randint(4, 10)
            time.sleep(delay)

    logger.success("Successfully downloaded stories.")
