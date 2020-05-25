import os
import random
import time
import sys
from PIL import Image
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

def convertStringToBinary(msg):
	if not msg.isascii():
		raise FormatError("Must be ASCII")
	return "".join(f"{ord(i):08b}" for i in msg)

def findLSB(colorVal):
	if (colorVal % 2 == 0):
		return '0'
	else:
		return '1'


def changeLSB(pixel, targetBits):
	if (targetBits[0] == '0'):
		if (pixel[0] % 2 == 0):
			red = pixel[0]
		else:
			red = pixel[0] - 1
	elif (targetBits[0] == '1'):
		if (pixel[0] % 2 == 0):
			red = pixel[0] + 1
		else:
			red = pixel[0]

	if (targetBits[1] == '0'):
		if (pixel[1] % 2 == 0):
			green = pixel[1]
		else:
			green = pixel[1] - 1
	elif (targetBits[1] == '1'):
		if (pixel[1] % 2 == 0):
			green = pixel[1] + 1
		else:
			green = pixel[1]

	if (targetBits[2] == '0'):
		if (pixel[2] % 2 == 0):
			blue = pixel[2]
		else:
			blue = pixel[2] - 1
	elif (targetBits[2] == '1'):
		if (pixel[2] % 2 == 0):
			blue = pixel[2] + 1
		else:
			blue = pixel[2]

	if (targetBits[3] == '0'):
		if (pixel[3] % 2 == 0):
			alpha = pixel[3]
		else:
			alpha = pixel[3] - 1
	elif (targetBits[3] == '1'):
		if (pixel[3] % 2 == 0):
			alpha = pixel[3] + 1
		else:
			alpha = pixel[3]

	return (red, green, blue, alpha)

"""
insertMessage()
Takes in a RGBA image, message to be encrypted, and associated data to be
authenticated. The authenticated associated data must be passed back to
the decrypt function or it will fail

"""
def insertMessage(img, msg, aad):

	alteredImg = img.copy()

	#Generate psuedo random order of pixels to modify based on length of msg
	order = random.sample(range(0, img.width * img.height), len(msg) * 2) 

	pixels = list(img.getdata())	#Flatten RGBA arrays into a list

	binaryMsg = convertStringToBinary(msg)

	for i in range(0, len(order)):
		for j in range(0, 4):

			pixels[ order[i] ] = changeLSB(pixels[ order[i] ], binaryMsg[ (i*4):((i*4)+4) ])

	alteredImg.putdata(pixels)  #Place modified pixels into another image

	print("Displaying image with embedded message...\n")

	alteredImg.show("Altered Image")

	orderString = " ".join(map(str,order))        #Concatenate pixel coordinates into one whole string
	byteString = bytes(orderString, "ascii")	  #Must be byte array to encrpt

	key = ChaCha20Poly1305.generate_key()
	print("Here is your private key: ", key)
	chacha = ChaCha20Poly1305(key)
	nonce = os.urandom(12)
	ct = chacha.encrypt(nonce, byteString, bytes(aad, "ascii"))

	print("Using key to decrypt image associated with", aad, "\n")

	decryptString = chacha.decrypt(nonce, ct, bytes(aad, "ascii"))

	decodeString = decryptString.decode("ascii")

	decryptOrder = list(map(int, decodeString.split()))

	decryptMsg = ""

	alteredPixels = list(alteredImg.getdata())

	for i in range(0, len(decryptOrder)):
		for j in range(0, 4):
			decryptMsg = decryptMsg + findLSB(alteredPixels[decryptOrder[i]][j])

		if (i % 2 == 1):
			decryptMsg = decryptMsg + " "

	decryptMsg = decryptMsg.split()

	decryptMsg = "".join(list(map(lambda x: chr(int(x ,2)), decryptMsg)))

	print("Here is the decrypted message: ", decryptMsg)





if __name__== "__main__":

	if (len(sys.argv) < 2):
		raise WrongNumberofArguments("Please provide the image file, the message you wish to encrypt, and a name to identify this message")

	else:
		img = Image.open(sys.argv[1])
		
		img = img.convert("RGBA")

		img.show("Original image")

		print("Inserting message into image...\n")

		insertMessage(img, sys.argv[2], sys.argv[3])