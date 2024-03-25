import glob
import os
from datetime import datetime, timedelta

import pytz
from PIL import Image
from loguru import logger


def preprocess_image(img_path: str):
    logger.info(f"Preprocess image for instagram: {img_path}")
    input_dir = os.path.dirname(img_path)
    filename = os.path.splitext(os.path.basename(img_path))
    basename, extension = filename[0], filename[1]
    output_path = f"{input_dir}/{basename}_edited{extension}"

    img = Image.open(img_path)

    # get dimensions of original image
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

    # create a new image with black background
    new_image = Image.new("RGB", (new_width, new_height), "black")

    # calculate the position to paste the image
    paste_position = ((new_width - original_width) // 2, (new_height - original_height) // 2)

    # paste the original image onto the new image
    new_image.paste(img, paste_position)

    # save the result
    new_image.save(output_path)
    logger.info(f"Sucessfully preprocessed and saved new image. Path to file: {output_path}")


if __name__ == "__main__":
    logger.add("insta-archive.log")

    local_timestamp_org = datetime(2024, 3, 24, 7, 10, 0)

    # Convert it to GMT-6
    denver_timezone = pytz.timezone('US/Mountain')
    local_timestamp = local_timestamp_org.astimezone(denver_timezone)

    local_timestamp = local_timestamp - timedelta(minutes=30)

    date = local_timestamp.strftime('%Y-%m-%d-%H-%M-%S')
    dir_name = local_timestamp.strftime('%Y-%m-%d')

    fps = glob.glob(f"data/{dir_name}/*.jpg")
    fps = [file for file in fps if not "edit" in file]

    for file in fps:
        preprocess_image(file)
