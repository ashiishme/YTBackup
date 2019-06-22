import os
import json
import sys
import time

import subprocess
import urllib.request
from bs4 import BeautifulSoup
from pytube import YouTube

import tkinter as tk;
from tkinter import filedialog

COMMAND_TYPE = sys.argv

ERROR = ''




# Backup function
def Backup():
    def get_media_metadata(filename):
        result = subprocess.Popen(
            ["hachoir-metadata", filename, "--raw"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        results = result.stdout.read().decode("utf-8").split("\r\n")

        # just a little bit of error checking
        if isinstance(results, list):
            try:
                if results[0].startswith("[err!]"):
                  ERROR = 'FILE_ERROR'
                  return ERROR
                
                if results[3].startswith("- height: "):
                    return int(results[3].lstrip("- height: "))
                else:
                    return None
            except IndexError:
                print("\n* No Dimensions Found for " + filename)
                return None
        else:
            return None

    data = []
    # PATH_NAME = input("Enter Directory Name To Backup: ")
    PATH_NAME = dest_folder_path.get()

    # spinner strings
    def spinning_cursor():
        while True:
            for cursor in "|/-\\":
                yield cursor

    spinner = spinning_cursor()

    # creates the array
    def create_file_lists(path):
        # spinner
        print("\rDoing Work ( {0} )".format(next(spinner)), end="")

        if os.path.isfile(path):
          video_info = get_media_metadata(os.path.relpath(path))
          # checks if there is any error (ie: if its not a video)
          if video_info != 'FILE_ERROR':
            data.append([os.path.relpath(path), video_info])

        if os.path.isdir(path):
            for x in os.listdir(path):
                # recursively get the files
                create_file_lists(os.path.join(path, x))
        return data

    # create json file
    def createJSON():
        with open(PATH_NAME + ".json", "w") as outfile:
            json.dump(create_file_lists(PATH_NAME), outfile)
            print("\nSuccessfully created " + PATH_NAME + ".json")

    createJSON()


# Restore function
def Restore():
    # BACKUP_FILE = 'videos.json'
    BACKUP_FILE = input("Enter Backup file path: ")
    OUTPUT_FOLDER = input("Enter Output Folder Name: ")

    # mix it up, soup it up
    def get_video_link(title):
        print('\nFetching "' + title + '"')
        query = urllib.parse.quote(title)
        url = "https://www.youtube.com/results?search_query=" + query
        response = urllib.request.urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        return soup.find(attrs={"class": "yt-uix-tile-link"})["href"]

    # progress bar
    def get_progress(stream, chunk, file_handle, bytes_remaining):
        percent = float(round((1 - bytes_remaining / filesize), 2))
        progress = "\rProgress: [{0:50s}] {1:.1f}%".format("#" * int(percent * 50), percent * 100)
        print(progress, end="")

    global filesize
    global filesizeMB

    # read json
    with open(BACKUP_FILE) as f:
        data = json.load(f)
        for i in data:

            # get the title - "my-video.mp"
            title = os.path.basename(i[0])
            title, ext = os.path.splitext(title)

            # get the dirname - "/video/html"
            dirname = os.path.join(OUTPUT_FOLDER, os.path.dirname(i[0]))
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            yt = YouTube(get_video_link(title), on_progress_callback=get_progress)

            # get the video by resolution/quality
            video = yt.streams.filter(res=str(i[1]) + "p").first()
            # if the specific quality is not available fallback to max quality
            if video is None:
                video = yt.streams.first()

            filesize = video.filesize
            filesizeMB = str(round(filesize / float(1 << 20), 2)) + "MB"

            print('\nDownloading "' + str(title) + '" size: ' + filesizeMB)
            video.download(dirname)




# ---------------- UI --------
window = tk.Tk()
window.title('YTBackup')
window.geometry("600x400") #Width x Height
window.resizable(width=False, height=False)
# title
title = tk.Label(text='YTBackup', font=('Century Gothic', 18, 'normal'))
title.grid(row=0, column=3, pady=20)

# filedialoug
dest_folder_path = tk.StringVar()
def browse_button_dest():
    global dest_folder_path
    
    filename = filedialog.askdirectory()

    dest_folder_path.set(filename)
    print(filename)

# destination
file_Label = tk.Label(text='Destination Folder')
filedialog_btn = tk.Button(text="Browse", command=browse_button_dest, width=20)
file_Label.grid(row=1, sticky=tk.E)
filedialog_btn.grid(row=1, column=5, sticky=tk.W)

# # button
button = tk.Button(text='Backup', command=Backup, width=10)
button.grid(row=2, column=5, pady=10, sticky=tk.E)

window.mainloop()


# check for args
if len(COMMAND_TYPE) > 1:
  if COMMAND_TYPE[1] == "--backup":
      Backup()
  elif COMMAND_TYPE[1] == "--restore":
      Restore()
else:
    print("Please specify what do you want to do --backup or --restore")

