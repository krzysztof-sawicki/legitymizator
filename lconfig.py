import json
import os

class lConfig:
	configFile = os.path.join(os.path.expanduser("~"), ".legitymizator")
	defaultConfig = {"lastDB": ""}

	@staticmethod
	def initializeConfig():
		if not os.path.exists(lConfig.configFile):
			lConfig.saveConfig(lConfig.defaultConfig)

	@staticmethod
	def loadConfig():
		lConfig.initializeConfig()
		with open(lConfig.configFile, 'r') as f:
			return json.load(f)

	@staticmethod
	def saveConfig(config):
		with open(lConfig.configFile, 'w') as f:
			json.dump(config, f, indent=4, separators=(',', ': '))

	@staticmethod
	def getField(fieldName):
		config = lConfig.loadConfig()
		return config.get(fieldName, None)

	@staticmethod
	def updateField(fieldName, value):
		config = lConfig.loadConfig()
		config[fieldName] = value
		lConfig.saveConfig(config)
