# chrome_webstore_crawler
A Python script crawling all extensions from the Chrome Web Store: saving them and/or creating a CSV with statistics about them.

```
$ python3 chrome_webstore_crawler.py --help
usage: chrome_webstore_crawler.py [-h] (--crawl | --stats | --download-crxs | --random-subset | --user-base-representative-subset) [--csv-file CSV_FILE] [--sitemap-xml SITEMAP_XML] [--crx-download FOLDER_PATH]
                                  [--crx-download-user-threshold SLEEP_IN_MILLIS] [--sleep SLEEP_IN_MILLIS] [--user-agent USER_AGENT] [--subset-size SUBSET_SIZE]

Chrome Webstore Crawler. When started with --crawl, starts crawling the Chrome extension webstore in a random order. Collects info about every extension in a .CSV file. This .CSV file can then be interpreted later
to created some statistics (use --stats instead of --crawl for that). Saving each Chrome extension as a .CRX file is optional (to do so, specify --crx-download FOLDER_PATH).

options:
  -h, --help            show this help message and exit
  --crawl               In this mode, the Chrome webstore will be crawled for extensions. Note that, when run in this mode, the program will only halt once the *entire* Chrome webstore has been crawled, so you might
                        want to kill it earlier than that. To generate statistics on previously crawled extensions, use --stats instead.
  --stats               In this mode, there won't be any crawling. Instead, the .CSV file will be read in and statistics will be generated.
  --download-crxs       In this mode, there won't be any crawling of *new* extensions. Instead, the .CRX file will be downloaded for every extension listed in the .CSV file. Note that this requires also specifying
                        the destination folder for the .CRX files using the --crx-download parameter. If you only want to download the .CRX files of extensions with a certain number of users, use the --crx-download-
                        user-threshold argument for that.
  --random-subset       In this mode, there won't be any crawling. Instead, the .CRX file given will be used to create a new, smaller .CRX file from a *random* subset of extensions taken from the big, original .CSV
                        file. By default, the size of this random subset will be 100, use the --subset-size parameter to specify something else.
  --user-base-representative-subset
                        In this mode, there won't be any crawling. Instead, the .CRX file given will be used to create a new, smaller .CRX file from a *representative* subset of extensions taken from the big,
                        original .CSV file. "Representative" in this case means that the extensions won't be chosen randomly from the set of all extensions (each extension being equally likely), but instead that the
                        extensions will be chosen randomly from the *user base*, making more frequently used extensions much more likely to be chosen. By default, the size of this random subset will be 100, use the
                        --subset-size parameter to specify something else.
  --csv-file CSV_FILE   The path to the .CSV file in which the crawled data shall be stored into (--crawl) / shall be retrieved from (--stats). Default: ./extensions.csv
  --sitemap-xml SITEMAP_XML
                        The path to the "sitemap.xml" file. Will be downloaded to this path automatically if the file doesn't exist yet. Default: ./sitemap.xml
  --crx-download FOLDER_PATH
                        The path to the folder into which every Chrome extension encountered shall be downloaded as a .CRX file. No .CRX files will be downloaded if this parameter isn't specified.
  --crx-download-user-threshold SLEEP_IN_MILLIS
                        Only download extensions with more than X users. This parameter only has an effect if the --crx-download argument is supplied. By default this parameter is set to 0 and therefore has no
                        effect. Default: 0
  --sleep SLEEP_IN_MILLIS
                        The sleep time in milliseconds between processing/downloading each extension. To avoid over-burdening the servers. Default: 1000
  --user-agent USER_AGENT
                        The custom user agent to use (when visiting chrome.google.com URLs). The default user agent will be used when this parameter isn't specified.
  --subset-size SUBSET_SIZE
                        The size of the (random, or representative) subset to be selected. Only has an effect when used in the --random-subset mode or --user-base-representative-subset mode. Default: 100
```
