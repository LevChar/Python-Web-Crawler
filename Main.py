import Args_parser
import Crawler

__title__ = 'Site Crawler [Python]'
__version__ = '0.1.1 Alpha'
__author__ = 'Arie Charfnadel'
__license__ = 'MIT'
__url__ = 'https://github.com/LevChar/Python-Web-Crawler'

if __name__ == '__main__':
    crawl = Crawler.crawler(**Args_parser.args_parser())
    crawl.crawl()
