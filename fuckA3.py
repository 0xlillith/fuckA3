import os
import sys
import requests
import ffmpeg # Requires only pip install ffmpeg-python, but not ffmpeg
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import json
import re

print("\n** Loading site to extract URL to media files...")

options = webdriver.ChromeOptions()

options = Options()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
# options.set_capability('pageLoadStrategy', {'eager'})
options.add_argument("user-data-dir=C:\\Users\\lillith\\AppData\\Local\\Google\\Chrome\\User Data\\")
driver = webdriver.Chrome(options=options)

# Import URL from command line argument
driver.get(sys.argv[1])

# Define final export file name from site title
chapterName = re.sub(r'[!@#$:/="]', '', driver.title) # RE to remove symbols from title
print("\n** Fetching " +chapterName)

# Click ACCEPT cookies button
#element = driver.find_element(By.PARTIAL_LINK_TEXT, "ACEPTAR")
#element.click()

# Wait only until PLAY button is visible
WebDriverWait(driver, timeout=10).until(ec.visibility_of_element_located((By.CLASS_NAME, "iUTaSS")))

# Click PLAY Button.
element = driver.find_element(By.CLASS_NAME, "iUTaSS")
element.click()

def process_browser_log_entry(entry):
  response = json.loads(entry['message'])['message']
  return response

audioFound = False
videoFound = False
while True:
  browser_log = driver.get_log('performance') 
  events = [process_browser_log_entry(entry) for entry in browser_log]
  events = [event for event in events if 'Network.response' in event['method']]

  for e in events:
    if 'vo_0.ts' in str(e['params']):
      urlVideo = str(e['params']).split("url': '")[-1].split("'}, ")[0]
      print("\n--> Found audio URL: " +urlVideo)
      videoFound = True
    if '==_0.ts' in str(e['params']):
      urlAudio = str(e['params']).split("url': '")[-1].split("'}, ")[0]
      print("\n--> Found video URL: " +urlAudio)
      audioFound = True
    if audioFound and videoFound == True:
      break
  if audioFound and videoFound == True:
    break
driver.quit()

#  URL spliting
listVideo = urlVideo.split(".ts")
listAudio = urlAudio.split(".ts")
videoPre = listVideo[0][:-1]
videoPost = ".ts" + listVideo[1]
audioPre = listAudio[0][:-1]
audioPost = ".ts" + listAudio[1]

# Download using Requests
i = 1
r = requests.get(videoPre +str(i) +videoPost)
while r.status_code != 404:
  r = requests.get(videoPre +str(i) +videoPost)
  open('video.ts', 'ab').write(r.content)
  r = requests.get(audioPre +str(i) +audioPost)
  open('audio.ts', 'ab').write(r.content)
  print("** Downloading audio #" +str(i) +" and video #" +str(i), end='\r')
  i = i + 1

print("\n\n** Joining video .TS and audio .TS to .mp4 file")
(
  ffmpeg
  .input('video.ts')
  .output(chapterName +".mp4", codec='copy')
  .global_args('-i', 'audio.ts')
  .run(quiet=True)
)
print("\n** Removing temporal .TS files")
os.remove("video.ts")
os.remove("audio.ts")
print("\n** Done <3 **")
