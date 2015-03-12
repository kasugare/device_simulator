from optparse import OptionParser
from option_object import OptionObject
import traceback
import sys, copy


class UserOptionParser:
	def __init__(self):
		parser, self.options, self.option_obj = self.__options__()

	def __options__(self):
		usage = """usage: %prog [options] arg1,arg2 [options] arg1 
$ python client_options.py -v -s 123,234 -d 1111,1123 -i 1 -p 1000 -m instance
$ python client_options.py -v --sids=123,234 --dids=1111,1123 --interval=1 -period=1000 -mode=instance"""

		parser = OptionParser(usage = usage)
		parser.add_option("-v", "--verbose",
  			action="store_true", 
  			dest="verbose", 
  			default=False,
  			help="""make lots of noise 
  			[options] -v
  			[default: %default]""")
		parser.add_option("-a", "--apikeys", 
			action="store", 
			dest="apikeys", 
			default="EDM1a",
			help="""device type : EDM1a, EDM1b, EDM1c
			[options] -d EDM1a  or  --devicetype=EDM1a
			[default: %default]""")
		parser.add_option("-s", "--sids", 
			action="store", 
			dest="sids", 
			default="random",
			help="""generated data by site id. It can not use option '-d'.
			[options] -s 1000,1001,1002  or  --sid=1000,1001,1002
			[default: %default]""")
		parser.add_option("-d", "--dids", 
			action="store", 
			dest="dids", 
			default="random",
			help="""generated data by device id. It can not use when sids are over two.
			[options] -d 1234,1235,1236  or  --did=1234,1235,1236
			[default: %default]""")
		parser.add_option("-i", "--interval", 
			action="store", 
			dest="interval", 
			default="1",
			help="""interval time: Assuming that this interval timestamp is in seconds. It will be increated timestamp %default secodns per 1 second.
			[options] -i 1  or  --interval=1
			[default: %default]""")
		parser.add_option("-p", "--period", 
			action="store", 
			dest="period",
			default="1",
			help="""sampling period: : Assuming that this interval timestamp is in seconds
			[options] -p 1  or  --period=1
			[default: %default]""")
		parser.add_option("-m", "--mode",
			action="store",
			dest="mode", 
            default="constant",
            help="""interaction mode: constant, instance
            [options] -m constant or mode=constant
            [default: %default]""")
		
		(options, args) = parser.parse_args()
		user_options = {}
		user_options['verbose'] = options.verbose
		user_options['mode'] = options.mode
		user_options['apikeys'] = options.apikeys.split(':')
		user_options['sids'] = options.sids.split(',')
		user_options['dids'] = options.dids.split(':')
		user_options['sps'] = options.period.split(':')
		user_options['intervals'] = options.interval.split(':')
		
		# if len(user_options['sids']) > 1 and len(user_options['dids']) > 1:
		# 	print "It can not use this options. sids(site ids) are only one when dids are over one or vice versa."
		# 	parser.print_help()
		# 	sys.exit(1)

		if self.vaildOptions(user_options) is False:
			print "[Invalid options] You should be checked with options."
			parser.print_help()
			sys.exit(1)
		option_obj = self.setMappingSidsWithDids(user_options)
		return parser, user_options, option_obj

	def vaildOptions(self, user_options):
		apikeys = user_options.get('apikeys')
		sids = user_options.get('sids')
		dids = user_options.get('dids')
		sps = user_options.get('sps')
		intervals = user_options.get('intervals')
		if len(sids) != len(apikeys) and len(apikeys) != 1:
			print "please check your -s or -k option. 'apikeys' size is one or same 'sids' size"
			return False
		if len(sids) != len(dids) and len(dids) != 1:
			print "please check your -s or -d option. 'dids' size is one or same 'sids' size"
			return False
		if len(sids) != len(sps) and len(sps) != 1:
			print "please check your -s or -p option. 'dids' size is one or same 'sps' size"
			return False
		if len(sids) != len(intervals) and len(intervals) != 1:
			print "please check your -s or -i option. 'dids' size is one or same 'intervals' size"
			return False

		if self.checkDuplicatedItems(apikeys):
			return False
		if self.checkDuplicatedUniqItems(sids):
			return False
		if self.checkDuplicatedItems(dids):
		 	return False
		if self.checkDuplicatedItems(sps):
			return False
		if self.checkDuplicatedItems(intervals):
			return False
		if self.checkValidatedEachOption(user_options) == False:
			return False
		return True

	def checkDuplicatedUniqItems(self, items):
		item_list = copy.copy(items)
		for i in range(len(items)):
			if item_list.__contains__(item_list.pop()):
				print "conflict : ", item_list
				return True
		return False

	def checkDuplicatedItems(self, items):
		item_list = []
		for item in items:
			item_list = item.split(',')
			for i in range(len(item_list)):
				item = item_list.pop()
				if item_list.__contains__(item):
					print "conflict : ", item_list
					return True
		return False

	# TODO: change vaidation checker. 
	def checkValidatedEachOption(self, user_options):
		apikeys = user_options.get('apikeys')
		sids = user_options.get('sids')
		dids = user_options.get('dids')
		sps = user_options.get('sps')
		intervals = user_options.get('intervals')

		try:
			for i in range(len(sids)):
				sid = sids[i]
				didsOfSid = dids[i].split(',')

				for j in range(len(didsOfSid)):
					did = didsOfSid[j]

					if len(apikeys) == 1:
						apikeyOfDid = apikeys[0].split(',')
					else:
						apikeyOfDid = apikeys[i].split(',')
					if len(apikeyOfDid) == 1:
						apikey = apikeyOfDid[0]
					else:
						apikey = apikeyOfDid[j]

					if len(sps) == 1:
						spsOfDid = sps[0].split(',')
					else:
						spsOfDid = sps[i].split(',')
					if len(spsOfDid) == 1:
						sp = spsOfDid[0]
					else:
						sp = spsOfDid[j]

					if len(intervals) == 1:
						intervalOfDid = intervals[0].split(',')
					else:
						intervalOfDid = intervals[i].split(',')
					if len(intervalOfDid) == 1:
						interval = intervalOfDid[0]
					else:
						interval = intervalOfDid[j]
		except Exception, e:
			# print traceback.format_exc(e)
			return False
		return True


	def setMappingSidsWithDids(self, user_options):
		option_objects = []
		apikeys = user_options.get('apikeys')
		sids = user_options.get('sids')
		dids = user_options.get('dids')
		sps = user_options.get('sps')
		intervals = user_options.get('intervals')
		
		for i in range(len(sids)):
			sid = sids[i]
			didsOfSid = dids[i].split(',')

			for j in range(len(didsOfSid)):
				did = didsOfSid[j]

				if len(apikeys) == 1:
					apikeyOfDid = apikeys[0].split(',')
				else:
					apikeyOfDid = apikeys[i].split(',')
				if len(apikeyOfDid) == 1:
					apikey = apikeyOfDid[0]
				else:
					apikey = apikeyOfDid[j]

				if len(sps) == 1:
					spsOfDid = sps[0].split(',')
				else:
					spsOfDid = sps[i].split(',')
				if len(spsOfDid) == 1:
					sp = spsOfDid[0]
				else:
					sp = spsOfDid[j]

				if len(intervals) == 1:
					intervalOfDid = intervals[0].split(',')
				else:
					intervalOfDid = intervals[i].split(',')
				if len(intervalOfDid) == 1:
					interval = intervalOfDid[0]
				else:
					interval = intervalOfDid[j]

				option_objects.append(OptionObject(apikey, sid, did, sp, interval))
		return option_objects

	def getOptions(self):
		return self.options, self.option_obj

	def getOption(self, optionKey = None):
		if optionKey and optionsKey.has_key(optionKey):
			return self.options.get(optionsKey)
		return None


if __name__ == "__main__":
	UserOptionParser()