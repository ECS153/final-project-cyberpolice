from tkinter import *
from PIL import Image, ImageTk

# needed to pass data between canvas click and button click event
imgPosition = 0

# extracts 4 least significant bits
def extractBits(pixelsToExtract):
	extractedPixels = []
	for i in range(0, len(pixelsToExtract)):
		watermarkBin = format(pixelsToExtract[i], '08b')
		watermarkBin = watermarkBin[6:]
		extractedPixels.append(int(watermarkBin + "000000", 2))
	return tuple(extractedPixels)

# creates list of tuples of last 4 bits of rgba values
# TODO figure out how this can be sped up... multithreading?
def extractWatermark(img):
	print("Extracting watermark from image...\n")
	# img = Image.open(img)
	# img = img.convert("RGBA")
	watermark = list(img.getdata())
	for i in range(0, len(watermark)):
		watermark[i] = extractBits(watermark[i])
	watermarkImg = img.copy()
	watermarkImg.putdata(watermark)
	return watermarkImg

# inserts 4 most significant bits of watermark to 4 least significant bits of image for rbga values
def modifyBits(pixelsToModify, pixelsToApply):
	modifiedPixels = []
	for i in range(0, len(pixelsToModify)):
		imgBin = format(pixelsToModify[i], '08b')
		watermarkBin = format(pixelsToApply[i], '08b')
		imgBin = imgBin[:6]
		watermarkBin = watermarkBin[:2]
		modifiedPixels.append(int(imgBin + watermarkBin, 2))
	return tuple(modifiedPixels)

# applies watermark starting at imgPosition specified by user click on gui
def applyWatermark(img, watermark):
	print("Applying watermark to image...\n")
	# setting up img and watermark to be used
	img = Image.open(img)
	imgWidth, height = img.size
	img = img.convert("RGBA")
	watermark = Image.open(watermark)
	watermarkWidth, height = watermark.size
	watermark = watermark.convert("RGBA")

	offset = 0
	pixelsToModify = list(img.getdata())
	watermarkPixels = list(watermark.getdata())
	global imgPosition
	# if length of remaining pixels is less than length of watermark, choose different spot
	if len(watermarkPixels) > len(pixelsToModify) - imgPosition:
		raise WatermarkTooLarge("Please ensure the watermark is smaller than the image")
	
	# when end of watermark image reached, start on next row of pixels
	watermarkIndex = 0
	watermarkWidthUnchanged = watermarkWidth
	# account for offset of imgPosition start
	watermarkWidth += imgPosition
	while watermarkIndex < len(watermarkPixels):
		if imgPosition == watermarkWidth:
			# account for watermark offset and go to beginning of new "row"
			imgPosition += imgWidth - watermarkWidthUnchanged
			# update what the end of the "row" is
			watermarkWidth += imgWidth

		pixelsToModify[imgPosition] = modifyBits(pixelsToModify[imgPosition], watermarkPixels[watermarkIndex])
		watermarkIndex+=1
		imgPosition+=1

	# can use scale or offset to apply at different spots
	imgToWatermark = img.copy()
	imgToWatermark.putdata(pixelsToModify)
	extractedWatermark = extractWatermark(imgToWatermark)
	imgToWatermark.show("Watermarked Image")
	extractedWatermark.show("Watermark")
	print("Pictures displayed")

# creates gui for user to click and confirm placement of watermark
def setupImageTk(originalImg, watermark):
	root = Tk()
	#setting up a tkinter canvas with scrollbars
	frame = Frame(root)
	# create frame to hold widgets
	frame.grid_rowconfigure(0, weight=1)
	frame.grid_columnconfigure(0, weight=1)
	# create scrollbar and button
	xscroll = Scrollbar(frame, orient=HORIZONTAL)
	xscroll.grid(row=1, column=0, sticky=E+W)
	yscroll = Scrollbar(frame)
	yscroll.grid(row=0, column=1, sticky=N+S)
	b = Button(frame, text="Confirm")
	b.grid(row=2, column=0)
	# canvas to display image with scrollbar starting at topleft of image
	canvas = Canvas(frame, bd=0, xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
	canvas.grid(row=0, column=0, sticky=N+S+E+W)
	xscroll.config(command=canvas.xview)
	yscroll.config(command=canvas.yview)

	# TODO figure out proper lambda expression for calling function with args
	def watermarkSpot():
		applyWatermark(originalImg, watermark)

	#button click event
	b.config(command=watermarkSpot)
	frame.pack(fill=BOTH,expand=True)

	#adding the image
	img = ImageTk.PhotoImage(Image.open(originalImg))
	canvas.create_image(0,0,image=img,anchor="nw")
	canvas.config(scrollregion=canvas.bbox(ALL))

	#function to be called when mouse is clicked
	# TODO fix coordinate placement issue
	def setupCoordinates(event):
		print ("(%d, %d)" % (canvas.canvasx(event.x), canvas.canvasy(event.y)))
		xcoord = canvas.canvasx(event.x)
		ycoord = canvas.canvasy(event.y)
		if (xcoord > 0 and ycoord > 0):
			tempImg = Image.open(originalImg)
			imgWidth, height = tempImg.size
			global imgPosition
			imgPosition = 0
			imgPosition = int(height)*xcoord + ycoord
			imgPosition = int(imgPosition)

	#mouseclick event
	canvas.bind("<ButtonPress-1>",setupCoordinates)

	# blocks executation from finishing so picture displays
	root.mainloop()

if __name__== "__main__":
	if (len(sys.argv) <= 2 or len(sys.argv) >= 4):
		raise WrongNumberofArguments("Please provide the image file, \
			then the watermark image file")

	else:
		setupImageTk(sys.argv[1], sys.argv[2])