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
