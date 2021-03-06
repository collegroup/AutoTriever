


import urllib.parse
import bs4

from . import ProcessorBase



class TgStoryTimeProcessor(ProcessorBase.ProcessorBase):

	log_name = "Main.Processor.TgStoryTime"

	@staticmethod
	def wants_url(lowerspliturl, mimetype):
		if 'text/html' not in mimetype:
			return False

		return lowerspliturl.netloc.endswith("tgstorytime.com")

	def preprocess_content(self, url, lowerspliturl, mimetype, contentstr):
		if not isinstance(contentstr, str):
			return contentstr

		self.log.info("Preprocessing content from URL: '%s'", url)
		if 'This story has explicit content.' in contentstr or\
			'This story has deviant content.' in contentstr:
			self.log.info("Adult clickwrap page. Stepping through")
			contentstr = self.acceptAdult(contentstr, url)
			self.log.info("Retreived clickwrapped content successfully")

		contentstr = contentstr.replace("charset=ISO-8859-1", 'charset=UTF-8')
		return contentstr



	def acceptAdult(self, content, url):

		soup = bs4.BeautifulSoup(content, "lxml")
		newloc = soup.find('div', class_='errormsg')
		if not newloc:
			return content
		newloc = newloc.a['href']
		tgt = urllib.parse.urljoin(url, newloc)
		new = self.wg.getpage(tgt)
		new = self.wg.getpage(url)

		assert 'This story has explicit content.' not in new
		return new

