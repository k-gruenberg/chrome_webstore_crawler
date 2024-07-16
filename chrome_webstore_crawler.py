from pathlib import Path
import urllib.request
import shutil

# ##### ##### ##### ##### Step 1: ##### ##### ##### ####
# Download https://chrome.google.com/webstore/sitemap
#   and save as 'sitemap.xml' if that hasn't been done already.
# Read in 'sitemap.xml'.
# ##### ##### ##### #### ##### ##### ##### ##### ####

sitemap_xml_file = Path("sitemap.xml")
if not sitemap_xml_file.is_file():
	# cf. https://stackoverflow.com/questions/27928470/how-can-i-download-this-xml-file-from-given-url
	headers = {} #{'User-Agent': 'Mozilla'}
	urlfile = "https://chrome.google.com/webstore/sitemap"
	
	print(f"No sitemap.xml found, downloading it from '{urlfile}'...")

	request = urllib.request.Request(urlfile, headers=headers)
	response = urllib.request.urlopen(request)
	with open(sitemap_xml_file, 'wb') as outfile:
		shutil.copyfileobj(response, outfile)

	print("sitemap.xml has been downloaded and saved.")
else:
	print("sitemap.xml file found, reading it in...")

sitemap_xml_content = ""
with open(sitemap_xml_file, 'r') as f:
	sitemap_xml_content = f.read()
print("sitemap.xml has been read in.")

print(f"Content of sitemap.xml reads: {sitemap_xml_content[:10]} ... {sitemap_xml_content[-10:]}")



# ##### ##### ##### ##### Step 2: ##### ##### ##### ####
# Visit each URL listed in 'sitemap.xml'.
#   => For each extension listed there:
#      => Visit the extension's URL and parse title, description, no. of users, no. of ratings, average rating, version no., size, last updated and no. of languages.
#      => Collect all of this information in a single 'extensions.csv' file, together with each extension's ID. Ensure (using the ID) that every extension is listed at most once!
#      => If the --download flag is set, try to download each extension as a .crx file as well. Should this fail, don't abort but simply skip.
# Skip this step if a file named 'extensions.csv' already exists.
# ##### ##### ##### #### ##### ##### ##### ##### ####

extensions_csv_file = Path("extensions.csv")
if not extensions_csv_file.is_file():
	pass # ToDo...



# ##### ##### ##### ##### Step 3: ##### ##### ##### ####
# Compute some statistics based on 'extensions.csv':
# (1.) plot cumulative distribution function of extension size in KB => important as larger extensions are generally harder to analyze
# (2.) plot cumulative distribution function of time since last update in months => might show that there are many abandoned extensions out there
# (3.) plot cumulative distribution function of no. of users => might show that most extensions in the store are rarely downloaded
# (4.) plot cumulative distribution function of no. of users as percentage of sum of *all* users => might show that there are many users of small extensions
# (5.) plot correlation between no. of users and time since last update in months (scatter plot) => how frequently are abandoned extensions used by users?
# (6.) plot correlation between no. of users and extension size => do users generally use more complex (and therefore harder to analyze) extensions?
# ##### ##### ##### #### ##### ##### ##### ##### ####

# ToDo...


