import struct

def read_short(file):
    return struct.unpack("h", file.read(2))[0]

def read_ushort(file):
    return struct.unpack("H", file.read(2))[0]

def read_string(file):
    read_byte(file)
    stringvariable= b''
    c = None
    while(c != b'\x00'):
        c = file.read(1)
        stringvariable += c
    stringvariable= stringvariable.decode('utf-8').rstrip('\x00')
    return str(stringvariable)


def read_byte(file):
    return struct.unpack("B", file.read(1))[0]

def read_bool(file):
    return struct.unpack("?", file.read(1))[0]

def read_int(file):
    return struct.unpack("i", file.read(4))[0]

def read_uint(file):
    return struct.unpack("I", file.read(4))[0]

def read_float(file):
    return struct.unpack("f", file.read(4))[0]

def read_double(file):
    return struct.unpack("d", file.read(8))[0]

def read_ulong(file):
    return struct.unpack("Q", file.read(8))[0]

def read_bytes(file, numBytes):
	byteBuffer = []
	for x in range(numBytes):
		byteBuffer.append(struct.unpack("B",file.read(1))[0])
	return byteBuffer