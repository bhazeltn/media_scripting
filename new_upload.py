#!/usr/bin/env python

import json, os, yaml, subprocess, http.client, urllib, requests, random
from datetime import date
from re import escape

#from pathlib import Path

#import http.client, urllib, sys, random, time, requests

CONFIG_FILE = 'config.yaml'
with open(CONFIG_FILE, 'r') as config_file:
    config = yaml.safe_load(config_file)
uhd_api_key = config['config']['uhd_api_key']
movie_api_key = config['config']['movie_api_key']
pushover_api_key = config['config']['pushover_api_key']
pushover_user = config['config']['pushover_user']
plex1 = config['config']['plex1_domain']
plex2 = config['config']['plex2_domain']
uhd_api_url = config['config']['uhd_api_url']
movie_api_url = config['config']['movie_api_url']


class Movie:
    def __init__(self, title, path, id, imdb):
        self.title = title
        prefix = "/home/bradley/.local"
        path = prefix + path
        self.path = escape(path).replace(';','\;')
        self.id = id
        self.imdb = imdb
        self.converted = escape(os.path.dirname(path) + "/" + (os.path.splitext(os.path.basename(path))[0])+".m4v").replace(';','\;')

def get_remote():
    with open("remote", "r") as f:
        remote=f.read()
        remote=int(remote)
        f.close() 
    print (remote)
    if remote < 4:
        remote += 1
    elif remote == 4:
        remote = 1
    else:
        remote = 1
    with open("remote", "w") as f:
        f.write(str(remote))
        f.close()
    remote = "4k" + str(remote) + ":/"
    return remote

def convert(movie_file, imdb):
    os.system("python /home/bradley/sickbeard_mp4_automator/manual.py -i " + movie_file + " -imdb " + imdb)

def rename(movie_file, content):
    if content == "movie":
        base = "Sorted\ Movies/"
    elif content == "uhd":
        base = "4K\ Sorted/"
    os.system("filebot -rename " + movie_file + "  --output ~/.local/" + base + " --format \"{genres.contains(\'Animation\') ? \'Animated\' : genres.contains(\'Science Fiction\') ? \'SciFi\' : genres.contains(\'Comedy\') && genres.contains(\'Romance\') ? \'RomCom\' : genres.contains(\'Horror\') ? \'Horror\' : genres[0]}/{any{collection}{ny}}/{fn}\" --db TheMovieDB -exec echo {f} > genre")
    with open("genre", "r") as f:
        genre=str(list(f)[-1])
        f.close()
    os.remove("genre")
    return genre

def upload(to_upload):
    local_path = escape(os.path.dirname(to_upload)).replace(';','\;')    
    remote_path = escape(get_remote() + os.path.dirname(os.path.relpath(to_upload, "/home/bradley/.local"))).replace(';','\;')
    os.system("/usr/bin/rclone move " + local_path + " " + remote_path + " -v --stats=15s --log-file logs/rclone." + str(date.today()) + ".log")

def del_movie(movie_id, radarr_api, radarr_url):
    print (radarr_api)
    header = {
        'X-api-key': radarr_api
    }
    del_url = radarr_url + movie_id +  "?deleteFiles=false&addExclusion=true"
    r = requests.delete(del_url, headers=header)
    print (del_url)

def notify(title, api, user):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": api,
        "user": user,
        "message": "Processed and uploaded " + title,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

def update_plex(to_update, plex_server, content):
    print("Plex")

    with open(content, "w") as write_file:
        write_file.write(to_update)
        write_file.close

    print ("Plex Update File Created")
    os.system("rsync -avz " + content + " plex@" + plex_server + ":/var/lib/plexmediaserver/scripts/")
    os.remove(content)

def locked(content):
    while os.path.isfile(content):
        t=random.randint(1,60)
        print("Waiting for other conversion to finish, sleeping for "+str(t)+" seconds")
        time.sleep(t)
 
def main():
    if os.path.isfile("movie.json"):
        with open("movie.json", "r") as f:
            m = json.load(f)
            f.close
        movie = Movie(m['movietitle'], m['moviepath'], m['movieid'],m['imdbid'])
        lockfile="movie.lock"
        locked(lockfile)
        os.mknod(lockfile)
        convert(movie.path, movie.imdb)
        os.remove(lockfile)
        moved = rename(movie.converted, "movie")
        upload(moved)
        del_movie(movie.id, movie_api_key, movie_api_url)
        notify(movie.title, pushover_api_key, pushover_user)
        update_plex(moved, plex1_domain, "movie")   
    else:
        quit("No Good")
    #elif os.path.isfile("tv.json"):
    #    return "tv"
    #elif os.path.isfile("uhd.json"):
    #    return "uhd"

main()