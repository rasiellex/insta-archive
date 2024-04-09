import random
import time

import instaloader
import pytz
import requests
import yaml
from loguru import logger


def send_to_discord_webhook(webhook: str, log_file: str):
    # Discord-Webhook-URL
    webhook_url = webhook

    # Daten für die POST-Anfrage

    with open(log_file, 'r') as file:
        content = file.readlines()

        for line in content:
            data = {
                'content': line
            }

            # Senden der POST-Anfrage an den Discord-Webhook
            response = requests.post(webhook_url, json=data)

            # Überprüfen des Statuscodes der Antwort
            if response.status_code == 204:
                print('Nachricht erfolgreich an Discord gesendet.')
                delay = random.randint(1, 6)
                time.sleep(delay)
            else:
                print(f'Fehler beim Senden der Nachricht an Discord. Statuscode: {response.status_code}')


if __name__ == "__main__":
    log_file = "insta-download.log"
    logger.add(log_file)
    logger.info("Start process: Download Instagram stories.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["USER"]
    pw = config["PASSWORD"]
    data_path = config["DATA_PATH"]
    instagram_profile = config["INSTAGRAM_PROFILE"]
    user_timezone = config["USER_TIMEZONE"]
    webhook = config["WEBHOOK_DOWNLOAD"]

    loader = instaloader.Instaloader(
        download_video_thumbnails=False
    )
    try:
        logger.info("Try to login via session file.")
        loader.load_session_from_file(username=user, filename="session_instaloader.json")
        logger.info(f"Successfully logged in to account: {user} via session file.")
    except:
        logger.info("Login via session file failed. Session file expired.")
        try:
            logger.info("Login in via credentials and save session file.")
            loader.login(user=user, passwd=pw)
            loader.save_session_to_file("session_instaloader.json")
            logger.info(f"Successfully logged in to account: {user} via credentials and saved session file to disk.")
        except Exception as e:
            logger.exception(e)

    loader.load_session_from_file(username=user, filename="session_instaloader.json")

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
    logger.info(f"Finished process: Download Instagram stories. End script.")
    send_to_discord_webhook(webhook=webhook, log_file=log_file)
