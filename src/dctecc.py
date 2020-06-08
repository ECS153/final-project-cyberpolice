import os
import random
import time
import sys
import string
from PIL import Image
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import binascii
import bchlib

BCH_POLYNOMIAL = 8219
# max number of bit flips we can account for, increasing this increase the ecc length
BCH_BITS = 100
# for determining how many times the packet should be repeated for ecc
NUM_REPETITIONS = 4
MAX_MESSAGE_LENGTH = 50

# check for errors and correct
def performBCHCorrection(extractedPacket):
	bch = bchlib.BCH(BCH_POLYNOMIAL, BCH_BITS)	
	newData, newEcc = extractedPacket[:-bch.ecc_bytes], extractedPacket[-bch.ecc_bytes:]
	bitflips = bch.decode_inplace(newData, newEcc)
	print('bitflips: %d' % (bitflips))
	print("Here is the decrypted message: ", newData.decode('utf-8'))

# assumes decryptMsg will be a list of binary with spaces between each 8 bits
def extractBCHPacket(decryptMsg):
	# turn binary back into int and append to bytearray
	extractedPacket = bytearray(b'')
	i = 0
	while i < len(decryptMsg):
		# introducing some errors
		bit_num = random.randint(0, 20)
		bytemessage = int(decryptMsg[i:i+8], 2)
		if bit_num == 0:
			bytemessage = 1
		extractedPacket.append(bytemessage)
		i += 8
	return extractedPacket

# generates binary message and ecc from input string
def setupBCH(msg):
	# create a bch object
	bch = bchlib.BCH(BCH_POLYNOMIAL, BCH_BITS)
	data = bytearray()
	data.extend(map(ord, msg))
	ecc = bch.encode(data)
	packet = data + ecc
	binPacket = ""
	for i in range(0, len(packet)):
		binPacket += '{0:08b}'.format(packet[i])
		# binPacket += " "
	return binPacket

def convertMsgLength():
	# if we change bch_length, conversion changes
	start = len(setupBCH(''))
	remainder = MAX_MESSAGE_LENGTH
	# 8 bits
	return (start + (8 * MAX_MESSAGE_LENGTH))
	
def extractRepetitions(decryptMsg):
	indices = []
	originalBinaryLength = convertMsgLength()
	for i in range(0, NUM_REPETITIONS):
		indices.append(originalBinaryLength*i)
	parts = [decryptMsg[i:j] for i,j in zip(indices, indices[1:]+[None])]
	return parts

def setupRepetitions(binaryMsg):
	# repeat the message+ecc based on NUM_REPETITIONS
	temp = binaryMsg
	for i in range(0, NUM_REPETITIONS - 1):
		binaryMsg += temp
	return binaryMsg

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

	# repeat the message+ecc based on NUM_REPETITIONS
	binaryMsg = setupBCH(msg)
	binaryMsg = setupRepetitions(binaryMsg)

	#Generate psuedo random order of pixels to modify based on length of bch msg
	order = random.sample(range(0, img.width * img.height), (len(binaryMsg.split(" "))-1) * 2) 
	pixels = list(img.getdata())	#Flatten RGBA arrays into a list

	# binaryMsg = binaryMsg.replace(" ", "")

	for i in range(0, len(order) - 1):
		for j in range(0, 4):
			pixels[ order[i] ] = changeLSB(pixels[ order[i] ], binaryMsg[ (i*4):((i*4)+4) ])

	alteredImg.putdata(pixels)  #Place modified pixels into another image

	print("Displaying image with embedded message...\n")

	# alteredImg.show("Altered Image")

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

		# if (i % 2 == 1):
		# 	decryptMsg = decryptMsg + " "

	# Split repeated packet based on length
	repeatedMessages = extractRepetitions(decryptMsg)

	# extract packet and perform BCH correction on each repeated message
	for i in range(0, len(repeatedMessages)):
		extractedPacket = extractBCHPacket(repeatedMessages[i])
		performBCHCorrection(extractedPacket)

if __name__== "__main__":

	# if (len(sys.argv) < 2):
	# 	raise WrongNumberofArguments("Please provide the image file, the message you wish to encrypt, and a name to identify this message")

	# else:
	# 	img = Image.open(sys.argv[1])
		
	# 	img = img.convert("RGBA")

	# 	print("Inserting message into image...\n")

	# 	insertMessage(img, sys.argv[2], sys.argv[3])
	img = Image.open("../Images/Picture.png")
		
	img = img.convert("RGBA")

	print("Inserting message into image...\n")
	testmsg = "a"
	i = len(testmsg)
	while i < MAX_MESSAGE_LENGTH:
		testmsg += " "
		i = len(testmsg)

	# repeat the message+ecc based on NUM_REPETITIONS
	binaryMsg = setupBCH(testmsg)
	binaryMsg = setupRepetitions(binaryMsg)
	repeatedMessages = extractRepetitions(binaryMsg)
	# extract packet and perform BCH correction on each repeated message
	for i in range(0, len(repeatedMessages)):
		extractedPacket = extractBCHPacket(repeatedMessages[i])
		performBCHCorrection(extractedPacket)	

	# insertMessage(img, testmsg, "testmsg")
