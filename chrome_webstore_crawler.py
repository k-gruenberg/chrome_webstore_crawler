import argparse
from pathlib import Path
import urllib.request
import shutil
import xml.etree.ElementTree as ET
import random
import tempfile
import time
from typing import List
import re
import sys
from collections import defaultdict
import time



# ToDo: remove temporary .xxx files



class ChromeExtension:
	def __init__(self, extension_id, title="", description="", no_of_users=0, no_of_ratings=0, avg_rating=0.0, version_no="", size="", last_updated="", no_of_languages=0, languages=""):
		self.extension_id = extension_id
		self.title = title
		self.description = description
		self.no_of_users = no_of_users
		self.no_of_ratings = no_of_ratings
		self.avg_rating = avg_rating
		self.version_no = version_no
		self.size = size
		self.last_updated = last_updated
		self.no_of_languages = no_of_languages
		self.languages = languages

	def as_cvs_line(self):
		return ",".join([\
			self.extension_id,\
			self.title,\
			self.description,\
			str(self.no_of_users),\
			str(self.no_of_ratings),\
			str(self.avg_rating),\
			self.version_no,\
			self.size,\
			self.last_updated,\
			str(self.no_of_languages),\
			self.languages\
		])

	def from_csv_line(csv_line):
		vals = csv_line.split(",")
		return ChromeExtension(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6], vals[7], vals[8], vals[9], vals[10])

	def download_info_from_url(self, extension_url=None, user_agent=""):
		if extension_url is None:
			extension_url = "https://chrome.google.com/webstore/detail/" + self.extension_id
		print(f"Getting info about extension with ID {self.extension_id} from URL: {extension_url}")

		# (1.) Retrieve HTML source code of https://chrome.google.com/webstore/detail/xxx...xxx
		dest_file = "./." + self.extension_id + ".html" # e.g. "./.abcdefghijklmnopqrstuvwxyzabcdef.xml"
		download_file(file_url=extension_url, destination_file=dest_file, user_agent=user_agent)
		html = ""
		with open(dest_file, "r") as html_file:
			html = html_file.read()
		print(f"Downloaded '{extension_url}' to '{dest_file}': {html[:10]} ... {html[-10:]}")


		# (2.) Retrieve each relevant data point:
		# => cf. https://stackoverflow.com/questions/4666973/how-to-extract-the-substring-between-two-markers

		# (2a) Retrieve title:
		m = re.search('<h1 class="\\w+">(.+?)</h1>', html)
		if m:
			self.title = m.group(1).replace(",", "")
		else:
			print(f"Error: failed to extract title for extension with ID {self.extension_id}", file=sys.stderr)

		# (2b) Retrieve description (or rather the first paragraph of the description):
		# e.g.: <h2 class="wpJH0b"><div>Overview</div></h2></div><div class="RNnO5e" jscontroller="qv5bsb" jsaction="click:i7GaQb(rs1XOd);rcuQ6b:npT2md"><div jsname="ij8cu" class="JJ3H1e JpY6Fd"><p>Display equations in ChatGPT using Latex notation</p>
		m = re.search('<h2 class="\\w+"><div>Overview</div></h2></div><div class="\\w+" jscontroller="\\w+" jsaction=".+"><div jsname="\\w+" class=".+"><p>([\\s\\S]+?)</p>', html) # [\s\S] being a trick for saying "ALL characters, INCLUDING linebreaks"!
		if m:
			self.description = m.group(1).replace(",", "").replace("\n", "\\n")
		else:
			print(f"Error: failed to extract description for extension with ID {self.extension_id}", file=sys.stderr)

		# (2c) Retrieve no. of users:
		m = re.search('>([\\d,]+?) users?</div></div><div class="\\w+" jscontroller="\\w+" jsaction="', html)
		if m:
			self.no_of_users = int(m.group(1).replace(",", "")) # Removing commas is important here as int("10,000") throws a ValueError, for example!
		else:
			print(f"Error: failed to extract number of users for extension with ID {self.extension_id}", file=sys.stderr)

		# (2d) Retrieve no. of ratings:
		# e.g.: <span class="PmmSTd">24 ratings</span>
		#
		# => Are we not accidentally scraping the no. of ratings of another (recommended) extension?!
		#    => No, because they look like one of these:
		#       <span class="GvZmud" role="img" aria-label="Average rating 4.8 out of 5 stars. 16 ratings." id="i20">
		#       <div>Average rating 4.8 out of 5 stars. 16 ratings.</div>
		#
		m = re.search('<span class="\\w+">(([\\d,]+|No)?) ratings?</span>', html)
		if m:
			self.no_of_ratings = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
		else:
			print(f"Error: failed to extract number of ratings for extension with ID {self.extension_id}", file=sys.stderr)

		# (2e) Retrieve average rating:
		# e.g.: <div class="eTD1t"><h2 class="wpJH0b Yemige"><span class="GlMWqe">4.7 out of 5<div class=
		# e.g.: <div class="eTD1t"><h2 class="wpJH0b Yemige"><span class="GlMWqe">0 out of 5<div class=
		# e.g.: <div class="eTD1t"><h2 class="wpJH0b Yemige"><span class="GlMWqe">5 out of 5<div class=
		#
		# => Are we not accidentally scraping the average rating of another (recommended) extension?!
		#    => No, because they look like one of these:
		#       <span class="GvZmud" role="img" aria-label="Average rating 4.8 out of 5 stars. 16 ratings." id="i20">
		#       <div>Average rating 4.8 out of 5 stars. 16 ratings.</div>
		#
		m = re.search('<div class="\\w+"><h2 class=".+"><span class="\\w+">((\\d(\\.\\d)?)?) out of 5<div class=', html)
		if m:
			self.avg_rating = float(m.group(1))
		else:
			print(f"Error: failed to extract average rating for extension with ID {self.extension_id}", file=sys.stderr)

		# (2f) Retrieve version number:
		m = re.search('<div class="\\w+">Version</div><div class="\\w+">(.+?)</div>', html)
		if m:
			self.version_no = m.group(1).replace(",", "")
		else:
			print(f"Error: failed to extract version number for extension with ID {self.extension_id}", file=sys.stderr)

		# (2g) Retrieve size:
		m = re.search('<div class="\\w+">Size</div><div>(.+?)</div>', html)
		if m:
			self.size = m.group(1).replace(",", "")
		else:
			print(f"Error: failed to extract size for extension with ID {self.extension_id}", file=sys.stderr)

		# (2h) Retrieve last updated:
		m = re.search('<div class="\\w+">Updated</div><div>(.+?)</div>', html) # e.g.: <div class="nws2nb">Updated</div><div>May 14, 2024</div>
		if m:
			self.last_updated = m.group(1).replace(",", "")
		else:
			print(f"Error: failed to extract date of last update for extension with ID {self.extension_id}", file=sys.stderr)

	def download_crx_to(self, crx_dest_folder):
		print(f"Downloading .CRX of extension with ID {self.extension_id} into folder '{crx_dest_folder}' ...")
		pass # ToDo!

	def already_listed_in_extensions_csv(self, extensions_csv):
		ext_csv = extensions_csv if isinstance(extensions_csv, ExtensionsCSV) else ExtensionsCSV(extensions_csv)
		return ext_csv.contains(self)

	def add_to_extensions_csv(self, extensions_csv):
		ext_csv = extensions_csv if isinstance(extensions_csv, ExtensionsCSV) else ExtensionsCSV(extensions_csv)
		ext_csv.add(self)

	def from_extensions_csv(extensions_csv):
		ext_csv = extensions_csv if isinstance(extensions_csv, ExtensionsCSV) else ExtensionsCSV(extensions_csv)
		return ext_csv.read()



