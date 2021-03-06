#!/usr/bin/env python3
import os
import traceback

from . import client
from . import plugin_loader

class RpcCallDispatcher(client.RpcHandler):
	'''
	dispatch calls.

	Call dispatch is done dynamically, by looking up methods in dynamically loaded plugins.

	'''


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.log.info("Loading plugins from disk.")
		self.plugins = plugin_loader.loadPlugins('modules', "PluginInterface_")
		self.log.info("Total loaded plugins pre-init: %s", len(self.plugins))
		for plugin_name in list(self.plugins.keys()):

			# Instantiate the initialization class
			p = self.plugins[plugin_name](settings=self.settings)
			self.log.info("Plugin '%s' provides the following %s calls:", plugin_name, len(p.calls))
			for call_name in p.calls.keys():
				self.log.info("	Call: '%s'", call_name)

			if '__setup__' in p.calls:
				# and then call it's setup method
				try:
					p.calls['__setup__']()
				except Exception:
					self.log.error("Plugin failed to initialize: '%s'. Disabling!", plugin_name)
					for line in traceback.format_exc().split("\n"):
						self.log.error("	%s", line.rstrip())
					self.plugins.pop(plugin_name)


		self.log.info("Active post-init plugins: %s", len(self.plugins))
		for item in self.plugins.keys():
			self.log.info("Enabled plugin: '%s'", item)
		self.classCache = {}


	def doCall(self, module, call, call_args, call_kwargs, context_responder, lock_interface):
		if not module in self.classCache:
			self.log.info("First call to module '%s'", module)
			self.classCache[module] =  self.plugins[module](settings=self.settings)
			self.log.info("Module provided calls: '%s'", self.classCache[module].calls.keys())

		self.log.info("Calling module '%s'", module)
		self.log.info("internal call name '%s'", call)
		self.log.info("Args '%s'", call_args)
		self.log.info("Kwargs '%s'", call_kwargs)


		have_lock = False
		if self.plugins[module].serialize:
			self.log.info("Module has a locking interface. Serializing.")
			have_lock = self.plugins[module].get_lock()
			if not have_lock:
				raise client.CannotHandleNow



		if hasattr(self.classCache[module], "can_send_partials"):
			call_kwargs['partial_resp_interface'] = context_responder

		if hasattr(self.classCache[module], "can_handle_locks"):
			call_kwargs['lock_interface'] = lock_interface

		if not call in self.classCache[module].calls:
			self.log.error("Call %s missing from target class!", call)
			self.log.error("Available calls:")
			for callname in self.classCache[module].calls.keys():
				self.log.error("	-> %s", callname)

		try:
			ret = self.classCache[module].calls[call](*call_args, **call_kwargs)
		finally:
			self.log.info("Module call complete.")

			if have_lock:
				self.plugins[module].free_lock()

		return ret

	def process(self, command, context_responder, lock_interface):
		if not 'module' in command:
			self.log.error("No 'module' in message!")
			self.log.error("Message: '%s'", command)

			ret = {
				'success'     : False,
				'error'       : "No module in message!",
				'cancontinue' : True
			}
			return ret

		if not 'call' in command:
			self.log.error("No 'call' in message!")

			ret = {
				'success'     : False,
				'error'       : "No call in message!",
				'cancontinue' : True
			}
			return ret

		args = []
		kwargs = {}
		if 'args' in command:
			args = command['args']
		if 'kwargs' in command:
			kwargs = command['kwargs']

		ret = self.doCall(
				module            = command['module'],
				call              = command['call'],
				call_args         = args,
				call_kwargs       = kwargs,
				context_responder = context_responder,
				lock_interface    = lock_interface
			)

		# print(ret)
		response = {
			'ret'          : ret,
			'success'      : True,
			'cancontinue'  : True,
			'dispatch_key' : command['dispatch_key'],
			'module'       : command['module'],
			'call'         : command['call'],
		}

		return response


def test(plug_name=None, call_name=None, *args, **kwargs):
	import deps.logSetup
	import logging
	log = logging.getLogger("Main.Importer")
	deps.logSetup.initLogging()
	log.info("Testing import options")

	dp = RpcCallDispatcher(settings=None, lock_dict=None)

	if not plug_name:
		return

	print("Invoking arguments: '%s'" % (args, ))
	print("Invoking kwargs: '%s'" % (kwargs, ))
	return dp.doCall(plug_name, call_name, call_args=args, call_kwargs=kwargs, context_responder=None, lock_interface=None)

	# plugins = loadPlugins('modules', "PluginInterface_")

	# print("plugins:", plugins)

	# for plugin in plugins:
	# 	print("Plugin: ", plugin)

if __name__ == "__main__":
	test()