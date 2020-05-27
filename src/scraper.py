from PIL import Image
from imgurpython import ImgurClient
import io
import requests
from pprint import pprint
from dct import embed_DCT, extract_DCT
import imageio

imgurEnv = {
  'client_id': 'afcafc05b75c60c',
  'client_secret': 'd17ae76a4ebbdbb63a71598dfc94966a47039e46'
}

def imagesFromGalleryObject(galleryObject):
  images = []
  try:
    for image in galleryObject.images:
      if image['link'][-4:] == '.mp4':
        continue
      img = imageio.imread(image['link'])
      images.append(img)
  except AttributeError:
    if galleryObject.link[-4:] != '.mp4':
      img = imageio.imread(galleryObject.link)
      images.append(img)
  return images

def imageDataToImage(imageData):
  try:
    img = Image.open(io.BytesIO(imageData))
  except:
    return None
  return img

def getImageData(url):
  data = requests.get(url).content
  return data

if __name__ == "__main__":
  cover = imageio.imread('S:/Pictures/Wallpapers - Spring 2019/175237.jpg', pilmode='L')
  msg = 'hellothere'
  stego, key, cipherText = embed_DCT(cover, msg)
  

  imgurClient = ImgurClient(imgurEnv['client_id'], imgurEnv['client_secret'])
  items = imgurClient.gallery()
  images = []
  for item in items:
    images += imagesFromGalleryObject(item)
