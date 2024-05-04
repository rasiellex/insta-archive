import glob
import os
import random
import time

import requests
from PIL import Image
from loguru import logger


def send_to_discord_webhook(webhook_url: str, input_text: str) -> None:
    """Send text to discord channel via webhook.

    Args:
        webhook_url: Webhook
        input_text: text

    Returns:

    """
    data = {
        'content': input_text
    }

    # Senden der POST-Anfrage an den Discord-Webhook
    response = requests.post(webhook_url, json=data)

    # Überprüfen des Statuscodes der Antwort
    if response.status_code == 204:
        print('Message successfully sent to Discord.')
        delay = random.randint(1, 6)
        time.sleep(delay)
    else:
        print(f'An error occurred while sending a message to Discord. Status code: {response.status_code}')


def preprocess_image_for_instagram(img_path: str):
    """Resize an image in ratio 1:1

    Args:
        img_path: Path to image

    Returns:
        None
    """
    logger.info(f"Preprocess image for instagram: {img_path}")
    input_dir = os.path.dirname(img_path)
    filename = os.path.splitext(os.path.basename(img_path))
    basename, extension = filename[0], filename[1]
    output_path = f"{input_dir}/{basename}_edited{extension}"

    img = Image.open(img_path)

    original_width, original_height = img.size

    # define target ratio for instagram post (1:1)
    target_ratio = 1 / 1

    # calculate dimensions for the new image
    if original_width / original_height > target_ratio:
        new_width = original_width
        new_height = int(original_width / target_ratio)
    else:
        new_width = int(original_height * target_ratio)
        new_height = original_height

    new_image = Image.new("RGB", (new_width, new_height), "black")

    # calculate the position to paste the image
    paste_position = ((new_width - original_width) // 2, (new_height - original_height) // 2)

    new_image.paste(img, paste_position)

    new_image.save(output_path)
    logger.info(f"Sucessfully preprocessed and saved new image. Path to file: {output_path}")


if __name__ == "__main__":
    fps = glob.glob("data/*.jpg")
    fps = [file for file in fps if "edit" not in file]

    for file in fps:
        preprocess_image_for_instagram(file)
