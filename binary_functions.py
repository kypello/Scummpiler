import math

def signed_decode(value):
    return ((value & 0x8000) >> 15) * -0x8000 + (value & 0x7fff)

def signed_encode(value):
    return ((value & 0x80000000) >> 16) + (value & 0x7fff)



def le_encode(value, word_size):
    bytes = []

    for i in range(word_size):
        bytes.append((value & (0xff * int(math.pow(0x100, i)))) >> (8 * i))
    
    return bytes

def le_decode(bytes, word_size):
    value = 0

    for i in range(word_size):
        value += bytes[i] * int(math.pow(0x100, i))
    
    return value

def be_encode(value, word_size):
    bytes = []

    i = word_size - 1
    while i >= 0:
        bytes.append((value & (0xff * int(math.pow(0x100, i)))) >> (8 * i))
        i -= 1
    
    return bytes

def be_decode(bytes, word_size):
    value = 0

    for i in range(word_size):
        value += bytes[word_size - 1 - i] * int(math.pow(0x100, i))
    
    return value
