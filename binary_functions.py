def le_decode(bytes):
    return bytes[1] * 0x100 + bytes[0]

def le_encode(value):
    return [value & 0xff, (value & 0xff00) >> 8]

def le_encode_32(value):
    return [value & 0xff, (value & 0xff00) >> 8, (value & 0xff0000) >> 16, (value & 0xff000000) >> 24]

def be_encode_32(value):
    return [(value & 0xff000000) >> 24, (value & 0xff0000) >> 16, (value & 0xff00) >> 8, value & 0xff]

def signed_decode(value):
    return ((value & 0x8000) >> 15) * -0x8000 + (value & 0x7fff)

def signed_encode(value):
    return ((value & 0x80000000) >> 16) + (value & 0x7fff)