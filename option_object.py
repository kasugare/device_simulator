import random

class OptionObject:
	def __init__(self, apikey, sid, did, sp, interval):
		if sid == 'random':
			sid = random.randrange(9000000, 90001000)
		if did == 'random':
			did = random.randrange(10000, 20000)
		self.apikey = apikey
		self.sid = int(sid)
		self.did = int(did)
		self.sp = int(sp)
		self.interval = int(interval)

	def getOptions(self):
		return self.apikey, self.sid, self.did, self.sp, self.interval

	def getApikey(self):
		return self.apikey

	def getSid(self):
		return self.sid

	def getDid(self):
		return self.did

	def getSampingPeriod(self):
		return self.sp

	def getInterval(self):
		return self.interval

	def hasApikey(self, apikey):
		if self.apikey == apikey:
			return True
		return False

	def hasSid(self, sid):
		if self.sid == sid:
			return True
		return False

	def hasDid(self, did):
		if self.did == did:
			return True
		return False