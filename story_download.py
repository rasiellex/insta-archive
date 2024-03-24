import instaloader
import time
import os
import random
import pytz
import logging

if __name__ == "__main__":
    user = os.environ["USER"]
    pw = os.environ["PASSWORD"]

    loader = instaloader.Instaloader(
        download_video_thumbnails=False
    )

    # Login (optional)
    # If you want to download stories from private profiles, you need to login with your Instagram credentials.
    loader.login(user=user, passwd=pw)

    # Define the profile name
    profile_name = ""  # Replace "username" with the actual username of the profile you want to download stories from

    # loader.download_profile(profile_name, download_stories_only=True,profile_pic=False)

    # Retrieve the profile metadata
    profile = instaloader.Profile.from_username(loader.context, profile_name)

    stories = loader.get_stories(userids=[profile.userid])

    for story in stories:
        logging.info(f"Number of stories found: {story.itemcount}")
        for item in story.get_items():
            local_timestamp = item.date_utc

            # Convert it to GMT-6
            denver_timezone = pytz.timezone('US/Mountain')
            local_timestamp = local_timestamp.astimezone(denver_timezone)

            date = local_timestamp.strftime('%Y-%m-%d-%H-%M-%S')
            dir_name = local_timestamp.strftime('%Y-%m-%d')

            loader.dirname_pattern = f"data/{dir_name}/"
            loader.filename_pattern = f'{date}'
            loader.download_storyitem(item, target='')

            delay = random.randint(4, 10)
            time.sleep(delay)

    print("Stories downloaded successfully.")