class ExtensionsCSV:
	def __init__(self, path):
		self.path = Path(path) # default: "./extensions.csv"
		if not self.path.is_file():
			# Create file:
			open(self.path, 'a').close() # https://stackoverflow.com/questions/12654772/create-empty-file-using-python

	def read(self) -> List[ChromeExtension]:
		return [ChromeExtension.from_csv_line(csv_line) for csv_line in open(self.path, "r")]

	def contains(self, extension: ChromeExtension):
		return any(extension.extension_id == ext.extension_id for ext in self.read())

	def add(self, extension: ChromeExtension):
		with open(self.path, "a") as csv_file:
			csv_file.write(extension.as_cvs_line() + "\n")

	# (1.) plot cumulative distribution function of extension size in KB => important as larger extensions are generally harder to analyze
	# (2.) plot cumulative distribution function of time since last update in months => might show that there are many abandoned extensions out there
	# (3.) plot cumulative distribution function of no. of users => might show that most extensions in the store are rarely downloaded
	# (4.) plot cumulative distribution function of no. of users as percentage of sum of *all* users => might show that there are many users of small extensions
	# (5.) plot correlation between no. of users and time since last update in months (scatter plot) => how frequently are abandoned extensions used by users?
	# (6.) plot correlation between no. of users and extension size => do users generally use more complex (and therefore harder to analyze) extensions?

	def plot_cum_distr_ext_size(self): # (1.)
		pass # ToDo!

	def plot_cum_distr_time_since_last_update(self): # (2.)
		pass # ToDo!

	def plot_cum_distr_no_of_users(self): # (3.)
		pass # ToDo!

	def plot_cum_distr_no_of_users_as_percentage_of_all_users(self): # (4.)
		pass # ToDo!

	def plot_corr_no_of_users_time_since_last_update(self): # (5.)
		pass # ToDo!

	def plot_corr_no_of_users_ext_size(self): # (6.)
		pass # ToDo!



