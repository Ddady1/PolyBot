import requests # to get image from the web
import shutil # to save it locally

def picture_download_url(image_url):
    filename = image_url.split("/")[-1]
    r = requests.get(image_url, stream=True)

    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True

        # Open a local file with wb ( write binary ) permission.
        with open(filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        print('Image sucessfully Downloaded: ', filename)
    else:
        print('Image Couldn\'t be retreived')

