from optparse import OptionParser
from option_parser import UserOptionParser
import ConfigParser
import math, random, time
import sys, traceback, os
import socket, threading
import struct
from Queue import Queue

THREAD_STATUS = True
DATA_QUEUE = Queue()

class EdmDataSimulator:
	SERVER_IP 	= 'localhost'
	SERVER_PORT	= 0

	def __init__(self):
		self.__config__()
		user_option_parser = UserOptionParser()
		self.user_options, self.option_obj = user_option_parser.getOptions()
		self.__doProcess__()

	def __config__(self, config_section = 'SERVER'):
		config_path = './conf/conf.ini'
		config = ConfigParser.RawConfigParser()
		config.read(config_path)
		self.SERVER_IP = config.get(config_section, 'host')
		self.SERVER_PORT = int(config.get(config_section, 'port'))

	def __doProcess__(self):
		thread_list = []
		
		for index in range(len(self.option_obj)):
			apikey, sid, did, sp, interval = self.option_obj[index].getOptions()

			thread_obj = threading.Thread(target=self.doGeneration, args=(apikey, sid, did, sp, interval))
			thread_obj.setDaemon(1)
			thread_obj.start()
			thread_obj.setName("%s_%s" %(sid, did))
			thread_list.append(thread_obj)
		
		thread_print = threading.Thread(target=self.setResultDataThread, args=())
		thread_print.setDaemon(1)
		thread_print.start()

		while True:
			user_query = raw_input("[Quit] pleased, if you want to quit, press 'q' or 'Q' : ")
			if user_query == 'q' or user_query == 'Q':
				THREAD_STATUS = False
				sys.exit(1)
		
	def doGeneration(self, apikey, sid, did, sp, interval = 0):
		prev_watt_hour = []
		prev_timestamp = 0
		isStarted = False

		while THREAD_STATUS:
			voltage = self.genVoltage()
			device_info = self.genDefaultFeederData()
			
			if isStarted == False:
				history_path = './conf/history.log'
				history = ConfigParser.RawConfigParser()
				history.read(history_path)
				section = "%d_%d" %(sid, did)
				if history.has_section(section):
					prev_watt_hour = history.get(section, 'watt_hour')
					prev_watt_hour = self.convertStringToIntegerList(prev_watt_hour)
					prev_timestamp = history.get(section, 'timestamp')
				else:
					prev_watt_hour = device_info['watt_hour']
					prev_timestamp = int(time.time())
				isStarted = True

			act_pwrs = device_info['app_pwr']
			curr_watt_hour = self.calWattHourByActPwr(act_pwrs, prev_watt_hour)
			curr_timestamp = int(prev_timestamp) + interval

			device_info['watt_hour'] = curr_watt_hour
			device_info['freq'] = curr_timestamp
			device_info['sid'] = str(sid)
			device_info['did'] = str(did)
			device_info['apikey'] = apikey
			device_info['voltage'] = voltage
			device_info['sp'] = sp

			hexDummyData = self.converHexFormat(device_info)
			self.sendHexData(hexDummyData)
			prev_watt_hour = curr_watt_hour
			prev_timestamp = curr_timestamp
			time.sleep(sp)

	def convertStringToIntegerList(self, items):
		convertItems = []
		items = items.split(',')
		for item in items:
			convertItems.append(int(item))
		return convertItems

	def calWattHourByActPwr(self, act_pwrs, prev_watt_hour):
		curr_watt_hour = []
		for index in range(len(act_pwrs)):
			act_pwr = act_pwrs[index]
			watt_hour = int(prev_watt_hour[index]) + float(act_pwr)/3600
			curr_watt_hour.append(int(watt_hour))
		return curr_watt_hour

	def converHexFormat(self, device_info):
		dummyData = device_info['freq'],
		dummyData += device_info['voltage']
		dummyData += tuple(device_info['curr_pwr'])
		dummyData += tuple(device_info['pwr_fact'])
		dummyData += tuple(device_info['firm_total'])
		dummyData += tuple(device_info['app_pwr'])
		dummyData += tuple(device_info['ract_pwr'])
		dummyData += tuple(device_info['act_pwr'])
		dummyData += tuple(device_info['watt_hour']) # ic_total_usage
		dummyData += device_info['apikey'],
		dummyData += device_info['sid'],
		dummyData += device_info['did'],
		dummyData += device_info['sp'],
		
		struct_fmt = struct.Struct('< I 3I 24I 24I 24Q 24I 24I 24I 24Q 32s 24s 24s I')
		hexData = struct_fmt.pack(*dummyData)
		DATA_QUEUE.put(dummyData)
		return hexData

	def genDefaultFeederData(self):
		feederValueKeys = ['pwr_fact', 'firm_total', 'watt_hour']
		defaultFeederInfo = {}
		defaultValue = [0,] * 24

		for valueKey in feederValueKeys:
			defaultFeederInfo[valueKey] = defaultValue
		act_pwrs, ract_pwrs, app_pwrs, curr_pwrs = self.genPowerData()

		defaultFeederInfo['act_pwr'] = act_pwrs
		defaultFeederInfo['ract_pwr'] = ract_pwrs
		defaultFeederInfo['app_pwr'] = app_pwrs
		defaultFeederInfo['curr_pwr'] = curr_pwrs
		return defaultFeederInfo

	def genVoltage(self):
		voltage = (int(200 * random.random()), int(200 * random.random()), int(200 * random.random()))
		return voltage

	def genPowerData(self):
		apikey = self.user_options.get('apikey')
		act_pwrs = []
		ract_pwrs = []
		app_pwrs = []
		curr_pwrs = []

		for i in range(0, 24):
			act_pwr, ract_pwr, app_pwr, curr_pwr = self.calPowerData()
			act_pwrs.append(act_pwr)
			ract_pwrs.append(ract_pwr)
			app_pwrs.append(app_pwr)
			curr_pwrs.append(curr_pwr)

		if apikey is 'EDM1a':
			return self.calEdm1aTotal(act_pwrs, ract_pwrs, app_pwrs, curr_pwrs)
		elif apikey is 'EDM1b':
			return self.calEdm1bTotal(act_pwrs, ract_pwrs, app_pwrs, curr_pwrs)
		return act_pwrs, ract_pwrs, app_pwrs, curr_pwrs

	def calEdm1aTotal(self, act_pwrs, ract_pwrs, app_pwrs, curr_pwrs):
		three_act_total = sum(act_pwrs[3:len(act_pwrs)])
		three_ract_total = sum(ract_pwrs[3:len(ract_pwrs)])
		three_app_total = sum(app_pwrs[3:len(app_pwrs)])
		three_curr_total = sum(curr_pwrs[3:len(curr_pwrs)])

		each_act = three_act_total/3
		each_ract = three_ract_total/3
		each_app = three_app_total/3
		each_curr = three_curr_total/3

		first_act = each_act + three_act_total - (each_act * 3)
		first_ract = each_ract + three_ract_total - (each_ract * 3)
		first_app = each_app + three_app_total - (each_app * 3)
		first_curr = each_curr + three_curr_total - (each_curr * 3)

		act_pwrs[0] = first_act
		ract_pwrs[0] = first_ract
		app_pwrs[0] = first_app
		curr_pwrs[0] = first_curr

		act_pwrs[1] = act_pwrs[2] = each_act
		ract_pwrs[1] = ract_pwrs[2] = each_ract
		app_pwrs[1] = app_pwrs[2] = each_app
		curr_pwrs[1] = curr_pwrs[2] = each_curr
		return act_pwrs, ract_pwrs, app_pwrs, curr_pwrs


	def calEdm1bTotal(self, act_pwrs, ract_pwrs, app_pwrs, curr_pwrs):
		single_act_total = sum(act_pwrs[1:len(act_pwrs)])
		single_ract_total = sum(ract_pwrs[1:len(ract_pwrs)])
		single_app_total = sum(app_pwrs[1:len(app_pwrs)])
		single_curr_total = sum(curr_pwrs[1:len(curr_pwrs)])

		act_pwrs[0] = single_act_total
		ract_pwrs[0] = single_ract_total
		app_pwrs[0] = single_app_total
		curr_pwrs[0] = single_curr_total
		return act_pwrs, ract_pwrs, app_pwrs, curr_pwrs


	def calPowerData(self):
		def_pwr = int(200 * random.randrange(3000, 50000))
		act_pwr = float(def_pwr * 10)
		ract_pwr = float(def_pwr)
		app_pwr = int(math.sqrt(act_pwr ** 2 + ract_pwr ** 2))
		curr_pwr = int(app_pwr / 10. / 220. * 10000.)
		return act_pwr, ract_pwr, app_pwr, curr_pwr

	def sendHexData(self, dummyData):
		try:
			soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			soc.connect((self.SERVER_IP, self.SERVER_PORT))
			soc.send(dummyData)
			soc.close()
		except Exception, e:
			print traceback.format_exc(e)

	def setResultDataThread(self):
		while True:
			if DATA_QUEUE.qsize() > 0:
				rawData = DATA_QUEUE.get()
				if self.user_options.get('mode') == 'constant':
					timestamp = rawData[0]
					sid = rawData[173]
					did = rawData[174]
					currWattHours = self.convertIntigerToStringList(rawData[148:172])
					self.saveHistory(timestamp, sid, did, currWattHours)
					
				if self.user_options.get('verbose'):
					self.printMessage(rawData)

	def saveHistory(self, timestamp, sid, did, watt_hours):
		history_path = './conf/history.log'
		history = ConfigParser.RawConfigParser()
		watt_hours = ','.join(watt_hours)

		section = '%s_%s' %(sid, did)
		history.read(history_path)
		if history.has_section(section):
			history.remove_section(section)
			with open(history_path, 'wb') as historyfile:
				history.write(historyfile)

		history.add_section(section)
		history.set(section, 'timestamp', timestamp)
		history.set(section, 'sid', sid)
		history.set(section, 'did', did)
		history.set(section, 'watt_hour', watt_hours)
		with open(history_path, 'wb') as historyfile:
			history.write(historyfile)

	def convertIntigerToStringList(self, items):
		convertItems = []
		for item in items:
			convertItems.append(str(item))
		return convertItems

	def printMessage(self, rawData):
		print rawData, "\n"


if __name__ == "__main__":
    EdmDataSimulator()

