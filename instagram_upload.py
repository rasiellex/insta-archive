import glob
import time
import traceback
from datetime import datetime, timedelta

import yaml
from instagrapi import Client
from loguru import logger

from helper_functions import preprocess_image_for_instagram, send_to_discord_webhook


def split_list(ls, chunk_size):
    return {i: ls[i:i + chunk_size] for i in range(0, len(ls), chunk_size)}


if __name__ == "__main__":
    log_file = "insta-upload.log"
    logger.add(log_file)
    start_time = time.time()
    logger.info("Start process: Upload to Instagram.")

    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    user = config["INSTA_DOWNLOAD"]["USER"]
    pw = config["INSTA_DOWNLOAD"]["PASSWORD"]
    data_path = config["DATA_PATH"]
    user_timezone = config["USER_TIMEZONE"]
    instagram_caption = config["CAPTION"]
    webhook_discord = config["DISCORD"]["WEBHOOK_INSTA_UPLOAD"]
    webhook_discord_alert = config["DISCORD"]["WEBHOOK_ALERT"]

    session_filename_user = user.replace('.', '_')
    session_filename = f"session_instagrapi_{session_filename_user}.json"

    try:
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
            cl.load_settings(session_filename)
            cl.login(user, pw)
            logger.info(f"Successfully logged in to account: {user} via session file.")
        except:
            logger.info("Login via session file failed. Session file expired.")
            try:
                logger.info("Login in via credentials and save session file.")
                cl.login(user, pw)
                cl.dump_settings(session_filename)
                logger.info(f"Successfully logged in to account: {user} via credentials and saved session file to disk.")
            except Exception as e:
                raise

        dir_path = f"{data_path}{date_dir}"

        fp_images = glob.glob(f"{dir_path}/*.jpg")
        fp_images = [file for file in fp_images if "edit" not in file]
        fp_images.sort()
        num_img = len(fp_images)

        logger.info(f"Select JPG files from date folder: {dir_path}. Found {num_img} images.")

        if num_img > 0:
            upload_image = True
            logger.info(f"Preprocess images for instagram.")
            for file in fp_images:
                preprocess_image_for_instagram(file)

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

            caption = (f"{instagram_caption} | {date_caption} \n\n\n "
                       f"#illenium #illenials #illeniumintel #nickmiller #edm")
            logger.info(f"Caption for Instagram post: {caption}")
            logger.info(f"Number of instagram posts: {num_img_posts} image posts | {num_video} video posts")

            if upload_image:
                for key, value in image_chunks.items():
                    num_images = len(value)
                    if num_images > 1:
                        logger.info(
                            f"Upload image post to Instagram. Number of images: {num_images}. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                        cl.album_upload(
                            paths=value,
                            caption=caption,
                        )
                        logger.success(
                            f"Successfully uploaded image post. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                    else:
                        fp_img = value[0]
                        logger.info(
                            f"Upload image post to Instagram. Number of images: {num_images}. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")
                        cl.photo_upload(
                            path=fp_img,
                            caption=caption,

                        )
                        logger.success(
                            f"Successfully uploaded image post. "
                            f"({key + 1}/{len(image_chunks.keys())} image posts)")

            if upload_video:
                for index, fp_video in enumerate(fp_videos):
                    logger.info(f"Upload {index + 1}/{num_video} video to Instagram.")
                    cl.clip_upload(
                        path=fp_video,
                        caption=caption,
                    )
                    logger.success(f"Successfully uploaded video post. ({index + 1}/{num_video} video posts)")

        else:
            logger.info(f"No files found to upload for date {date_dir}.")

        total_time = int(round((time.time() - start_time)))
        total_time = str(timedelta(seconds=total_time))
        logger.info(f"Finished process: Upload to Instagram. End script. Elapsed time: {total_time}")

    except Exception as e:
        logger.info("Script failed.")
        logger.exception(e)
        error_message = traceback.format_exc()
        send_to_discord_webhook(webhook_url=webhook_discord_alert,
                                input_text="ERROR: Instagram upload script failed.")
        send_to_discord_webhook(webhook_url=webhook_discord_alert,
                                input_text=error_message)

    finally:
        with open(log_file, 'r') as file:
            log_content = file.readlines()
            [send_to_discord_webhook(webhook_url=webhook_discord, input_text=line) for line in log_content]