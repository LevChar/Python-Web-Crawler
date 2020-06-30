from urllib.parse import urlparse, urlsplit, urlunsplit
from queue import PriorityQueue
from bs4 import BeautifulSoup
import threading
import logging
import Logger
import Utils
import time

class IllegalArgumentError(ValueError):
	pass

class crawler:
    valid_links = dict([])
    valid_not_folowed_links = dict([])
    valid_file_links = dict([])
    broken_links = dict([])
    treated_urls = set([])
    active_threads = 0
    output_file = None

    def __init__(self, domain=None, num_workers = 5000, max_queue_size = 10000, output=None, log=1):
        self.start = time.time()
        self.link_q = PriorityQueue(maxsize=max_queue_size)
        self.max_threads = num_workers
        self.output = output
        self.domain = domain
        self.logger = Logger.init_logger(log)
        self.logger.error("Execution started")
        self.logger.error("Initializing...\n")

        try:
            parsed_url = urlparse(domain)
            self.target_tld = Utils.parse_targets_tld(parsed_url.netloc)
            self.scheme = parsed_url.scheme
        except:
            raise IllegalArgumentError("Invalid domain")

        self.output_file = Utils.create_results_file(self.output)

        self.not_treated_extensions = (".epub", ".mobi", ".docx", ".doc", ".opf", ".7z",
                                  ".ibooks", ".cbr", ".avi", ".mkv", ".mp4", ".jpg",
                                  ".jpeg", ".png", ".gif", ".pdf", ".iso", ".rar",
                                  ".tar", ".tgz", ".zip", ".dmg", ".exe")

        # Error codes by: https://www.deadlinkchecker.com/error-codes.asp
        self.broken_link_codes = [300,301,302,303,304,305,307,308,400,401,402,403,404,
                405,406,407,408,409,410,411,412,413,414,415,416,417,
                420,422,423,424,429,431,450,500,501,502,503,504,505,
                506,507,509,510,"Timeout"]

        self.link_q.put((0, domain))

    def crawl(self):
        amt_of_threads = len(threading.enumerate())
        # when run in debug mode there are 3 additional threads which are started by py charm:
        # (WriterThread, ReaderThread and PyDBCommandThread) in addition to main thread, in other IDE's
        # there might be other situation, in any case, this variable is allowing us to catch the right moment
        # when only the main thread left and the Q is empty.

        self.logger.error(f"Started Crawling of: domain: {self.domain} || Max allowed threads: {self.max_threads}\n")
        while(not self.link_q.empty() or threading.active_count() > amt_of_threads):
            if(not self.link_q.empty()):
                if (threading.active_count() < self.max_threads):
                    try:
                        wrapped_url = self.link_q.get()
                        threading.Thread(target=self.process_url, args=(wrapped_url,)).start()
                    except PriorityQueue.Empty:
                        continue
            self.logger.warning(f"IN MAIN LOOP: Q SIZE: {self.link_q.qsize()}  WORKERS: {threading.active_count()}")
            time.sleep(0.0001)  #intentional delay to slow the main thread down little bit (save cpu)
        self.link_q.join()
        self.logger.error(f"Finished Crawling of: domain: {self.domain}")
        Utils.write_output(self.output_file, self.valid_links, self.broken_links, self.valid_not_folowed_links, self.valid_file_links)
        end_time = time.time()
        total_time = end_time - self.start
        self.logger.error(f"\nExecution finished")
        self.logger.error(f"Execution took: --- {total_time} seconds ---\n")

    def process_url(self, url_object):      # url_object is (level:int, url:string)
        try:
            html = Utils.open_url(url_object)
            if (html.status_code in self.broken_link_codes):
                raise IllegalArgumentError("Wrong Link!!!")
            parsed_html = BeautifulSoup(html.content.decode('utf-8', 'ignore'), 'lxml')

            for link in parsed_html.findAll('a'):
                current_link = link.attrs.get('href')
                if(current_link is None or current_link == ""):
                    continue
                url_obj = Utils.check_and_fix_link(url_object[1], current_link)  # url_obj (type: str, link: str)

                self.logger.info(f"Current link is: {url_obj[1]} and the page it came from is: {url_object[1]}")

                if (url_obj[0] == "ignore"):
                    continue

                if (url_obj[1] not in self.treated_urls):
                    self.treated_urls.add(url_obj[1])
                else:
                    continue

                if(url_obj[0] == "not_to_folow"):
                    if url_obj[1] not in self.valid_not_folowed_links:
                        self.store_valid_not_folowed_link((url_object[0], url_obj[1]))
                        continue

                if (url_obj[1].endswith(self.not_treated_extensions)):
                    if url_obj[1] not in self.valid_file_links:
                        self.store_valid_file_link((url_object[0], url_obj[1]))
                    else:
                        self.check_and_treat_link_second_time(url_obj[1], url_object[0])
                else:
                    if url_obj[1] not in self.valid_links and url_obj[1] not in self.broken_links:
                        self.store_valid_link((url_object[0], url_obj[1]))
                    else:
                        self.check_and_treat_link_second_time(url_obj[1], url_object[0])

                    if (Utils.check_same_domain(self.target_tld, url_obj[1], url_object[1])):
                        self.link_q.put_nowait((url_object[0] + 1, url_obj[1]))  # (Level, url)

        except  IllegalArgumentError as e:
            self.logger.warning(f"Wrong link! => Error: {html.status_code :>4} |>|>|> {url_object[1].center(126)} <|<|<|")
            self.treated_urls.add(url_object[1])
            self.store_broken_link(url_object, str(html.status_code))
        finally:
            self.link_q.task_done()
            self.logger.warning(f"{'Thread:'} {str(threading.current_thread()):<37} finished searching the page! ||| active threads: {threading.active_count():>4}")
            self.logger.error(
                f"{'Q SIZE IS:':<10} {self.link_q.qsize():>4} ||"
                f"{'# Unique visited links:':<23} {len(self.treated_urls):>5} ||"
                f"{'# Ordinary valid links:':<23} {len(self.valid_links):>5} ||"
                f"{'# Valid file links:':<17} {len(self.valid_file_links):>5} ||"
                f"{'# Not followed valid links:':<25} {len(self.valid_not_folowed_links):>5} ||"
                f"{'# Broken links:':<15} {len(self.broken_links):>5}")

    def store_broken_link(self, url_object, error):         # url_object is (level:int, url:string), error:str
        self.broken_links[url_object[1]] = (url_object[0], error)

    def store_valid_link(self, url_object):                 # url_object is (level:int, url:string)
        self.valid_links[url_object[1]] = url_object[0]

    def store_valid_not_folowed_link(self, url_object):     # url_object is (level:int, url:string)
        self.valid_not_folowed_links[url_object[1]] = url_object[0]

    def store_valid_file_link(self, url_object):            # url_object is (level:int, url:string)
        self.valid_file_links[url_object[1]] = url_object[0]

    def check_and_treat_link_second_time(self, url, base_level):
        if url in self.valid_links:
            level_of_stored_url = int(self.valid_links[url])
            if (base_level+1) < level_of_stored_url:
                self.valid_links[url] = base_level+1
        elif url in self.broken_links:
            level_of_stored_url = int(self.broken_links[url][0])
            if (base_level + 1) < level_of_stored_url:
                self.broken_links[url][0] = base_level + 1
        else:
            level_of_stored_url = int(self.valid_file_links[url])
            if (base_level + 1) < level_of_stored_url:
                self.valid_file_links[url] = base_level + 1