#!/usr/bin/env python

import json, os, re, yaml
from datetime import date

#from pathlib import Path

#import http.client, urllib, sys, random, time, requests

CONFIG_FILE = 'config.yaml'
with open(CONFIG_FILE, 'r') as config_file:
    config = yaml.safe_load(config_file)

uhd_api_key = config['config']['uhd_api_key']
movie_api_key: config['config']['movie_api_key']
pushover_api_key: config['config']['pushover_api_key']
pushover_user: config['config']['pushover_user']
plex1: config['config']['plex1_domain']
plex2: config['config']['plex2_domain']
uhd_api_url: config['config']['uhd_api_url']
movie_api_url: config['config']['movie_api_url']


rclone_log_file = "logs/rclone." + str(date.today()) + ".log"

class Movie:
    def __init__(self, title, path, id, imdb):
        self.title = title
        self.path = re.escape(path).replace(';','\;')
        self.id = id
        self.imdb = imdb
        self.converted = re.escape(os.path.dirname(path) + "/" + (os.path.splitext(os.path.basename(path))[0])+".m4v").replace(';','\;')

def content_type():
    if os.path.isfile("movie.json"):
        return "movie"
    elif os.path.isfile("tv.json"):
        return "tv"
    elif os.path.isfile("uhd.json"):
        return "uhd"

def get_remote():
    with open("remote", "r") as f:
        remote=f.read()
        remote=int(remote)
        f.close()
        
        if remote < 4:
            remote += 1
        elif remote == 4:
            remote = 1
        else:
            remote = 1

    with open("remote", "w") as f:
        f.write(str(remote))
        f.close()

    return str(remote)

#Convert SD/HD Movie to friendly formats, rename, put in sorted folder
def movie_convert(path, imdb, converted):
    genre_file = "genre"
    #os.system("python /home/bradley/sickbeard_mp4_automator/manual.py -i " + path + " -imdb " + imdb)
    #os.system("filebot -rename " + converted + "  --output ~/.local/Sorted\ Movies/ --format \"{genres.contains(\'Animation\') ? \'Animated\' : genres.contains(\'Science Fiction\') ? \'SciFi\' : genres.contains(\'Comedy\') && genres.contains(\'Romance\') ? \'RomCom\' : genres.contains(\'Horror\') ? \'Horror\' : genres[0]}/{any{collection}{ny}}/{fn}\" --db TheMovieDB -exec echo {f} > " + genre_file)
    with open(genre_file, "r") as f:
        genre=str(list(f)[-1])
        f.close()
    #os.remove(genre_file)
    return genre

#Rename and sort UHD movie
def uhd_convert(path):
    genre_file = "genre"
    os.system("filebot -rename " + path + "  --output ~/.local/4K\ Sorted/ --format \"{genres.contains(\'Animation\') ? \'Animated\' : genres.contains(\'Science Fiction\') ? \'SciFi\' : genres.contains(\'Comedy\') && genres.contains(\'Romance\') ? \'RomCom\' : genres.contains(\'Horror\') ? \'Horror\' : genres[0]}/{any{collection}{ny}}/{fn}\" --db TheMovieDB -exec echo {f} > " + genre_file)
    with open(genre_file, "r") as f:
        genre=str(list(f)[-1])
        f.close()
    os.remove(genre_file)
    return genre

def movie_upload(remote, content, file_path, log):
    if content == "movie":
        prefix = re.escape("Sorted Movies")
    elif content == "uhd":
        prefix = re.escape("4K Sorted")
    local_path = re.escape(os.path.dirname(file_path)).replace(';','\;')    
    remote_path = prefix + str(remote) + ":/" + os.path.dirname(os.path.relpath(file_path, "/home/bradley/.local")).replace(';','\;')
    #os.system("/usr/bin/rclone move " + rclone_path + " " + remote_path + " -v --stats=15s --log-file " + log)
    return remote_path 

content = content_type()

if content == "movie":
    data = "movie.json"
    with open(data, "r") as f:
        m = json.load(f)
        f.close
    #os.remove(genre_file)   //remove comment when live
    movie = Movie(m['movietitle'], m['moviepath'], m['movieid'],m['imdbid'])
    genre_path = movie_convert(movie.path, movie.imdb, movie.converted)
    upload = movie_upload(get_remote(), content, movie.path, rclone_log_file)

elif content == "tv":
    data = "tv.json"
else:
    data = "uhd.json"
    with open(data, "r") as f:
        m = json.load(f)
        f.close
    #os.remove(genre_file)   //remove comment when live
    movie = Movie(m['movietitle'], m['moviepath'], m['movieid'],m['imdbid'])
    upload = movie_upload(get_remote(), content, movie.path, rclone_log_file)

#print (upload)
print (movie.converted)