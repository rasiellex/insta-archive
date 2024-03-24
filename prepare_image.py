from PIL import Image
import os


def preprocess_image(img_path: str):

    input_dir = os.path.dirname(img_path)
    filename = os.path.splitext(os.path.basename(img_path))
    basename, extension = filename[0], filename[1]
    output_path = f"{input_dir}/{basename}_edited{extension}"

    img = Image.open(img_path)
    img.show()

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

if __name__ == "__main__":
    image_path = "D:/PyCharm/insta-archive/data/2024-03-22/2024-03-22_08-30-07_UTC.jpg"
    preprocess_image(image_path)
