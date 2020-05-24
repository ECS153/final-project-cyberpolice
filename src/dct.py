import os
import random
import numpy as np
import matplotlib.pyplot as pyplot
import imageio
import math
from scipy.fftpack import dct
from scipy.fftpack import idct
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

u1 = 5
v1 = 4  #Middle band coordinates
u2= 4
v2 = 5

n = 8 # 8x8 pixel block

thresh = 500  #Threshold

def dctType2(a):
	return dct(dct(a, axis=0), axis=1)

def idctType2(a):
	return idct(idct(a, axis=0), axis=1)

def round_down(num, divisor):
	return num - (num % divisor)

def msg_encodeBinary(msg):
	binary_msg = msg.encode()

	binary_int = int.from_bytes(binary_msg, "big") 

	return bin(binary_int)[2:]


def msg_decodeBinary(msg):
	msg_int = int(msg, 2)

	msg_num_bytes = msg_int.bit_length() + 7 // 8

	msg_bytes = msg_int.to_bytes(msg_num_bytes, "big")

	return msg_bytes.decode().lstrip('\x00')


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


def sub_coeff(c):
	if (c >= 0.0):
		return c - 1.0
	else:
		return c + 1.0


def modify_coeff(arr, bit):
	coeff = arr.copy()

	if (bit == '0'):
		coeff[u1, v1] = add_coeff(coeff[u1, v1])
		coeff[u2, v2] = sub_coeff(coeff[u2, v2])

	elif(bit == '1'):
		coeff[u1, v1] = sub_coeff(coeff[u1, v1])
		coeff[u2, v2] = add_coeff(coeff[u2, v2])

	return coeff


def embed_bit(arr, b_msg, P):
	coeff = dctType2(arr)

	#Modify coefficients if they don't satisfy req for bit value
	while(check_coeff(coeff[u1, v1], coeff[u2,v2], b_msg, P) == False):
		coeff = modify_coeff(coeff, b_msg)

	block = idctType2(coeff) / ((2*n)**(2))

	return block;


def embed_DCT(cover, msg, keyName):
	coverSize = cover.shape

	stego = cover.copy()  #create copy of cover

	binary_msg = msg_encodeBinary(msg)

	msg_len = len(binary_msg)

	num_bits = math.floor(round_down(coverSize[0], n) *  #One bit per 8x8 block
						  round_down(coverSize[1], n) / (n*n)) 

	if (msg_len > num_bits):

		raise ValueError("Message too long")

	order = random.sample(range(0, num_bits), msg_len)

	msg_idx = 0;

	for x in order:
		i = (x // (coverSize[0]//n)) * n
		j = (x % (coverSize[1]//n)) * n

		if (msg_idx >= msg_len):
			break

		stego[i:(i+n), j:(j+n)] = embed_bit(cover[i:(i+n), j:(j+n)], \
											   binary_msg[msg_idx], thresh)

		msg_idx = msg_idx + 1

	orderString = " ".join(map(str,order))
	byteString = bytes(orderString, "utf-8")	  #Must be byte array to encrpt
	key = ChaCha20Poly1305.generate_key() #User keeps this
	chacha = ChaCha20Poly1305(key)
	nonce = os.urandom(12) 	#User keeps this
	ct = chacha.encrypt(nonce, byteString, bytes(keyName, "utf-8")) #User keeps this

	return stego, ct, key, nonce

def extract_bit(arr):
	coeff = dctType2(arr)
	if (abs(coeff[u1, v1]) - abs(coeff[u2, v2]) > 0):
		return '0'
	else:
		return '1'


def extract_DCT(stego, ct, key, nonce, keyName):
	stegoSize = stego.shape

	chacha = ChaCha20Poly1305(key)

	decryptString = chacha.decrypt(nonce, ct, bytes(keyName, "utf-8"))

	decodeString = decryptString.decode("utf-8")

	order = list(map(int, decodeString.split()))

	msg_bits = ['']
	
	for x in order:
		i = (x // (stegoSize[0]//n)) * n
		j = (x % (stegoSize[1]//n)) * n
		msg_bits.append(extract_bit(stego[i:(i+8), j:(j+8)]))

	msg = ''.join(msg_bits)

	return msg_decodeBinary(msg)


if __name__ == "__main__":
	import sys
	if (len(sys.argv) < 2):
		raise ValueError("Please provide the cover image file, \
						  output file name, a message, and name\
						  for your key\n")

	else:
		stegoFile = sys.argv[2]
		msg = sys.argv[3]
		keyName = sys.argv[4]

		cover = imageio.imread(sys.argv[1], pilmode='L')

		print("Inserting watermark into image...\n")

		stego, ct, key, nonce = embed_DCT(cover, msg, keyName)

		print("Writing to ", stegoFile)
		imageio.imwrite(stegoFile, stego, pilmode='L')

		stego = imageio.imread(stegoFile, pilmode='L');

		pyplot.figure(2)

		pyplot.imshow( np.hstack( (cover, stego) ) ,cmap='gray')
		pyplot.show()
		extracted_msg = extract_DCT(stego, ct, key, nonce, keyName)

		print("Extracted message:", extracted_msg)
		if (extracted_msg == msg):
			print("Successfully extracted same message")