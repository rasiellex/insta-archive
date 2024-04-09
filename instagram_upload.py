import random
import glob
import time
from datetime import datetime, timedelta

import requests
import yaml
from instagrapi import Client
from loguru import logger

from prepare_image import preprocess_image


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


def split_list(ls, chunk_size):
    return {i: ls[i:i + chunk_size] for i in range(0, len(ls), chunk_size)}


if __name__ == "__main__":
    log_file = "insta-upload.log"
    logger.add(log_file)
    start_time = time.time()
    logger.info("Start process: Upload to Instagram.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["USER"]
    pw = config["PASSWORD"]
    data_path = config["DATA_PATH"]
    user_timezone = config["USER_TIMEZONE"]
    instagram_caption = config["INSTAGRAM_CAPTION"]
    webhook = config["WEBHOOK_UPLOAD"]

    upload_image = False
    upload_video = False

    # Convert local time to destination time
    local_timestamp_org = datetime.now()
    local_timestamp = local_timestamp_org - timedelta(hours=24)

    date_dir = local_timestamp.strftime('%Y-%m-%d')
    date_caption = local_timestamp.strftime('%d.%m.%Y')
    logger.info(f"Local timestamp minus 24 hours: {date_dir}")

    cl = Client()
    # adds a random delay between 1 and 3 seconds after each request
    cl.delay_range = [3, 10]
    try:
        logger.info("Try to login via session file.")
        cl.load_settings("session_instagrapi.json")
        cl.login(user, pw)
        logger.info(f"Successfully logged in to account: {user} via session file.")
    except:
        logger.info("Login via session file failed. Session file expired.")
        try:
            logger.info("Login in via credentials and save session file.")
            cl.login(user, pw)
            cl.dump_settings("session_instagrapi.json")
            logger.info(f"Successfully logged in to account: {user} via credentials and saved session file to disk.")
        except Exception as e:
            logger.exception(e)

    dir_path = f"{data_path}{date_dir}"

    fp_images = glob.glob(f"{dir_path}/*.jpg")
    fp_images = [file for file in fp_images if not "edit" in file]
    fp_images.sort()
    num_img = len(fp_images)

    logger.info(f"Select JPG files from date folder: {dir_path}. Found {num_img} images.")

    if num_img > 0:
        upload_image = True
        logger.info(f"Preprocess images for instagram.")
        for file in fp_images:
            preprocess_image(file)

        fps_edited = glob.glob(f"{dir_path}/*_edited.jpg")
        num_edited_img = len(fps_edited)
        if num_img == num_edited_img:
            logger.success(f"Successfully preprocessed all images ({num_edited_img}/{num_img}).")
        else:
            logger.warning(f"Preprocessed only {num_edited_img}/{num_img} images.")

    fp_videos = glob.glob(f"{dir_path}/*.mp4")
    fp_videos.sort()
    num_video = len(fp_videos)
    logger.info(f"Select MP4 files from date folder: {date_dir}. Found {num_video} videos.")
    if num_video > 0:
        upload_video = True

    if upload_image or upload_video:
        if upload_image:
            image_chunks = split_list(ls=fps_edited, chunk_size=10)
            num_img_posts = len(image_chunks.keys())
        else:
            num_img_posts = 0

        logger.info(f"Connect to Instagram via instagrapi.")
        try:
            cl = Client()
            # adds a random delay between 1 and 3 seconds after each request
            cl.delay_range = [3, 10]
            cl.load_settings("session_instagrapi.json")
            cl.login(user, pw)
            logger.info(f"Successfully logged in to account: {user}.")
        except Exception as e:
            logger.exception(e)

        caption = f"{instagram_caption} | {date_caption}"
        logger.info(f"Caption for Instagram post: {caption}")
        logger.info(f"Number of instagram posts: {num_img_posts} image posts | {num_video} video posts")

        if upload_image:
            for key, value in image_chunks.items():
                num_images = len(value)
                if num_images > 1:
                    try:
                        logger.info(
                            f"Upload image post to Instagram. Number of images: {num_images}. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                        cl.album_upload(
                            paths=value,
                            caption=caption
                        )
                        logger.success(
                            f"Successfully uploaded image post. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                    except Exception as e:
                        logger.warning(e)
                else:
                    try:
                        fp_img = value[0]
                        logger.info(
                            f"Upload image post to Instagram. Number of images: {num_images}. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                        cl.photo_upload(
                            path=fp_img,
                            caption=caption
                        )
                        logger.success(
                            f"Successfully uploaded image post. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                    except Exception as e:
                        logger.warning(e)

        if upload_video:
            for index, fp_video in enumerate(fp_videos):
                try:
                    logger.info(f"Upload {index + 1}/{num_video} video to Instagram.")
                    cl.clip_upload(
                        path=fp_video,
                        caption=caption,
                    )
                    logger.success(f"Successfully uploaded video post. ({index + 1}/{num_video} video posts)")
                except Exception as e:
                    logger.warning(e)

    else:
        logger.info(f"No files found to upload for date {date_dir}.")

    total_time = int(round((time.time() - start_time)))
    total_time = str(timedelta(seconds=total_time))
    logger.info(f"Finished process: Upload to Instagram. End script. Elapsed time: {total_time}")
    send_to_discord_webhook(webhook=webhook, log_file=log_file)
