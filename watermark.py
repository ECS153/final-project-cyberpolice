import os
import random
import time
import sys
from PIL import Image	

# extracts 4 least significant bits
def extractBits(pixelsToExtract):
	extractedPixels = []
	for i in range(0, len(pixelsToExtract)):
		watermarkBin = format(pixelsToExtract[i], '08b')
		watermarkBin = watermarkBin[6:]
		extractedPixels.append(int(watermarkBin + "000000", 2))
	return tuple(extractedPixels)

# creates list of tuples of last 4 bits of rgba values
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
	# print(*modifiedPixels, sep = ", ")
	return tuple(modifiedPixels)

# start by applying to topleft
def applyWatermark(img, watermark):
	print("Applying watermark to image...\n")
	img = Image.open(img)
	imgWidth, height = img.size
	img = img.convert("RGBA")
	watermark = Image.open(watermark)
	watermarkWidth, height = watermark.size
	watermark = watermark.convert("RGBA")

	offset = 0
	pixelsToModify = list(img.getdata())
	watermarkPixels = list(watermark.getdata())

	if len(watermarkPixels) > len(pixelsToModify):
		raise WatermarkTooLarge("Please ensure the watermark is smaller than the image")
	
	# when end of watermark image reached, start on next row of pixels
	watermarkIndex = 0
	watermarkWidthUnchanged = watermarkWidth
	i = 0
	while watermarkIndex < len(watermarkPixels):
		if i == watermarkWidth:
			i += imgWidth - watermarkWidthUnchanged
			watermarkWidth += imgWidth

		pixelsToModify[i] = modifyBits(pixelsToModify[i], watermarkPixels[watermarkIndex])
		watermarkIndex+=1
		i+=1

	# can use scale or offset to apply at different spots
	imgToWatermark = img.copy()
	imgToWatermark.putdata(pixelsToModify)
	extractedWatermark = extractWatermark(imgToWatermark)
	imgToWatermark.show("Watermarked Image")
	extractedWatermark.show("Watermark")

def main():

	if (len(sys.argv) <= 2 or len(sys.argv) >= 4):
		raise WrongNumberofArguments("Please provide the image file, \
			and the watermark image file")

	else:
		applyWatermark(sys.argv[1], sys.argv[2])

main()