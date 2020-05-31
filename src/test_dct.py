from dct import extract_DCT
from dct import embed_DCT
import imageio
import sys
import os

file = "test"

def test_compression(cover, msg, threshold):
	print("\nBeginning compression tests")

	for rate in range(10, 110, 10):
		match = False

		stego, key, encoded_text, order = embed_DCT(cover, msg, threshold)

		#Writeback as jpg to simulate compression
		imageio.imwrite(file + ".jpg", stego, pilmode='L', quality= rate)

		stegojpg = imageio.imread(file + ".jpg", pilmode='L')

		try:
			extracted_msg = extract_DCT(stegojpg, key, encoded_text, order)
			print("\tRecovered Messages:")
			for x in extracted_msg:
				print("\t\t", x)
				if (x == msg):
					match = True

			if (match):
				print("\tCompression Rate:", rate, "Success\n")
			else:
				print("\tCompression Rate:", rate, "Failed\n")
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
	msg = sys.argv[3].rstrip('\n')
	
	test_compression(cover, msg, threshold)

main()