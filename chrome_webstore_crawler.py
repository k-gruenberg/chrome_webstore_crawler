import argparse
from pathlib import Path
import urllib.request
import shutil



def download_sitemap_xml_file(sitemap_xml_file, user_agent=""):
	# cf. https://stackoverflow.com/questions/27928470/how-can-i-download-this-xml-file-from-given-url
	headers = {} if user_agent == "" else {'User-Agent': user_agent}
	urlfile = "https://chrome.google.com/webstore/sitemap"
	
	print(f"No sitemap.xml found, downloading it from '{urlfile}'...")

	request = urllib.request.Request(urlfile, headers=headers)
	response = urllib.request.urlopen(request)
	with open(sitemap_xml_file, 'wb') as outfile:
		shutil.copyfileobj(response, outfile)



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
		""",
		metavar='CSV_FILE')

	parser.add_argument('--sitemap-xml',
		type=str,
		default='./sitemap.xml',
		help="""
		The path to the "sitemap.xml" file.
		Will be downloaded to this path automatically if the file doesn't exist yet.
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

	parser.add_argument('--timeout',
		type=int,
		default=1000,
		help="""
		The timeout in milliseconds between processing/downloading each extension.
		""",
		metavar='TIMEOUT_IN_MILLIS')

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
		#   and save as 'sitemap.xml' (or some other user-specified name, cf. --sitemap-xml argument) if that hasn't been done already.
		# Read in 'sitemap.xml'.
		# ##### ##### ##### #### ##### ##### ##### ##### ####
		sitemap_xml_file = Path(args.sitemap_xml) # default: "./sitemap.xml"
		if not sitemap_xml_file.is_file():
			download_sitemap_xml_file(sitemap_xml_file, user_agent=args.user_agent)
			print("sitemap.xml has been downloaded and saved.")
		else:
			print("sitemap.xml file found, reading it in...")
		# Read in 'sitemap.xml':
		sitemap_xml_content = ""
		with open(sitemap_xml_file, 'r') as f:
			sitemap_xml_content = f.read()
		print("sitemap.xml has been read in.")
		print(f"Content of sitemap.xml reads: {sitemap_xml_content[:10]} ... {sitemap_xml_content[-10:]}")

		# ##### ##### ##### ##### Step 2: ##### ##### ##### ####
		# Visit each URL listed in './sitemap.xml'.
		#   => For each extension listed there:
		#      => Visit the extension's URL and parse title, description, no. of users, no. of ratings, average rating, version no., size, last updated and no. of languages.
		#      => Collect all of this information in the './extensions.csv' file, together with each extension's ID. Ensure (using the ID) that every extension is listed at most once!
		#      => If the --crx-download flag is set, try to download each extension as a .CRX file as well. Should this fail, don't abort but simply skip (and display an error message!).
		# ##### ##### ##### #### ##### ##### ##### ##### ####
		extensions_csv_file = Path(args.csv_file) # default: "./extensions.csv"
		if not extensions_csv_file.is_file():
			pass # ToDo...

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
		pass # ToDo...

	else:
		print(f"Argument Error: Neither --crawl nor --stats flag was specified!")



if __name__ == "__main__":
	main()


