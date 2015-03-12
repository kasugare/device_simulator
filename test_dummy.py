import sys
import json
import math
import time
import httplib

import struct 
#import numpy
import socket
import random

class EDM1:
	SERVER_IP 	= 'localhost'
	SERVER_PORT	= 5010
	FIELD_SEP	= ' '

	def __init__(self, site_id='10000062', device_id='1668', api_key='EDM1a'):
		self.site_id 	= (site_id,)
		self.device_id 	= (device_id,)
		self.api_key	= (api_key,)
		print self.api_key

	def set_data(self, rows):

		# initialize data
		self.data_time		= 0
		self.current		= [0,]*24
		self.active_power	= [0,]*24
		self.reactive_power	= [0,]*24
		self.apparent_power	= [0,]*24

		# set data to the list
		for line in rows:
			try:
				arr = line.split(self.FIELD_SEP)

				timestamp 		= int(arr[0])
				feeder_id 		= int(arr[1])
				active_power 	= int(float(arr[2])*10)
				reactive_power	= int(float(arr[3])*10)
				apparent_power 	= int(math.sqrt(active_power**2+reactive_power**2))
				current 		= int(apparent_power/10./220.*10000.)

				self.current[feeder_id] 		= current
				self.active_power[feeder_id]	= active_power
				self.reactive_power[feeder_id]	= reactive_power
				self.apparent_power[feeder_id]	= apparent_power

				self.data_time					= timestamp

				#print self.data_time, self.current[feeder_id], self.active_power[feeder_id], self.reactive_power[feeder_id]
			except Exception as inst:
				print inst 
				print 'set data error'
				print line


	def send_data(self):

		# Reference:
		# http://pymotw.com/2/struct/
		#
		# Test example:
		#values = (1,'ab',2.7)
		#s = struct.Struct('! I 2s f')
		#packed_data = s.pack(*values)
		#

		# dummy for now
		frequency 		= (60 * 1000,)
		voltage			= (220 * 1000, ) * 3

		power_factor	= (0,)*24
		accum_usage		= (0,)*24

		# formatting the data
		values = frequency + voltage 
		values = values + tuple(self.current) + power_factor + accum_usage 
		values = values + tuple(self.apparent_power) + tuple(self.reactive_power) + tuple(self.active_power) + accum_usage 

		#values_uint = struct.unpack_from("196I", struct.pack("196i", *values)) + self.api_key + self.site_id + self.device_id
		#values_uint = values + self.api_key + self.site_id + self.device_id

		values_uint = values + self.api_key + self.site_id + self.device_id
		print "----------------------------------------"
		print values_uint
		print "----------------------------------------"
		struct_fmt = struct.Struct('< I 3I 24I 24I 24Q 24I 24I 24I 24Q 32s 24s 24s')
		data_to_send = struct_fmt.pack(*values_uint) 

		#print data_to_send
		
		# send data to server
		try:
			soc=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			soc.connect((self.SERVER_IP,self.SERVER_PORT))
			soc.send( data_to_send )
			print soc.recv(1024).strip()
			soc.close()

			print 'send complete'
		except Exception as inst:
			print inst
			print 'send error'	

def _test_EDM1():
	c = EDM1()

	for i in range(0,100):
		p1 = int(200*random.random())
		q1 = int(p1*0.1)

		p2 = int(100)
		q2 = int(p2*0.1)

		rows=[
			(str(int(time.time())*1000) + ' 0 ' + str(p1) + ' ' + str(q1)),
			(str(int(time.time())*1000) + ' 1 ' + str(p2) + ' ' + str(q2))
			]

		c.set_data(rows)
		c.send_data()

		time.sleep(1.0)


if __name__ == "__main__":
    _test_EDM1()


