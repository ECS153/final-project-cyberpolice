from PIL import Image
import sys

def encode(coverImage, msg):
  byte_array = msg.encode()
  binary_int = int.from_bytes(byte_array, "big")
  binary_string = bin(binary_int)[2:] + '1111111111111110'
  n = coverImage.size[0] * coverImage.size[1]
  if len(binary_string) > 3 * n:
    print('Message too long')
    return None
  coverBands = (coverImage.getdata(0), coverImage.getdata(1), coverImage.getdata(2))
  newRBand = encodeBand(coverBands[0], binary_string[:n])
  newGBand = encodeBand(coverBands[1], binary_string[n:]) if len(binary_string) >= n else coverBands[1]
  newBBand = encodeBand(coverBands[2], binary_string[2 * n:]) if len(binary_string) >= 2 * n else coverBands[2]
  new = Image.new('RGB', coverImage.size)
  newData = zip(newRBand, newGBand, newBBand)
  new.putdata(list(newData))
  return new
  
def decode(coverImage, stegoImage):
  n = stegoImage.size[0] * stegoImage.size[1]
  coverBands = (coverImage.getdata(0), coverImage.getdata(1), coverImage.getdata(2))
  stegoBands = (stegoImage.getdata(0), stegoImage.getdata(1), stegoImage.getdata(2))

  msgBits = '0b'

  for coverBand, stegoBand in zip(coverBands, stegoBands):
    for i in range(n):
      if coverBand[i] != stegoBand[i]:
        msgBits += '1'
      else:
        msgBits += '0'
  delimiterIndex = msgBits.find('1111111111111110')
  binary_int = int(msgBits[:delimiterIndex], 2)
  byte_number = binary_int.bit_length() + 7 // 8
  binary_array = binary_int.to_bytes(byte_number, "big")
  return binary_array.decode().lstrip('\x00')

def encodeBand(band, bits):
  if len(bits) == 0:
    return band
  newBand = list(band)
  for i, bit in enumerate(bits):
    bandBits = bin(band[i])
    newBit = 1 - int(bandBits[-1]) if bit == '1' else int(bandBits[-1])
    bandBits = bandBits[:-1] + str(newBit)
    newBand[i] = int(bandBits, 2)
  return newBand

if __name__ == "__main__":
  if (len(sys.argv) < 2):
    print("""Commands:
    encode <cover image path> <message> <output stego image path>
    decode <stego image path> <cover image>
    """)
  else:
    if (sys.argv[1]) == 'encode':
      coverImage = Image.open(sys.argv[2])
      msg = sys.argv[3]
      stegoImage = encode(coverImage, msg)
      stegoImage.save(sys.argv[4])
    elif (sys.argv[1]) == 'decode':
      coverImage = Image.open(sys.argv[3])
      stegoImage = Image.open(sys.argv[2])
      msg = decode(coverImage, stegoImage)
      print(msg)