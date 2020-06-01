from PIL import Image
from imgurpython import ImgurClient
import io
import requests
from pprint import pprint
from dct import embed_DCT, extract_DCT
import imageio
import matplotlib.pyplot as pyplot
from tkinter import *
from tkinter.ttk import *

imgurEnv = {
  'client_id': 'afcafc05b75c60c',
  'client_secret': 'd17ae76a4ebbdbb63a71598dfc94966a47039e46'
}

def ReadImage(url, greyscale=True):
  img = imageio.imread(url, pilmode='L') if greyscale else imageio.imread(url)
  return img

def imagesFromGalleryObject(galleryObject):
  images = []
  try:
    for image in galleryObject.images:
      if image['link'][-4:].lower() not in ['.mp4', '.gif']:
        continue
      img = imageio.imread(image['link'], pilmode='L')
      images.append(img)
  except AttributeError:
    if galleryObject.link[-4:].lower() not in ['.mp4', '.gif']:
      img = imageio.imread(galleryObject.link, pilmode='L')
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

def checkMatch(msg, stego, key, cipherText):
  try:
    repMsg = extract_DCT(stego, key, cipherText)
    return msg in repMsg
  except:
    return None

class MonitorApp:
  def __init__(self):
    self.coverImageFilePath = None
    self.stegoImageFilePath = None
    self.key = None
    self.cipherText = None
    self.mainWindow = Tk()
    self.notebook = Notebook(self.mainWindow)
    self.encodeTab = Frame(self.notebook)
    self.decodeTab = Frame(self.notebook)
    self.notebook.add(self.encodeTab, text='Encode', compound=TOP)
    self.notebook.add(self.decodeTab, text='Decode')
    self.setupEncodingTab(self.encodeTab)
    self.setupDecodingTab(self.decodeTab)
    self.notebook.pack()
    
  
  def setupEncodingTab(self, tab):
    self.coverImageFileButton = Button(tab, text='Click to choose cover file', command=lambda: self.chooseCoverImageFilePath())
    self.coverImageFileButton.grid(row=0, columnspan=2, pady=(10,0))
    Label(tab, text='Fingerprint').grid(row=1, column=0)
    self.messageEntry = Entry(tab)
    self.messageEntry.grid(row=1, column=1)
    self.encodeButton = Button(tab, text='Encode', command=self.encode)
    self.encodeButton.grid(row=2, columnspan=2)

  def setupDecodingTab(self, tab):
    self.curRadio = IntVar()
    self.urlRadio = Radiobutton(tab, text='URL', variable=self.curRadio, value=0)
    self.urlRadio.grid(row=0, column=0, pady=(10,0))
    self.urlEntry = Entry(tab)
    self.urlEntry.grid(row=0, column=1, pady=(10,0))
    self.stegoFileRadio = Radiobutton(tab, text='File', variable=self.curRadio, value=1)
    self.stegoFileRadio.grid(row=1, column=0)
    self.stegoImageFileButton = Button(tab, text='Click to choose stego file', command=lambda: self.chooseStegoImageFilePath())
    self.stegoImageFileButton.grid(row=1, column=1)
    self.encodeButton = Button(tab, text='Decode', command=self.decode)
    self.encodeButton.grid(row=2, columnspan=2) 

  def start(self):
    self.mainWindow.mainloop()

  def chooseCoverImageFilePath(self):
    path = filedialog.askopenfilename()
    if not path:
      return
    self.coverImageFilePath = path
    self.coverImageFileButton.configure(text=path)

  def chooseStegoImageFilePath(self):
    path = filedialog.askopenfilename()
    if not path:
      return
    self.stegoImageFilePath = path
    self.stegoImageFileButton.configure(text=path)

  def encode(self):
    if not self.coverImageFilePath:
      return
    cover = imageio.imread(self.coverImageFilePath, pilmode='L')
    self.message = self.messageEntry.get()
    stego, self.key, self.cipherText = embed_DCT(cover, self.message, 500)
    begin = self.coverImageFilePath.rindex('/')
    end = self.coverImageFilePath.rindex('.')
    stegoFilePath = self.coverImageFilePath[:begin+1] + 'stego' + self.coverImageFilePath[end:]
    imageio.imwrite(stegoFilePath, stego, pilmode='L', quality=50)

  def decode(self):
    stegoPath = self.urlEntry.get() if self.curRadio.get() == 0 else self.stegoImageFilePath
    if not stegoPath:
      return
    stego = imageio.imread(stegoPath, pilmode='L')
    if checkMatch(self.message, stego, self.key, self.cipherText):
      messagebox.showwarning('Match', 'The fingerprint was found in the image')
    else:
      messagebox.showinfo('Not a match', 'The fingerprint was not found in the image')

if __name__ == "__main__":
  # cover = imageio.imread('S:/Downloads/cover.jpg', pilmode='L')
  # msg = 'mymessage'
  # stego, key, cipherText = embed_DCT(cover, msg, 500)
  # imageio.imwrite('S:/Downloads/stego.jpg', stego, pilmode='L', quality=50)

  # imgurClient = ImgurClient(imgurEnv['client_id'], imgurEnv['client_secret'])
  # # items = imgurClient.gallery()
  # # images = []
  # # for item in items:
  # #   images += imagesFromGalleryObject(item)

  # # for image in images:
  # #   print(image)
  # #   extractedMsg = extract_DCT(image, key, cipherText)
  # #   print(extractedMsg == msg)

  # # pyplot.imshow(im)
  # # pyplot.show()

  # url = imgurClient.get_image('PhGOkkJ').link
  # im = ReadImage(url)
  # print(checkMatch(msg, im, key, cipherText))
  monitorApp = MonitorApp()
  monitorApp.start()
  