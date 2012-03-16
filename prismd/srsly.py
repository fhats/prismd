"""Does all the serial things for prismd.

Talks to serial like so:
START(4bits),rgb(12bits),i(8bits),n(8bits).
if n=63, command addresses all lights.

START=0011"""

import struct # :(

import serial # :( :(


# define our format
BITS = { 	# 'n cats
	"START": 4,
	"r": 4,
	"g": 4,
	"b": 4,
	"i": 8,
	"n": 8
}

START_PATTERN = 0b0011		# 3

class OutOfRangeException(Exception):
	pass

def pack_light_data(n, rgbi):
	"""Packs the data given by r,g,b,i for light n into a struct that can be sent over serial.

	TODO(fhats): Investigate whether or not the byte order is a problem."""

	# Do some basic bounds checking, since Python ints can be big and we can only deal with small data
	if any([v > 2**BITS[k] - 1 for k,v in rgbi.iteritems()]):
		raise OutOfRangeException

	# Do some shiftery to truncate shit and pack it
	start_r = START_PATTERN | rgbi['r'] << 4
	g_b = rgbi['b'] << 4 | rgbi['g']

	return struct.pack("BBBB", start_r, g_b, rgbi['i'], n)

def write_light_cmd(srl, packed_cmd):
	srl.write(packed_cmd)

	# find out how many bytes were read
	output = srl.readline()
	bytes = int(output)
	return bytes