def download_file(file_url, destination_file, user_agent=""):
	# cf. https://stackoverflow.com/questions/27928470/how-can-i-download-this-xml-file-from-given-url
	headers = {} if user_agent == "" else {'User-Agent': user_agent}
	
	request = urllib.request.Request(file_url, headers=headers)
	response = urllib.request.urlopen(request)
	with open(destination_file, 'wb') as outfile:
		shutil.copyfileobj(response, outfile)



def download_sitemap_xml_file(sitemap_xml_file, user_agent=""):
	print(f"No sitemap.xml found, downloading it from '{file_url}'...")

	url = "https://chrome.google.com/webstore/sitemap"
	download_file(url=url, destination_file=sitemap_xml_file, user_agent=user_agent)



def print_progress(done, total, of_what="", suffix="", width_in_chars=50, done_char='\u2588', undone_char='\u2591'):
	no_done_chars   = round((done/total) * width_in_chars)
	no_undone_chars = width_in_chars - no_done_chars
	print(f"[{done_char * no_done_chars}{undone_char * no_undone_chars}] {done} / {total} {of_what} {suffix}")


def format_seconds_to_printable_time(no_of_seconds):
	if no_of_seconds < 3600*24:
		# a trick to convert seconds into HH:MM:SS format, see: https://stackoverflow.com/questions/1384406/convert-seconds-to-hhmmss-in-python
		return time.strftime('%H:%M:%S', time.gmtime(no_of_seconds))
	else:
		return f"{no_of_seconds/(3600*24)} days"



