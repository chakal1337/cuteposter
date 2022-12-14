# Cuteposter

Cuteposter is a SEO tool, a fast poster that supports simple spintax, macros, automatic form recognition, crawling, randomization and more.
This tool can be used to create backlinks on many types of blogs and forums as long as they don't have a captcha.
I'm not responsible for how this tool is used, any violation of search engine terms of service is your own fault, don't blame me if your website gets blacklisted.

# usage examples

# post comments from comments.txt to targets.txt urls using rootkitz.top as the link, 3 crawl depth, custom usernames file and 50 threads

python3 cutepost.py targets.txt https://rootkitz.top/ -d 3 -c comments.txt -u usernames.txt -t 50

# post comments from comments.txt to targets.txt urls using rootkitz.top as the link, 2 crawl depth, random usernames and 25 threads

python3 cutepost.py targets.txt links.txt -d 2 -c comments.txt -t 25


for more advanced usage read the code
