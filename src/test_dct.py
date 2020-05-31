from dct import extract_DCT
from dct import embed_DCT
import imageio
import sys
import os

file = "test"

def test_compression(cover, msg, threshold):
	print("\nBeginning compression tests\n")

	for rate in range(10, 110, 10):
		stego, key, encoded_text, order = embed_DCT(cover, msg, threshold)

		#Writeback as jpg to simulate compression
		imageio.imwrite(file + ".jpg", stego, pilmode='L', quality= rate)

		stegojpg = imageio.imread(file + ".jpg", pilmode='L')

		try:
			extracted_msg = extract_DCT(stegojpg, key, encoded_text, order)
			if (extracted_msg == msg):
				print("\tCompression Rate:", rate, "Success")
			else:
				print("\tCompression Rate:", rate, "Failed")
		except:
			print("\tCompression Rate:", rate, "Failed")


	if os.path.exists(file + ".jpg"):
		print("\nDeleting test image\n")
		os.remove(file + ".jpg")
	else:
		print("The file does not exist")

def main():
	if (len(sys.argv) < 3):
			raise ValueError("Please provide the cover image file, threshold, \
							 and a message\n")
	cover = imageio.imread(sys.argv[1], pilmode='L')
	threshold = int(sys.argv[2])
	msg = sys.argv[3]
	i = len(msg)
	while i < 50:
		msg += " "
		i = len(msg)
	test_compression(cover, msg, threshold)

main()