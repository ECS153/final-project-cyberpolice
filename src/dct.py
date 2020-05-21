import os
import random
import time
import sys
from PIL import Image
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import numpy as np
import matplotlib.pyplot as pyplot
import scipy
import imageio

from numpy import pi
from numpy import sin
from numpy import zeros
from numpy import r_
from scipy import signal
from scipy import misc 
import matplotlib.pylab as pylab
from scipy.fftpack import dct
from scipy.fftpack import idct

u1 = 5
v1 = 4  #Middle band coordinates
u2= 4
v2 = 5

n = 8 # 8x8 pixel block

thresh = 500  #Threshold

def double_to_byte(arr):
    return np.uint8(np.round(np.clip(arr, 0, 255), 0))

def dctType2(a):
	return dct(dct(a, axis=0), axis=1)

def idctType2(a):
	return idct(idct(a, axis=0), axis=1)


def msg_to_binary(msg):
	binary_msg = msg.encode()
	binary_int = int.from_bytes(binary_msg, "big") 
	return bin(binary_int)[2:]

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

def embed_DCT(cover, msg):
	coverSize = cover.shape
	stego = cover.copy()  #create copy of cover

	binary_msg = msg_to_binary(msg)

	msg_len = len(binary_msg)

	num_bits = (coverSize[0] * coverSize[1]) / 64 #One bit per 8x8 block

	if (msg_len > num_bits):
		print("Message too long")
		return None

	msg_idx = 0;

	for i in range(0, coverSize[0] - n, n):
		for j in range(0, coverSize[1] - n, n):
			if (msg_idx >= msg_len):
				break

			stego[i:(i+n), j:(j+n)] = embed_bit(cover[i:(i+n), j:(j+n)], \
											   binary_msg[msg_idx], thresh)

			msg_idx = msg_idx + 1
		else:
			continue
		break

	return stego;

def extract_bit(arr):
	coeff = dctType2(arr)
	if (abs(coeff[u1, v1]) - abs(coeff[u2, v2]) > 0):
		return '0'
	else:
		return '1'


def extract_DCT(stego):
	stegoSize = stego.shape


	msg_len = len(msg_to_binary("fjnieahfioelhafiealhfiehaefea"))  #Will come from key

	msg_bits = ['']

	block_idx = np.arange(0, msg_len)  #Will come from key
	
	for x in block_idx:
		i = (x // (stegoSize[0]//n)) * n
		j = (x % (stegoSize[1]//n)) * n
		msg_bits.append(extract_bit(stego[i:(i+8), j:(j+8)]))

	msg = ''.join(msg_bits)

	msg_int = int(msg, 2)

	msg_num_bytes = msg_int.bit_length() + 7 // 8

	msg_bytes = msg_int.to_bytes(msg_num_bytes, "big")

	return msg_bytes.decode().lstrip('\x00')


def main():

	if (len(sys.argv) < 1):
		raise WrongNumberofArguments("Please provide the cover image file \
										and a message\n")

	else:
		cover = imageio.imread(sys.argv[1], as_gray=1)


		print("Inserting watermark into image...\n")

		stego = embed_DCT(cover, sys.argv[2])

		pyplot.figure(2)

		pyplot.imshow( np.hstack( (cover, stego) ) ,cmap='gray')
		pyplot.show()

		print("Extracted message: ", extract_DCT(stego))
	
			
main()