def main():
	parser = argparse.ArgumentParser(
		description="""Chrome Webstore Crawler.
		When started with --crawl, starts crawling the Chrome extension webstore in a random order.
		Collects info about every extension in a .CSV file.
		This .CSV file can then be interpreted later to created some statistics (use --stats instead of --crawl for that).
		Saving each Chrome extension as a .CRX file is optional (to do so, specify --crx-download FOLDER_PATH).
		""")

	group1 = parser.add_mutually_exclusive_group(required=True)
	group1.add_argument('--crawl', action='store_true',
		help="""
		In this mode, the Chrome webstore will be crawled for extensions.
		Note that, when run in this mode, the program will only halt once the *entire* Chrome webstore has been crawled,
		so you might want to kill it earlier than that.
		To generate statistics on previously crawled extensions, use --stats instead.
		""")
	group1.add_argument('--stats', action='store_true',
		help="""
		In this mode, there won't be any crawling. Instead, the .CSV file will be read in and statistics will be generated.
		""")

	parser.add_argument('--csv-file',
		type=str,
		default='./extensions.csv',
		help="""
		The path to the .CSV file in which the crawled data shall be stored into (--crawl) / shall be retrieved from (--stats).
		Default: ./extensions.csv
		""",
		metavar='CSV_FILE')

	parser.add_argument('--sitemap-xml',
		type=str,
		default='./sitemap.xml',
		help="""
		The path to the "sitemap.xml" file.
		Will be downloaded to this path automatically if the file doesn't exist yet.
		Default: ./sitemap.xml
		""",
		metavar='SITEMAP_XML')

	parser.add_argument('--crx-download',
		type=str,
		default='',
		help="""
		The path to the folder into which every Chrome extension encountered shall be downloaded as a .CRX file.
		No .CRX files will be downloaded if this parameter isn't specified.
		""",
		metavar='FOLDER_PATH')

	parser.add_argument('--sleep',
		type=int,
		default=1000,
		help="""
		The sleep time in milliseconds between processing/downloading each extension.
		To avoid over-burdening the servers.
		Default: 1000
		""",
		metavar='SLEEP_IN_MILLIS')

	parser.add_argument('--user-agent',
		type=str,
		default='',
		help="""
		The custom user agent to use (when visiting chrome.google.com URLs).
		The default user agent will be used when this parameter isn't specified.
		""",
		metavar='USER_AGENT')

	args = parser.parse_args()

	if args.crawl:
		# ##### ##### ##### ##### Step 1: ##### ##### ##### ####
		# Download https://chrome.google.com/webstore/sitemap
		#   and save as './sitemap.xml' (or some other user-specified name, cf. --sitemap-xml argument) if that hasn't been done already.
		# Read in and parse './sitemap.xml'.
		# ##### ##### ##### #### ##### ##### ##### ##### ####
		sitemap_xml_file = Path(args.sitemap_xml) # default: "./sitemap.xml"
		if not sitemap_xml_file.is_file():
			download_sitemap_xml_file(sitemap_xml_file, user_agent=args.user_agent)
			print("sitemap.xml has been downloaded and saved.")
		else:
			print("sitemap.xml file found, reading it in...")
		# Read in './sitemap.xml':
		sitemap_xml_content = ""
		with open(sitemap_xml_file, 'r') as f:
			sitemap_xml_content = f.read()
		print("sitemap.xml has been read in.")
		print(f"Content of sitemap.xml reads: {sitemap_xml_content[:10]} ... {sitemap_xml_content[-10:]}")
		# Parse './sitemap.xml':
		xml_root = ET.parse(sitemap_xml_file).getroot() # https://stackoverflow.com/questions/1912434/how-to-parse-xml-and-get-instances-of-a-particular-node-attribute
		print(f"Parsed content of sitemap.xml: {xml_root}")
		print(f"Collecting URLs from sitemap.xml...")
		urls = []
		for xml_el in xml_root.iter(): # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.XML
			# print(xml_el) # print(xml_el.tag) # print(xml_el.text)
			if xml_el.tag.endswith("loc"):
				# print(xml_el.text)
				url = xml_el.text # e.g. "https://chrome.google.com/webstore/sitemap?shard=42"
				if "&hl=" not in url: # Ignore all URLs with a "&hl=..." language specifier!
					urls.append(url)
		print(f"Collected {len(urls)} URLs from sitemap.xml.")
		# Remove duplicates:
		urls = list(set(urls))
		print(f"  => {len(urls)} URLs left after removing duplicates.")
		# Shuffle URLs:
		random.shuffle(urls)
		print(f"Shuffled URLs, beginning with '{urls[0]}' ...")

		# ##### ##### ##### ##### Step 2: ##### ##### ##### ####
		# Visit each URL listed in './sitemap.xml'.
		#   => For each extension listed there:
		#      => Visit the extension's URL and parse title, description, no. of users, no. of ratings, average rating, version no., size, last updated and no. of languages.
		#      => Collect all of this information in the './extensions.csv' file, together with each extension's ID. Ensure (using the ID) that every extension is listed at most once!
		#      => If the --crx-download flag is set, try to download each extension as a .CRX file as well. Should this fail, don't abort but simply skip (and display an error message!).
		# (!!!) Note that each of the two "for each" above is done in random(!) order (!!!)
		# ##### ##### ##### #### ##### ##### ##### ##### ####	
		extensions_csv = ExtensionsCSV(args.csv_file) # default: "./extensions.csv"
		start_time = time.time()
		for i in range(len(urls)):
			# Print progress info:
			seconds_passed_so_far = int(time.time() - start_time)
			formatted_time_passed_so_far = format_seconds_to_printable_time(seconds_passed_so_far)
			formatted_estimated_time_remaining = ""
			if i > 0: # (to avoid division by zero)
				avg_no_of_seconds_spent_per_url = seconds_passed_so_far//i
				estimated_no_of_seconds_remaining = (len(urls)-i) * avg_no_of_seconds_spent_per_url # estimated time remaining = #URLs left * avg(time/URL)
				formatted_estimated_time_remaining = format_seconds_to_printable_time(estimated_no_of_seconds_remaining)
			else:
				formatted_estimated_time_remaining = "???"
			print_progress(i, len(urls), "URLs", f"({formatted_time_passed_so_far} passed so far; estimated time remaining: {formatted_estimated_time_remaining})")

			url = urls[i]
			print(f"(#{i+1}) Downloading '{url}' ...") # e.g. "https://chrome.google.com/webstore/sitemap?shard=573"
			dest_file = "./." + url.split("=")[-1] + ".xml" # e.g. "./.573.xml"
			download_file(file_url=url, destination_file=dest_file, user_agent=args.user_agent)
			print(f"Downloaded '{url}' to: {dest_file}")
			# Parse XML:
			xml_root = ET.parse(dest_file).getroot() # https://stackoverflow.com/questions/1912434/how-to-parse-xml-and-get-instances-of-a-particular-node-attribute
			print(f"Parsed content of .xml file: {xml_root}")
			print(f"Collecting extension URLs from .xml ...")
			extension_urls = []
			extension_languages = defaultdict(list) # maps each extension URL to the list of supported languages
			for xml_el in xml_root.iter(): # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.XML
				#print(xml_el.tag) # print(xml_el) # print(xml_el.tag) # print(xml_el.text)
				# e.g. <xhtml:link href="https://chrome.google.com/webstore/detail/extension-name-here/abcdefghijklmnopqrstuvwxyzabcdef" hreflang="en-US" rel="alternate"/>
				if xml_el.tag.endswith("link"):
					# print("href attribute = " + xml_el.attrib["href"])
					extension_url = xml_el.attrib["href"] # e.g. "https://chrome.google.com/webstore/detail/extension-name-here/abcdefghijklmnopqrstuvwxyzabcdef"
					extension_urls.append(extension_url)
					extension_languages[extension_url].append(xml_el.attrib["hreflang"]) # keeps track of all languages supported by each extension
			print(f"Collected {len(extension_urls)} extension URLs from '{url}'")
			# Remove duplicates:
			extension_urls = list(set(extension_urls))
			print(f"  => {len(extension_urls)} extension URLs left after removing duplicates.")
			# Shuffle extension URLs:
			random.shuffle(extension_urls)
			print(f"Shuffled extension URLs, beginning with '{extension_urls[0]}' ...")
			for extension_url in extension_urls: # e.g. "https://chrome.google.com/webstore/detail/extension-name-here/abcdefghijklmnopqrstuvwxyzabcdef"
				extension_id = [url_el for url_el in extension_url.split("/") if url_el != ""][-1] # list comprehension just in case there should ever be a trailing slash "/"
				chrome_extension = ChromeExtension(extension_id=extension_id, no_of_languages=len(extension_languages[extension_url]), languages="|".join(extension_languages[extension_url]))
				if chrome_extension.already_listed_in_extensions_csv(extensions_csv):
					print(f"Extension with ID {extension_id} is already in '{args.csv_file}', skipping it...")
				else:
					chrome_extension.download_info_from_url(extension_url=extension_url, user_agent=args.user_agent)
					if args.crx_download != "":
						chrome_extension.download_crx_to(crx_dest_folder=args.crx_download)
					chrome_extension.add_to_extensions_csv(extensions_csv=extensions_csv)
				# Sleep:
				time.sleep(args.sleep / 1000)

	elif args.stats:
		# ##### ##### ##### ##### Step 3: ##### ##### ##### ####
		# Compute some statistics based on './extensions.csv':
		# (1.) plot cumulative distribution function of extension size in KB => important as larger extensions are generally harder to analyze
		# (2.) plot cumulative distribution function of time since last update in months => might show that there are many abandoned extensions out there
		# (3.) plot cumulative distribution function of no. of users => might show that most extensions in the store are rarely downloaded
		# (4.) plot cumulative distribution function of no. of users as percentage of sum of *all* users => might show that there are many users of small extensions
		# (5.) plot correlation between no. of users and time since last update in months (scatter plot) => how frequently are abandoned extensions used by users?
		# (6.) plot correlation between no. of users and extension size => do users generally use more complex (and therefore harder to analyze) extensions?
		# ##### ##### ##### #### ##### ##### ##### ##### ####
		extensions_csv = ExtensionsCSV(args.csv_file) # default: "./extensions.csv"
		extensions_csv.plot_cum_distr_ext_size() # (1.)
		extensions_csv.plot_cum_distr_time_since_last_update() # (2.)
		extensions_csv.plot_cum_distr_no_of_users() # (3.)
		extensions_csv.plot_cum_distr_no_of_users_as_percentage_of_all_users() # (4.)
		extensions_csv.plot_corr_no_of_users_time_since_last_update() # (5.)
		extensions_csv.plot_corr_no_of_users_ext_size() # (6.)

	else:
		print(f"Argument Error: Neither --crawl nor --stats flag was specified!")



if __name__ == "__main__":
	main()


