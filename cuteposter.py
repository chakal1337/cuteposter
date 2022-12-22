#!/usr/bin/python3
import sys
import requests
import argparse
import random
import string
import threading
import time
import urllib.parse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json

tlock = threading.Lock()

actions_posted = {}
urls_crawled = {}
threads = 25
tor = 0
max_depth = 1
max_url = 30
max_resp_sz = 1000000
max_forms = 10
comments = ["%%LINK%%"]
random_dict = []
usernames = []
debug = 0

parser = argparse.ArgumentParser(
 prog = "CutePoster",
 description = "posting tool"
)

parser.add_argument('targets')
parser.add_argument('links')
parser.add_argument('-c', '--comments-file')
parser.add_argument('-u', '--username-file')
parser.add_argument('-t', '--threads')
parser.add_argument('-m', '--max-url-crawl')
parser.add_argument('-s', '--max-resp-sz')
parser.add_argument('-f', '--max-forms')
parser.add_argument('-z', '--tor', action="store_true")
parser.add_argument('-d', '--depth')
parser.add_argument('-v', '--verbose', action="store_true")

args = parser.parse_args()

if args.tor:
 tor = 1

if args.threads:
 threads = int(args.threads)

if args.max_resp_sz:
 max_resp_sz = int(args.max_resp_sz)

if args.verbose:
 debug = 1

if args.max_forms:
 max_forms = int(args.max_forms)

if args.max_url_crawl:
 max_url = int(args.max_url_crawl)

if args.depth:
 max_depth = int(args.depth)

if args.comments_file:
 with open(args.comments_file, "rb") as file:
  comments = file.read().decode().splitlines()

if args.username_file:
 with open(args.username_file, "rb") as file:
  usernames = file.read().decode().splitlines()

targets = []
try:
 with open(args.targets, "rb") as file:
  targets = file.read().decode().splitlines()
except:
 targets = [args.targets]

links = []
try:
 with open(args.links, "rb") as file:
  links = file.read().decode().splitlines()
except:
 links = [args.links]

def get_url_root(url):
 if "://" in url: 
  schema = url.split("://")[0]
  domain = url.split("://")[1]
  if ":" in domain: domain = domain.split(":")[0]
  if "/" in domain: domain = domain.split("/")[0]
  root_url = f"{schema}://{domain}"
  return root_url
 return "unrecognized"

def get_random_string():
 if len(random_dict):
  return random_choice(random_dict)
 else:
  rstr = "".join(random.choice(string.ascii_lowercase) for _ in range(random.randint(6, 8)))
  return rstr

def get_uname():
 if len(usernames):
  return random.choice(usernames)
 else:
  return get_random_string()

def spin_bot(stc):
 finalstc = ""
 i = 0
 phrase = stc
 while i < len(phrase):
  if phrase[i] == "[" and phrase[i+1] == "[":
   i+=2
   dzsz = ""
   while i < len(phrase):
    dzsz += phrase[i]
    i+=1
    if phrase[i] == "]" and phrase[i+1] == "]":
     break
   i+=2
   finalstc += random.choice(dzsz.split("|"))
  else: 
   finalstc += phrase[i]
   i+=1
 return finalstc

def parse_def(str):
 str = str.split(" ")
 for i in range(len(str)):
  if "%%LINK%" in str[i]: str[i] = str[i].replace("%%LINK%%", random.choice(links))
  if "%%RAND%%" in str[i]: str[i] = str[i].replace("%%RAND%%", get_random_string())
  if "%%NAME%%" in str[i]: str[i] = str[i].replace("%%NAME%%", get_uname())
 return spin_bot(" ".join(str))

def get_payload(inp_name):
 inp_name = inp_name.lower()
 username_defs = ["user","name","nick"]
 url_defs = ["url","link","web"]
 email_defs = ["mail","addr"]
 full_defs = ["comment","text","content"]
 phone_defs = ["phone","mobile","tel"]
 for unm in username_defs:
  if unm in inp_name:
   return parse_def(get_uname())
 for urm in url_defs:
  if urm in inp_name:
   return parse_def(random.choice(links)) 
 for emm in email_defs:
  if emm in inp_name:
   return parse_def(get_uname()+"@gmail.com")
 for ffm in full_defs:
  if ffm in inp_name:
   return parse_def(random.choice(comments))
 for phm in phone_defs:
  if phm in inp_name:
   return "".join(random.choice("0123456789") for _ in range(9))
 return parse_def(random.choice(comments))

def send_form_payload(form_action, form, s, headers, proxies):
 input_names = ["input","textarea","checkbox","select"]
 data = {}
 for input_name in input_names:
  for input in form.find_all(input_name):
   inp_name = input.get("name")
   if not inp_name: continue
   inp_value = input.get("value")
   if inp_value:
    data[inp_name] = inp_value
   else:
    payload = get_payload(inp_name)
    data[inp_name] = payload
 with s.post(url=form_action, data=data, headers=headers, proxies=proxies, timeout=5, stream=True) as r:
  print("Posted to: {}".format(form_action))
  if debug == 1: print(json.dumps(data))

def post(url, url_original, s, soup, headers, proxies):
 global actions_posted
 forms = soup.find_all("form")
 random.shuffle(forms)
 formcount = 0
 for form in forms:
  if formcount >= max_forms: break
  formcount += 1
  form_action = form.get("action")
  if not form_action: continue
  if form_action.startswith("http"):
   if not form_action.startswith(url_original): continue
  else:
   form_action = urljoin(url, form_action)
  with tlock:
   if form_action in actions_posted.keys(): continue
   else: actions_posted[form_action] = True
  send_form_payload(form_action, form, s, headers, proxies)

def getreqsafe(s, url, proxies, headers):
 rchnksz = 0
 data = ""
 with s.get(url=url, headers=headers, timeout=5, proxies=proxies, stream=True) as r:
  for chunk in r.iter_content(chunk_size=1024):
   data += chunk.decode()
   rchnksz += 1024
   if rchnksz >= max_resp_sz:
    break
  r.close()
  return data

def scrape(url, url_original, depth=1):
 global urls_crawled
 try:
  proxies = {}
  if tor == 1:
   proxies["http"] = "socks5h://127.0.0.1:9050"
   proxies["https"] = "socks5h://127.0.0.1:9050"
  headers = {
   "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
  }
  s = requests.Session()
  r = getreqsafe(s, url, proxies, headers)
  if r == "": return
  soup = BeautifulSoup(r, "html.parser")
  if "<form" in r: post(url, url_original, s, soup, headers, proxies) 
  lnkpool = soup.find_all("a")
  random.shuffle(lnkpool)
  for a_lnk in lnkpool:
   link = a_lnk.get("href")
   if not link: continue
   if link.startswith("http"):
    if not url_original in link: continue
   link = urljoin(url, link)
   with tlock:
    if link in urls_crawled.keys(): continue
    else: urls_crawled[link] = True
   if depth < max_depth:
    if debug == 1: print(link)
    scrape(link, url_original, depth+1)
  del soup
  del r
 except Exception as error:
  if debug == 1: print(error) 

def _start():
 global keywords
 while len(targets):
  with tlock: target = targets.pop(0)
  target_root = get_url_root(target)
  scrape(target, target_root)

def main():
 for i in range(threads):
  t=threading.Thread(target=_start)
  t.start()

if __name__ == "__main__":
 main()
