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
import os

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import statistics
from math import log10, floor



KEEP_TEMP_XML_FILES = False
KEEP_TEMP_HTML_FILES = False



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

	def __str__(self):
		return self.as_cvs_line()

	def from_csv_line(csv_line):
		vals = csv_line.rstrip('\r\n').split(",")
		return ChromeExtension(vals[0], vals[1], vals[2], int(vals[3]), int(vals[4]), float(vals[5]), vals[6], vals[7], vals[8], int(vals[9]), vals[10])

	def download_info_from_url(self, extension_url=None, user_agent=""):
		if extension_url is None:
			extension_url = "https://chrome.google.com/webstore/detail/" + self.extension_id
		print(f"Getting info about extension with ID {self.extension_id} from URL: {extension_url}")

		# (1.) Retrieve HTML source code of https://chrome.google.com/webstore/detail/xxx...xxx
		temp_dest_file = "./." + self.extension_id + ".html" # e.g. "./.abcdefghijklmnopqrstuvwxyzabcdef.html"
		download_file(file_url=extension_url, destination_file=temp_dest_file, user_agent=user_agent)
		html = ""
		with open(temp_dest_file, "r") as html_file:
			html = html_file.read()
		print(f"Downloaded '{extension_url}' to '{temp_dest_file}': {html[:10]} ... {html[-10:]}")
		# Delete downloaded .HTML file again after it has been read in:
		if not KEEP_TEMP_HTML_FILES:
			os.remove(temp_dest_file)


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
		m = re.search('<span class="\\w+">([\\d,]+|No) ratings?</span>', html)
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
		m = re.search('<div class="\\w+"><h2 class=".+"><span class="\\w+">(\\d(\\.\\d)?) out of 5<div class=', html)
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

	def download_crx_to(self, crx_dest_folder, user_agent=""): # may throw urllib.error.HTTPError or AttributeError
		# (ToDo: be able to download .CRXs of lesser known extensions by not using www.crx4chrome.com but instead getting the .CRXs from the store directly somehow...)
		print(f"Downloading .CRX of extension with ID {self.extension_id} into folder '{crx_dest_folder}' ...")
		
		# (1.) Visit https://www.crx4chrome.com/extensions/abcdefghijklmnopqrstuvwxyzabcdef/ and download as HTML:
		url = "https://www.crx4chrome.com/extensions/" + self.extension_id
		temp_dest_file = "./.crx4chrome.extensions." + self.extension_id + ".html" # e.g. "./.crx4chrome.abcdefghijklmnopqrstuvwxyzabcdef.html"
		download_file(file_url=url, destination_file=temp_dest_file, user_agent=user_agent)
		html = ""
		with open(temp_dest_file, "r") as html_file:
			html = html_file.read()
		# Delete downloaded .HTML file again after it has been read in:
		if not KEEP_TEMP_HTML_FILES:
			os.remove(temp_dest_file)

		# (2.) Extract the the link to the download site (e.g. "https://www.crx4chrome.com/crx/584/") from this HTML:
		#      => example: <a href="/crx/584/" title="Download Now">Download Now &gt;</a>
		m = re.search('<a href="/crx/(\\d+?)/" title="Download Now">Download Now &gt;</a>', html)
		if m:
			url = "https://www.crx4chrome.com/crx/" + str(int(m.group(1))) # e.g. "https://www.crx4chrome.com/crx/584/" # note that the int(.) cast here solely acts as an assertion!
		else:
			raise AttributeError(f"Error: failed to download extension with ID {self.extension_id} (couldn't extract link to download site from '{url}')")

		# (3.) Visit https://www.crx4chrome.com/crx/0000/ and download as HTML:
		temp_dest_file = "./.crx4chrome.crx." + self.extension_id + ".html" # e.g. "./.crx4chrome.abcdefghijklmnopqrstuvwxyzabcdef.html"
		download_file(file_url=url, destination_file=temp_dest_file, user_agent=user_agent)
		html = ""
		with open(temp_dest_file, "r") as html_file:
			html = html_file.read()
		# Delete downloaded .HTML file again after it has been read in:
		if not KEEP_TEMP_HTML_FILES:
			os.remove(temp_dest_file)

		# (4.) Extract the the download link from this HTML (e.g. "https://www.crx4chrome.com/go.php?p=584&i=aapbdbdomjkkjkaonfhkkikfgjllcleb&s=O37YH28UQ4xbA&l=https%3A%2F%2Ff6.crx4chrome.com%2Fcrx.php%3Fi%3Daapbdbdomjkkjkaonfhkkikfgjllcleb%26v%3D2.0.15"):
		#      => example: <p class="app-desc">download crx from <a href="/go.php?p=584&i=aapbdbdomjkkjkaonfhkkikfgjllcleb&s=O37YH28UQ4xbA&l=https%3A%2F%2Ff6.crx4chrome.com%2Fcrx.php%3Fi%3Daapbdbdomjkkjkaonfhkkikfgjllcleb%26v%3D2.0.15" class="more" rel="nofollow" title="download crx from crx4chrome">crx4chrome</a></p>
		m = re.search('<p class="app-desc">download crx from <a href="/go.php\\?p=(.+?)" class="more" rel="nofollow" title="download crx from crx4chrome">crx4chrome</a></p>', html)
		if m:
			url = "https://www.crx4chrome.com/go.php?p=" + m.group(1) # e.g. "https://www.crx4chrome.com/go.php?p=584&i=aapbdbdomjkkjkaonfhkkikfgjllcleb&s=O37YH28UQ4xbA&l=https%3A%2F%2Ff6.crx4chrome.com%2Fcrx.php%3Fi%3Daapbdbdomjkkjkaonfhkkikfgjllcleb%26v%3D2.0.15"
		else:
			raise AttributeError(f"Error: failed to download extension with ID {self.extension_id} (couldn't extract download link from '{url}')")

		# (5.) Visit the download link and download the extension into the desired destination folder:
		crx_dest_file = os.path.join(crx_dest_folder, self.extension_id + ".crx")
		download_file(file_url=url, destination_file=crx_dest_file, user_agent=user_agent)
		#print(f"Successfully downloaded .CRX of extension with ID {self.extension_id} to: '{crx_dest_file}'") # sucess print shall be done by calling function
		return crx_dest_file

	def already_listed_in_extensions_csv(self, extensions_csv):
		ext_csv = extensions_csv if isinstance(extensions_csv, ExtensionsCSV) else ExtensionsCSV(extensions_csv)
		return ext_csv.contains(self)

	def add_to_extensions_csv(self, extensions_csv):
		ext_csv = extensions_csv if isinstance(extensions_csv, ExtensionsCSV) else ExtensionsCSV(extensions_csv)
		ext_csv.add(self)

	def from_extensions_csv(extensions_csv):
		ext_csv = extensions_csv if isinstance(extensions_csv, ExtensionsCSV) else ExtensionsCSV(extensions_csv)
		return ext_csv.read()

	def months_since_last_update(self):
		date_string = self.last_updated # e.g.: "August 9 2014"
		if date_string is None or date_string == "":
			return None
		last_updated_date = datetime.strptime(date_string, '%B %d %Y') # e.g.: datetime.datetime(2014, 8, 9, 0, 0) # cf. https://stackoverflow.com/questions/2265357/parse-date-string-and-change-format and https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
		time_delta = datetime.today() - last_updated_date # e.g.: datetime.timedelta(days=3636, seconds=78182, microseconds=601750)
		no_of_months = time_delta.days/30.437 # On average, there are 30.437 days in each month!
		return no_of_months



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

	# (0.) PDF/bar plot: frequency of each bin of no. of users (<10 users, <100 users, <1000 users, ...) => are most extensions rarely used?
	# (1.) plot cumulative distribution function of extension size in KB => important as larger extensions are generally harder to analyze
	# (2.) plot cumulative distribution function of time since last update in months => might show that there are many abandoned extensions out there
	# (3.) plot cumulative distribution function of no. of users => might show that most extensions in the store are rarely downloaded
	# (4.) plot cumulative distribution function of no. of users as percentage of sum of *all* users => might show that there are many users of small extensions
	# (5.) plot correlation between no. of users and time since last update in months (scatter plot) => how frequently are abandoned extensions used by users?
	# (6.) plot correlation between no. of users and extension size => do users generally use more complex (and therefore harder to analyze) extensions?
	# (7.) bar plot of the {median/average} user count for each of the {no_of_quantiles} quantiles of extensions, sorted *by* user count => are most extensions rarely used?
	# (8.) bar plot of the {median/average} extension size for each of the {no_of_quantiles} quantiles of extensions, sorted *by* user count => are more rarely used extensions more simple/smaller?

	"""
	A simple example illustrating how to plot a CDF with numpy and plotplot
	(taken from https://stackoverflow.com/questions/15408371/cumulative-distribution-plots-python):

	import numpy as np
	import matplotlib.pyplot as plt

	# some fake data
	data = np.random.randn(1000)
	# evaluate the histogram
	values, base = np.histogram(data, bins=40)
	#evaluate the cumulative
	cumulative = np.cumsum(values)
	# plot the cumulative function
	plt.plot(base[:-1], cumulative, c='blue')
	#plot the survival function
	plt.plot(base[:-1], len(data)-cumulative, c='green')

	plt.show()
	"""

	def plot_pdf_no_of_users(self): # (0.)
		print("(0.) Plotting PDF (Probability Density Function) of no of users (<10 users, <100 users, <1000 users, ...).")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extensions.sort(key=lambda ext: ext.no_of_users) # Sort extensions by no. of users, in ascending order.
		# Compute bins (<10 users, <100 users, <1000 users, ...):
		bins = {} # something like: {10: 12, 100: 1234, 1000: 123, 10000: ...}
		for ext in extensions:
			bin_ = 10 if ext.no_of_users < 10 else 10**(floor(log10(ext.no_of_users))+1) # e.g., turns 123 into 1000, i.e., the smallest power of 10 that's strictly(!) larger than ext.no_of_users
			if bin_ not in bins.keys():
				bins[bin_] = 0
			bins[bin_] += 1
		# Plot:
		xs = sorted(list(bins.keys()))
		ys = [bins[x] for x in xs]
		plt.bar(x=[f"<{x:,}" for x in xs], height=ys) # ":_" to format with thousands separator, see: https://stackoverflow.com/questions/1823058/how-to-print-a-number-using-commas-as-thousands-separators
		plt.xlabel("No. of users")
		plt.ylabel("No. of extensions")
		plt.show()

	def plot_cum_distr_ext_size(self): # (1.)
		print("(1.) Plotting cumulative distribution function of extension size in KB.")
		NO_OF_BINS = 40
		print(f"\t=> No. of bins: {NO_OF_BINS}")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extension_sizes = [parse_size(ext.size)/1000 for ext in extensions if ext.size not in [None, ""]] # = [parse_size("7.59MiB")/1000, parse_size("29.56KiB")/1000, ...] = [7958.692, ...] # dividing by 1000 to turn into kilo-bytes
		values, base = np.histogram(extension_sizes, bins=NO_OF_BINS) # values = [1,2,3,2,1] = how many extensions fall into each bin (unit = count) # base = [10, 20, 30, 40, 50] = the bins (unit = kilo-bytes)
		print(f"\t=> Bins (unit=KB): {base[:5]} ... {base[-5:]}")
		print(f"\t=> Bin assignments: {values[:5]} ... {values[-5:]}")
		cumulative = np.cumsum(values) # = [1, 3, 6, 8, 9]
		cumulative_as_percentage = [100.0*(x/cumulative[-1]) for x in cumulative] # = [11.11, 33.33, 66.66, 88.88, 100.0]
		plt.plot(base[:-1], cumulative_as_percentage, c='blue')
		plt.xlabel("KB")
		plt.ylabel("%")
		plt.show()

	def plot_cum_distr_time_since_last_update(self): # (2.)
		print("(2.) Plotting cumulative distribution function of time since last update in months.")
		NO_OF_BINS = 40
		print(f"\t=> No. of bins: {NO_OF_BINS}")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		last_updates = [ext.months_since_last_update() for ext in extensions if ext.months_since_last_update() is not None]
		values, base = np.histogram(last_updates, bins=NO_OF_BINS) # values = [1,2,3,2,1] = how many extensions fall into each bin (unit = count) # base = [1, 2, 3, 4, 5] = the bins (unit = months)
		print(f"\t=> Bins (values=no. of months): {base[:5]} ... {base[-5:]}")
		print(f"\t=> Bin assignments: {values[:5]} ... {values[-5:]}")
		cumulative = np.cumsum(values) # = [1, 3, 6, 8, 9]
		cumulative_as_percentage = [100.0*(x/cumulative[-1]) for x in cumulative] # = [11.11, 33.33, 66.66, 88.88, 100.0]
		plt.plot(base[:-1], cumulative_as_percentage, c='blue')
		plt.xlabel("No. of months since last update")
		plt.ylabel("%")
		plt.show()

	def plot_cum_distr_no_of_users(self): # (3.)
		print("(3.) Plotting cumulative distribution function of number of users.")
		NO_OF_BINS = 40
		print(f"\t=> No. of bins: {NO_OF_BINS}")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		no_of_users = [ext.no_of_users for ext in extensions] # = [1, 270, 308, 8, 0, ...] = the no. of users for each extension
		values, base = np.histogram(no_of_users, bins=NO_OF_BINS) # values = [1,2,3,2,1] = how many extensions fall into each bin (unit = count) # base = [10, 20, 30, 40, 50] = the bins (no. of users)
		print(f"\t=> Bins (values=no. of users): {base[:5]} ... {base[-5:]}")
		print(f"\t=> Bin assignments: {values[:5]} ... {values[-5:]}")
		cumulative = np.cumsum(values) # = [1, 3, 6, 8, 9]
		cumulative_as_percentage = [100.0*(x/cumulative[-1]) for x in cumulative] # = [11.11, 33.33, 66.66, 88.88, 100.0]
		plt.plot(base[:-1], cumulative_as_percentage, c='blue')
		plt.xlabel("No. of users")
		plt.ylabel("%")
		plt.show()

	def plot_cum_distr_no_of_users_as_percentage_of_all_users(self): # (4.)
		print("(4.) Plotting cumulative distribution function of number of users as percentage of sum of *all* users.")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extensions.sort(key=lambda ext: ext.no_of_users) # Sort extensions by no. of users, in ascending order.
		no_of_users = [ext.no_of_users for ext in extensions] # = [0, 1, 8, 270, 308, ...] = the no. of users for each extension
		sum_of_all_user_counts = sum(no_of_users) # Note that this number might be rather large as some users might have *multiple* extensions installed!
		xs = [ x for x in range(101) ] # = % of extensions
		ys = [ 100 * sum(ext.no_of_users for ext in extensions[:int(len(extensions)*(x/100))]) / sum_of_all_user_counts for x in xs ] # = % of cumulative user count
		plt.plot(xs, ys, c='blue')
		plt.xlabel("% of extensions")
		plt.ylabel("% of cumulative user count")
		plt.show()

	# (ToDo: color scatter plot points according to the average user rating, e.g., green = 5.0 star rating, etc.)

	def plot_corr_no_of_users_time_since_last_update(self, log_scale=False): # (5.)
		print("(5.) Correlation between no. of users and time since last update in months (scatter plot).")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extensions = [ext for ext in extensions if ext.no_of_users is not None and ext.months_since_last_update() is not None]
		no_of_users = [ext.no_of_users for ext in extensions]
		months_since_last_update = [ext.months_since_last_update() for ext in extensions]
		plt.scatter(no_of_users, months_since_last_update, c='blue')
		plt.xlabel("No. of users")
		plt.ylabel("Months since last update")
		if log_scale:
			plt.xscale('log') # https://stackoverflow.com/questions/773814/plot-logarithmic-axes
		plt.show()

	def plot_corr_no_of_users_ext_size(self, log_scale=False): # (6.)
		print("(6.) Correlation between no. of users and extension size.")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extensions = [ext for ext in extensions if ext.no_of_users is not None and ext.size not in [None, ""]]
		no_of_users = [ext.no_of_users for ext in extensions]
		extension_size = [parse_size(ext.size)/1000 for ext in extensions] # divide by 1000 to turn bytes into KB
		plt.scatter(no_of_users, extension_size, c='blue')
		plt.xlabel("No. of users")
		plt.ylabel("Extension size (KB)")
		if log_scale:
			plt.xscale('log') # https://stackoverflow.com/questions/773814/plot-logarithmic-axes
		plt.show()

	def plot_bars_quantiles_user_count(self, no_of_quantiles=4, compute_median=False): # (7.)
		print(f"(7.) Bar plot of the {'median' if compute_median else 'average'} user count for each of the {no_of_quantiles} quantiles of extensions, sorted *by* user count.")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extensions.sort(key=lambda ext: ext.no_of_users) # Sort extensions by no. of users, in ascending order.
		size_per_quantile = len(extensions) // no_of_quantiles # = how many extensions will be in each quantile
		quantiles = [extensions[i*size_per_quantile:(i+1)*size_per_quantile] for i in range(no_of_quantiles-1)] + [extensions[(no_of_quantiles-1)*size_per_quantile:]]
		xs = [i+1 for i in range(no_of_quantiles)] # e.g.: [1,2,3,4]
		ys = []
		if compute_median:
			ys = [statistics.median(ext.no_of_users for ext in quantile) for quantile in quantiles]
		else:
			ys = [statistics.mean(ext.no_of_users for ext in quantile) for quantile in quantiles]
		plt.bar(x=xs, height=ys)
		plt.xlabel("Quantiles of extensions, sorted by user count")
		plt.ylabel(f"{'Median' if compute_median else 'Average'} user count in each quantile")
		plt.show()

	def plot_bars_quantiles_extension_size(self, no_of_quantiles=4, compute_median=False): # (8.)
		print(f"(8.) Bar plot of the {'median' if compute_median else 'average'} extension size for each of the {no_of_quantiles} quantiles of extensions, sorted *by* user count.")
		extensions = self.read() # = [ChromeExtension, ChromeExtension, ChromeExtension, ...]
		extensions = [ext for ext in extensions if ext.size not in [None, ""]] # Remove all extensions where we have no value for the size!
		extensions.sort(key=lambda ext: ext.no_of_users) # Sort extensions by no. of users, in ascending order.
		size_per_quantile = len(extensions) // no_of_quantiles # = how many extensions will be in each quantile
		quantiles = [extensions[i*size_per_quantile:(i+1)*size_per_quantile] for i in range(no_of_quantiles-1)] + [extensions[(no_of_quantiles-1)*size_per_quantile:]]
		xs = [i+1 for i in range(no_of_quantiles)] # e.g.: [1,2,3,4]
		ys = []
		if compute_median:
			ys = [statistics.median(parse_size(ext.size)/1000.0 for ext in quantile) for quantile in quantiles] # divide by 1000.0 to turn bytes into KB
		else:
			ys = [statistics.mean(parse_size(ext.size)/1000.0 for ext in quantile) for quantile in quantiles]
		plt.bar(x=xs, height=ys)
		plt.xlabel("Quantiles of extensions, sorted by user count")
		plt.ylabel(f"{'Median' if compute_median else 'Average'} extension size in each quantile (KB)")
		plt.show()



