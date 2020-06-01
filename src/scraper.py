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

def GalleryLinks(gallery):
  links = []
  for item in gallery:
    links += GalleryObjectLinks(item)
  return links

def GalleryObjectLinks(galleryObject):
  links = []
  try:
    for image in galleryObject.images:
      links.append(image['link'])
  except AttributeError:
    links.append(galleryObject.link)
  return links

def imagesFromGalleryObject(galleryObject):
  images = []
  try:
    for image in galleryObject.images:
      print(image['link'][-4:])
      if image['link'][-4:] not in ['.mp4', '.gif']:
        img = imageio.imread(image['link'], pilmode='L')
        images.append(img)
  except AttributeError:
    if galleryObject.link[-4:] not in ['.mp4', '.gif']:
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
    self.isEncoded = False
    self.coverImageFilePath = None
    self.stegoImageFilePath = None
    self.key = None
    self.cipherText = None
    self.mainWindow = Tk()
    self.mainWindow.title('Steganography Tools')
    self.mainWindow.resizable(False, False)
    self.notebook = Notebook(self.mainWindow)
    self.encodeTab = Frame(self.notebook)
    self.decodeTab = Frame(self.notebook)
    self.monitorTab = Frame(self.notebook)
    self.notebook.add(self.encodeTab, text='Encode', compound=TOP)
    self.notebook.add(self.decodeTab, text='Decode')
    self.notebook.add(self.monitorTab, text='Monitor')
    self.setupEncodingTab(self.encodeTab)
    self.setupDecodingTab(self.decodeTab)
    self.setupMonitorTab(self.monitorTab)
    self.notebook.pack()
  
  def setupEncodingTab(self, tab):
    frame = Frame(tab)
    frame.grid(row=0, columnspan=2)
    Label(frame, text='Fingerprint').grid(row=0, column=0, pady=(10,5), sticky='e')
    self.messageEntry = Entry(frame)
    self.messageEntry.grid(row=0, column=1, pady=(10,5))
    self.coverImageFileButton = Button(tab, text='Choose cover image', command=lambda: self.chooseCoverImageFilePath())
    self.coverImageFileButton.grid(row=1, column=0, pady=(5,5), sticky='w')
    self.encodeButton = Button(tab, text='Encode', command=self.encode)
    self.encodeButton.grid(row=1, column=1, pady=(5,5), sticky='w')

  def setupDecodingTab(self, tab):
    self.curRadio = IntVar()
    self.urlRadio = Radiobutton(tab, text='URL', variable=self.curRadio, value=0)
    self.urlRadio.grid(row=0, column=0, pady=(10,5))
    self.urlEntry = Entry(tab)
    self.urlEntry.grid(row=0, column=1, pady=(10,5))
    self.stegoFileRadio = Radiobutton(tab, text='File', variable=self.curRadio, value=1)
    self.stegoFileRadio.grid(row=1, column=0, pady=(10,5))
    self.stegoImageFileButton = Button(tab, text='Click to choose stego file', command=lambda: self.chooseStegoImageFilePath())
    self.stegoImageFileButton.grid(row=1, column=1)
    self.encodeButton = Button(tab, text='Decode', command=self.decode)
    self.encodeButton.grid(row=2, columnspan=2, pady=(10,5)) 

  def setupMonitorTab(self, tab):
    self.scannedImagesText = Text(tab)
    # self.scannedImagesText.configure(state='disabled')
    self.scannedImagesText.grid(row=0)
    self.scanButton = Button(tab, text='Scan Imgur Viral Images', command=self.scanImgurViral)
    self.scanButton.grid(row=1)

  def scanImgurViral(self):
    imgurClient = ImgurClient(imgurEnv['client_id'], imgurEnv['client_secret'])
    links = GalleryLinks(imgurClient.gallery())
    imageLinks = [link for link in links if link[-4:] not in ('.mp4', '.gif')]
    for link in imageLinks:
      stego = imageio.imread(link, pilmode='L')
      matchStatus = 'Match!' if checkMatch(self.message, stego, self.key, self.cipherText) else 'No match'
      print('{} --- {}\n'.format(link, matchStatus))
      self.scannedImagesText.insert(END, '{} --- {}\n'.format(link, matchStatus))

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
    if not self.coverImageFilePath or self.messageEntry.get() == None:
      return
    cover = imageio.imread(self.coverImageFilePath, pilmode='L')
    self.message = self.messageEntry.get()
    stego, self.key, self.cipherText = embed_DCT(cover, self.message, 500)
    begin = self.coverImageFilePath.rindex('/')
    end = self.coverImageFilePath.rindex('.')
    stegoFilePath = self.coverImageFilePath[:begin+1] + 'stego' + self.coverImageFilePath[end:]
    imageio.imwrite(stegoFilePath, stego, pilmode='L', quality=50)
    self.isEncoded=  True

  def decode(self):
    if not self.isEncoded:
      return
    stegoPath = self.urlEntry.get() if self.curRadio.get() == 0 else self.stegoImageFilePath
    if not stegoPath:
      return
    stego = imageio.imread(stegoPath, pilmode='L')
    if checkMatch(self.message, stego, self.key, self.cipherText):
      messagebox.showwarning('Match', 'The fingerprint was found in the image')
    else:
      messagebox.showinfo('Not a match', 'The fingerprint was not found in the image')

if __name__ == "__main__":
  monitorApp = MonitorApp()
  monitorApp.start()
  