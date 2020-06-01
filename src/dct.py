import os
import random
import numpy as np
import matplotlib.pyplot as pyplot
import imageio
import math
from scipy.fftpack import dct
from scipy.fftpack import idct
from cryptography.fernet import Fernet
import bchlib

BCH_POLYNOMIAL = 8219
# max number of bit flips we can account for, increasing this increase the ecc length
BCH_BITS = 30
# for determining how many times the packet should be repeated for ecc
NUM_REPETITIONS = 3
MAX_MESSAGE_LENGTH = 50

u1 = 3
v1 = 4  #Middle band coordinates
u2= 4
v2 = 3

n = 8 # 8x8 pixel block

threshold = 500  #Default threshold

compressionRate = 50

def dctType2(a):
	return dct(dct(a, axis=0), axis=1)

def idctType2(a):
	return idct(idct(a, axis=0), axis=1)

def round_down(num, divisor):
	return num - (num % divisor)

# check for errors and correct
def performBCHCorrection(extractedPacket):
	bch = bchlib.BCH(BCH_POLYNOMIAL, BCH_BITS)	
	newData, newEcc = extractedPacket[:-bch.ecc_bytes], extractedPacket[-bch.ecc_bytes:]
	try:
		bitflips = bch.decode_inplace(newData, newEcc)
		#print('bitflips: %d' % (bitflips))
		#print("Here is the decrypted message: ", newData.decode('utf-8'))
		return newData.decode('utf-8').rstrip(' \n')
	except:
		#print("Issues with decoding data, here's what was recovered: ", newData)
		return newData

# assumes decryptMsg will be a list of binary with spaces between each 8 bits
def extractBCHPacket(decryptMsg):
	# turn binary back into int and append to bytearray
	extractedPacket = bytearray(b'')
	i = 0
	while i < len(decryptMsg):
		bytemessage = int(decryptMsg[i:i+8], 2)
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

def msg_encodeBinary(msg):
	i = len(msg)
	while i < 50:
		msg += " "
		i = len(msg)
	binaryMsg = setupBCH(msg)
	return setupRepetitions(binaryMsg)


def msg_decodeBinary(msg):
	repeatedMessages = extractRepetitions(msg)
	# extract packet and perform BCH correction on each repeated message
	extractedMessages = []
	for i in range(0, len(repeatedMessages)):
		extractedPacket = extractBCHPacket(repeatedMessages[i])
		extractedMessages.append(performBCHCorrection(extractedPacket))

	#Return a list of recovered messages
	return extractedMessages


def check_coeff(c1, c2, bit, P):
	diff = abs(c1) - abs(c2)

	if (bit == '0') and (diff > P):
		return True
	elif (bit == '1') and (diff < -P):
		return True
	else:
		return False


def add_coeff(c):
	if (c >= 0.0):
		return c + 1.0
	else:
		return c - 1.0


def sub_coeff(c, c_init):
	if (abs(c) <= 1):
		return 0
	elif (c >= 0):
		return c - 1.0
	else:
		return c + 1



def modify_coeff(arr, bit, c1_init, c2_init):
	coeff = arr.copy()

	if (bit == '0'):
		coeff[u1, v1] = add_coeff(coeff[u1, v1])
		coeff[u2, v2] = sub_coeff(coeff[u2, v2], c2_init)

	elif(bit == '1'):
		coeff[u1, v1] = sub_coeff(coeff[u1, v1], c1_init)
		coeff[u2, v2] = add_coeff(coeff[u2, v2])

	return coeff


def embed_bit(arr, b_msg, P):
	coeff = dctType2(arr)
	if (coeff[u1, v1] <= 0):
		c1_init = 0
	else:
		c1_init = 1

	if (coeff[u2, v2] <= 0):
		c2_init = 0
	else:
		c2_init = 1
	
	#Modify coefficients if they don't satisfy req for bit value
	while(check_coeff(coeff[u1, v1], coeff[u2,v2], b_msg, P) == False):
		coeff = modify_coeff(coeff, b_msg, c1_init, c2_init)
	
	block = idctType2(coeff) / ((2*n)**(2))
	return block;


def embed_DCT(cover, msg, thresh):
	coverSize = cover.shape

	stego = cover.copy()  #create copy of cover

	binary_msg = msg_encodeBinary(msg)

	msg_len = len(binary_msg)

	num_bits = math.floor(round_down(coverSize[0], n) *  #One bit per 8x8 block
						  round_down(coverSize[1], n) / (n*n)) 

	if (msg_len > num_bits):
		raise ValueError("Message too long")

	order = random.sample(range(0, num_bits), msg_len)  #

	msg_idx = 0;

	for x in order:
		i = (x % (coverSize[0]//n)) * n
		j = (x // (coverSize[1]//n)) * n

		if (msg_idx >= msg_len):
			break
		stego[i:(i+n), j:(j+n)] = embed_bit(cover[i:(i+n), j:(j+n)], \
											   binary_msg[msg_idx], thresh)

		msg_idx = msg_idx + 1

	orderString = " ".join(map(str,order))
	binOrderString = orderString.encode('utf-8')
	key = Fernet.generate_key()
	cipher_suite = Fernet(key)
	encoded_text = cipher_suite.encrypt(binOrderString)

	return stego, key, encoded_text

def extract_bit(arr):
	coeff = dctType2(arr)
	if (abs(coeff[u1, v1]) - abs(coeff[u2, v2]) >= 0):
		return '0'
	else:
		return '1'


def extract_DCT(stego, key, encoded_text):
	stegoSize = stego.shape

	cipher_suite = Fernet(key)
	decoded_text = cipher_suite.decrypt(encoded_text)

	order = list(map(int, decoded_text.split()))

	msg_bits = ['']
	
	for x in order:
		i = (x % (stegoSize[0]//n)) * n
		j = (x // (stegoSize[1]//n)) * n
		msg_bits.append(extract_bit(stego[i:(i+8), j:(j+8)]))

	msg = ''.join(msg_bits)

	msg_reps = msg_decodeBinary(msg)


	return msg_reps

if __name__ == "__main__":
	import sys
	if (len(sys.argv) < 2):
		raise ValueError("Please provide the cover image file, \
						  output file name, and a message\n")

	else:
		stegoFile = sys.argv[2]
		msg = sys.argv[3].rstrip('\n')
		if (len(msg) > MAX_MESSAGE_LENGTH):
			raise ValueError("Please make sure your message is less than " + str(MAX_MESSAGE_LENGTH) + " characters long.")

		cover = imageio.imread(sys.argv[1], pilmode='L')

		print("Inserting watermark into image...\n")

		stego, key, encoded_text = embed_DCT(cover, msg, threshold)

		print("Writing to", stegoFile)

		#Save image with message
		imageio.imwrite(stegoFile + ".jpg", stego, pilmode='L', quality=compressionRate)
		imageio.imwrite(stegoFile + ".bmp", stego);

		#Display Image
		stegojpg = imageio.imread(stegoFile + ".jpg", pilmode='L');
		stegobmp = imageio.imread(stegoFile + ".bmp", pilmode='L');

		pyplot.figure(2)

		pyplot.imshow( np.hstack( (cover, stegobmp, stegojpg) ) ,cmap='gray')
		pyplot.show()

		extracted_msg = extract_DCT(stegojpg, key, encoded_text)
		print("\tOriginal Message:  ", msg + "\n")
		for x in extracted_msg:
			if (x == msg):
				print("\tExtracted Message: ", x)
				print("\t\tSuccessfully recovered the same message")
			else:
				print("\t\tFailed to retrieve original message")