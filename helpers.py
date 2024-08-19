from PIL import Image
from pillow_heif import HeifImagePlugin
import io
import os
import uuid
import requests

# return true if image is valid, false if it's not
def verify_image(image, path):
    try:
        with Image.open(image) as im:
            # image must be a jpeg or heif
            if im.format in ["JPEG", "HEIF"]:
                try:
                    im.save(path)
                    return True
                except OSError:
                    return False
    # error if file is not an image
    except IOError:
        return False
    return False

# returns the file name if image is correctly saved, else returns None
def save_image(image):
    # creates a random name to the file using uuid
    # image is saved as a jpg
    file_name = str(uuid.uuid4()) + ".jpg"
    if verify_image(image, f"static/images/{file_name}"):
        return file_name
    return None

# returns the file name if image is correctly saved, else returns None
def save_image_instagram(url):
    # gets the imaga content with request
    image_data = io.BytesIO(requests.get(url).content)
    # creates a random name to the file using uuid
    # image is saved as a jpg
    file_name = str(uuid.uuid4()) + ".jpg"
    if verify_image(image_data, f"static/images/{file_name}"):
        return file_name
    return None

def delete_image(file_name):
    try:
        os.remove(f"static/images/{file_name}")
    except OSError:
        return None
    
# returns the data from instagram if everything works, else returns None
def instagram_scrapper(account_name):
    url = (
        "https://i.instagram.com/api/v1/users/web_profile_info/?username="
        + account_name
    )
    # header to make the request simulating an mobile device
    headers = {
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.11.118 (iPhone11,8; iOS 12_3_1; en_US; en-US; scale=2.00; 828x1792; 165586599)"
    }

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        unfiltered_data = r.json()["data"]["user"]
        if unfiltered_data != None:
            keys = [
                "full_name",
                "biography",
                "business_address_json",
                "username",
                "profile_pic_url",
            ]
            # filter only the data wanted
            restaurant_data = {x: unfiltered_data[x] for x in keys}
            restaurant_data["image_path"] = save_image_instagram(restaurant_data["profile_pic_url"]
            )
            return restaurant_data

    return None
