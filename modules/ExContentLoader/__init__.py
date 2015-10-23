
import modules.ExContentLoader.ExContentLoader

class PluginInterface_ExContentLoader(modules.ExContentLoader.ExContentLoader.ExContentLoader):

	name = 'ExContentLoader'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.checkLogin()


		self.calls = {
			'getpage'               : self.wg.getpage,
			'fetchcontent'          : self.getLink,
		}