def download_file(file_url, destination_file, user_agent=""):
	# cf. https://stackoverflow.com/questions/27928470/how-can-i-download-this-xml-file-from-given-url
	headers = {} if user_agent == "" else {'User-Agent': user_agent}
	
	request = urllib.request.Request(file_url, headers=headers)
	response = urllib.request.urlopen(request)
	with open(destination_file, 'wb') as outfile:
		shutil.copyfileobj(response, outfile)



def download_sitemap_xml_file(sitemap_xml_file, user_agent=""):
	url = "https://chrome.google.com/webstore/sitemap"
	print(f"Downloading sitemap.xml from '{url}' to '{sitemap_xml_file}' ...")
	download_file(file_url=url, destination_file=sitemap_xml_file, user_agent=user_agent)



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



def parse_size(size_string): # turns strings like "7.59MiB", or "29.56KiB", or "149KiB" into the number of bytes that they represent/encode
	m = re.search('([\\d\\.]+)([a-zA-Z]+)', size_string)
	prefix, suffix = float(m.group(1)), m.group(2)
	match suffix:
		case "KiB":
			return round(1024 * prefix)
		case "MiB":
			return round(1024 * 1024 * prefix)
		case "GiB":
			return round(1024 * 1024 * 1024 * prefix)
		case _:
			raise ValueError(f"'{suffix}' in '{size_string}' is not a valid unit.")



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
	group1.add_argument('--download-crxs', action='store_true',
		help="""
		In this mode, there won't be any crawling of *new* extensions.
		Instead, the .CRX file will be downloaded for every extension listed in the .CSV file.
		Note that this requires also specifying the destination folder for the .CRX files using the --crx-download parameter.
		If you only want to download the .CRX files of extensions with a certain number of users, use the --crx-download-user-threshold argument for that.
		""")
	group1.add_argument('--random-subset', action='store_true',
		help="""
		In this mode, there won't be any crawling.
		Instead, the .CRX file given will be used to create a new, smaller .CRX file from a *random* subset of extensions taken from the big, original .CSV file.
		By default, the size of this random subset will be 100, use the --subset-size parameter to specify something else.
		""")
	group1.add_argument('--user-base-representative-subset', action='store_true',
		help="""
		In this mode, there won't be any crawling.
		Instead, the .CRX file given will be used to create a new, smaller .CRX file from a *representative* subset of extensions taken from the big, original .CSV file.
		"Representative" in this case means that the extensions won't be chosen randomly from the set of all extensions (each extension being equally likely),
		but instead that the extensions will be chosen randomly from the *user base*, making more frequently used extensions much more likely to be chosen.
		By default, the size of this random subset will be 100, use the --subset-size parameter to specify something else.
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

	parser.add_argument('--crx-download-user-threshold',
		type=int,
		default=0,
		help="""
		Only download extensions with more than X users.
		This parameter only has an effect if the --crx-download argument is supplied.
		By default this parameter is set to 0 and therefore has no effect.
		Default: 0
		""",
		metavar='SLEEP_IN_MILLIS')

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

	parser.add_argument('--subset-size',
		type=int,
		default=100,
		help="""
		The size of the (random, or representative) subset to be selected.
		Only has an effect when used in the --random-subset mode or --user-base-representative-subset mode.
		Default: 100
		""",
		metavar='SUBSET_SIZE')

	args = parser.parse_args()

	if args.crawl:
		# ##### ##### ##### ##### Step 1: ##### ##### ##### ####
		# Download https://chrome.google.com/webstore/sitemap
		#   and save as './sitemap.xml' (or some other user-specified name, cf. --sitemap-xml argument) if that hasn't been done already.
		# Read in and parse './sitemap.xml'.
		# ##### ##### ##### #### ##### ##### ##### ##### ####
		sitemap_xml_file = Path(args.sitemap_xml) # default: "./sitemap.xml"
		if not sitemap_xml_file.is_file():
			print(f"No sitemap.xml found under '{args.sitemap_xml}', downloading it...")
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
			temp_dest_file = "./." + url.split("=")[-1] + ".xml" # e.g. "./.573.xml"
			download_file(file_url=url, destination_file=temp_dest_file, user_agent=args.user_agent)
			print(f"Downloaded '{url}' to: {temp_dest_file}")
			# Parse XML:
			xml_root = ET.parse(temp_dest_file).getroot() # https://stackoverflow.com/questions/1912434/how-to-parse-xml-and-get-instances-of-a-particular-node-attribute
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
			# Delete temporary .XML file again:
			if not KEEP_TEMP_XML_FILES:
				os.remove(temp_dest_file)
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
					try:
						chrome_extension.download_info_from_url(extension_url=extension_url, user_agent=args.user_agent)
						if args.crx_download != "":
							if chrome_extension.no_of_users >= args.crx_download_user_threshold:
								try: # Graceful failure if .CRX download fails:
									crx_file = chrome_extension.download_crx_to(crx_dest_folder=args.crx_download, user_agent=args.user_agent)
									print(f"Download Success: Downloaded extension with ID {chrome_extension.extension_id} to: {crx_file}")
								except urllib.error.HTTPError as http_err:
									print(f"Error: failed to download extension with ID {chrome_extension.extension_id} (HTTP error when visiting '{http_err.url}'): {http_err}", file=sys.stderr)
								except AttributeError as attr_err:
									print(f"Error: failed to download extension with ID {chrome_extension.extension_id} (parse error): {attr_err}", file=sys.stderr)
							else:
								print(f"Not downloading .CRX of extension with ID {extension_id} as it has too few users ({chrome_extension.no_of_users} < {args.crx_download_user_threshold}).")
						chrome_extension.add_to_extensions_csv(extensions_csv=extensions_csv)
					except urllib.error.HTTPError as http_err:
						if http_err.code in [404, 301]:
							# urllib.error.HTTPError: HTTP Error 404: Not Found
							#   => e.g.: https://chrome.google.com/webstore/detail/shopping-saviour/jagmhbnfefommcdbkodbdbmklbagodcl
							# urllib.error.HTTPError: HTTP Error 301: The HTTP server returned a redirect error that would lead to an infinite loop.
							#   => e.g.: https://chrome.google.com/webstore/detail/%D9%83%D9%88%D8%AF-%D8%AE%D8%B5%D9%85-%D9%86%D8%B3%D9%8A%D9%85-%D9%84%D9%84%D9%88%D8%B1%D8%AF-%2510-%D9%84%D9%83/ngbejcbghammjgkmheipacdnkelaocco
							print(f"Error: Visiting extension URL '{extension_url}' resulted in a {http_err.code} HTTP error ({http_err}), skipping this extension (it will not be added to the .CSV file).", file=sys.stderr)
						else:
							raise # re-throw any other HTTPError, e.g., a "urllib.error.HTTPError: HTTP Error 503: Service Unavailable"
					# Sleep:
					time.sleep(args.sleep / 1000)

	elif args.stats:
		# ##### ##### ##### ##### Step 3: ##### ##### ##### #####
		# Compute some statistics based on './extensions.csv':
		# (0.) PDF/bar plot: frequency of each bin of no. of users (<10 users, <100 users, <1000 users, ...) => are most extensions rarely used?
		# (1.) plot cumulative distribution function of extension size in KB => important as larger extensions are generally harder to analyze
		# (2.) plot cumulative distribution function of time since last update in months => might show that there are many abandoned extensions out there
		# (3.) plot cumulative distribution function of no. of users => might show that most extensions in the store are rarely downloaded
		# (4.) plot cumulative distribution function of no. of users as percentage of sum of *all* users => might show that there are many users of small extensions
		# (5.) plot correlation between no. of users and time since last update in months (scatter plot) => how frequently are abandoned extensions used by users?
		# (6.) plot correlation between no. of users and extension size => do users generally use more complex (and therefore harder to analyze) extensions?
		# (7.) bar plot of the {median/average} user count for each of the {no_of_quantiles} quantiles of extensions, sorted *by* user count => are most extensions rarely used?
		# (8.) bar plot of the {median/average} extension size for each of the {no_of_quantiles} quantiles of extensions, sorted *by* user count => are more rarely used extensions more simple/smaller?
		# ##### ##### ##### ##### ##### ##### ##### ##### #####
		extensions_csv = ExtensionsCSV(args.csv_file) # default: "./extensions.csv"
		print(f"Generating statistics based on {len(extensions_csv.read())} crawled extensions...")
		extensions_csv.plot_pdf_no_of_users() # (0.)
		extensions_csv.plot_cum_distr_ext_size() # (1.)
		extensions_csv.plot_cum_distr_time_since_last_update() # (2.)
		extensions_csv.plot_cum_distr_no_of_users() # (3.)
		extensions_csv.plot_cum_distr_no_of_users_as_percentage_of_all_users() # (4.)
		extensions_csv.plot_corr_no_of_users_time_since_last_update(log_scale=False) # (5.)
		extensions_csv.plot_corr_no_of_users_time_since_last_update(log_scale=True) # (5.)
		extensions_csv.plot_corr_no_of_users_ext_size(log_scale=False) # (6.)
		extensions_csv.plot_corr_no_of_users_ext_size(log_scale=True) # (6.)
		for compute_median in [False, True]:
			for no_of_quantiles in [4, 10, 20]:
				extensions_csv.plot_bars_quantiles_user_count(no_of_quantiles=no_of_quantiles, compute_median=compute_median) # (7.)
				extensions_csv.plot_bars_quantiles_extension_size(no_of_quantiles=no_of_quantiles, compute_median=compute_median) # (8.)

	elif args.download_crxs:
		# Download the .CRX file for all extensions *ALREADY* listed in the (extensions).csv file:
		if args.crx_download == "":
			print(f"Argument Error: --download-crxs flag was specified but no destination folder with --crx-download!", file=sys.stderr)
		else:
			extensions_csv = ExtensionsCSV(args.csv_file) # default: "./extensions.csv"
			extensions = extensions_csv.read()
			count_download_successful = 0
			count_download_failed = 0
			count_download_skipped = 0
			for chrome_extension in extensions:
				#print(f"{chrome_extension.no_of_users} ({type(chrome_extension.no_of_users)}) >= {args.crx_download_user_threshold} ({type(args.crx_download_user_threshold)}) ?")
				if chrome_extension.no_of_users >= args.crx_download_user_threshold:
					# Try download (graceful failure):
					try:
						crx_file = chrome_extension.download_crx_to(crx_dest_folder=args.crx_download, user_agent=args.user_agent)
						print(f"Success: Downloaded extension with ID {chrome_extension.extension_id} to: {crx_file}")
						count_download_successful += 1
					except urllib.error.HTTPError as http_err:
						print(f"Error: failed to download extension with ID {chrome_extension.extension_id} (HTTP error when visiting '{http_err.url}'): {http_err}", file=sys.stderr)
						count_download_failed += 1
					except AttributeError as attr_err:
						print(f"Error: failed to download extension with ID {chrome_extension.extension_id} (parse error): {attr_err}", file=sys.stderr)
						count_download_failed += 1
					
					# Sleep:
					time.sleep(args.sleep / 1000)
				else:
					print(f"Not downloading .CRX of extension with ID {chrome_extension.extension_id} as it has too few users ({chrome_extension.no_of_users} < {args.crx_download_user_threshold}).")
					count_download_skipped += 1
					# DO NOT SLEEP WHEN NOT HAVING DOWNLOADED ANYTHING(!!!)
			print(f"Finished. Total no. of extensions: {len(extensions)} | Downloaded successfully: {count_download_successful} | Download failed: {count_download_failed} | Ignored (due to low user count): {count_download_skipped}")

	elif args.random_subset:
		# Take the .CSV file, take a *random* subset of size --subset-size and put that into a *new* .CSV file:
		
		# Take a *random* subset of size --subset-size of the existing .CSV file:
		extensions_csv = ExtensionsCSV(args.csv_file) # default: "./extensions.csv"
		extensions = extensions_csv.read() # If this were [i+1 for i in range(100)] ...
		extensions_sample = np.random.choice(extensions, size=args.subset_size) # ...then this would be: [67,  3, 47, 94, 30, 42, 23, 13, 72, 88] for args.subset_size=10 for example.
		
		# Choose a file name that does not exist yet: (otherwise, ExtensionsCSV(outfile) would be *appending* to an existing file! (as it's supposed to!))
		outfile = args.csv_file.removesuffix(".csv") + f"_random_sample_{args.subset_size}.csv"
		i = 2
		while Path(outfile).is_file():
			outfile = args.csv_file.removesuffix(".csv") + f"_random_sample_{args.subset_size}_no{i}.csv"
			i += 1

		# Create the *new* .CSV file:
		out_extensions_csv = ExtensionsCSV(outfile)
		for ext in extensions_sample:
			out_extensions_csv.add(ext)
		print(f"{outfile} now contains a random subset of {args.subset_size} extensions from {args.csv_file}")

	elif args.user_base_representative_subset:
		# Take the .CSV file, take a *representative* subset of size --subset-size and put that into a *new* .CSV file:

		# Take a *representative* subset of size --subset-size of the existing .CSV file:
		extensions_csv = ExtensionsCSV(args.csv_file) # default: "./extensions.csv"
		extensions = extensions_csv.read()
		# ...now make this set representative by repeating each extension N times where N is the no. of users of that extension:
		extensions = [[ext] * ext.no_of_users for ext in extensions]
		extensions = [x for xs in extensions for x in xs] # flattens the above list of lists, cf. https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
		# ...now sample --subset-size extensions from this enlarged set of extensions; making sure no extension is selected twice:
		extensions_sample = []
		while len(extensions_sample) < args.subset_size:
			ext = random.choice(extensions)
			if ext.extension_id not in [e.extension_id for e in extensions_sample]:
				extensions_sample.append(ext)

		# Choose a file name that does not exist yet: (otherwise, ExtensionsCSV(outfile) would be *appending* to an existing file! (as it's supposed to!))
		outfile = args.csv_file.removesuffix(".csv") + f"_representative_sample_{args.subset_size}.csv"
		i = 2
		while Path(outfile).is_file():
			outfile = args.csv_file.removesuffix(".csv") + f"_representative_sample_{args.subset_size}_no{i}.csv"
			i += 1

		# Create the *new* .CSV file:
		out_extensions_csv = ExtensionsCSV(outfile)
		for ext in extensions_sample:
			out_extensions_csv.add(ext)
		print(f"{outfile} now contains a user-base-representative subset of {args.subset_size} extensions from {args.csv_file}")


	else:
		print(f"Argument Error: Neither --crawl nor --stats nor --download-crxs nor --random-subset nor --user-base-representative-subset flag was specified!", file=sys.stderr)



if __name__ == "__main__":
	main()


