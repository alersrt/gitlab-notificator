#!/usr/bin/python

import json
import time
from datetime import datetime
from datetime import timedelta

import gi
import requests
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Notify', '0.7')
from gi.repository import GdkPixbuf, Notify


class PushData:
    action = ""
    ref_type = ""
    ref = ""
    
    
class Event:
    created_at = ""
    action_name = ""
    author_username = ""
    target_type = ""
    target_title = ""
    
    
class Project:
    events = []
    

class GitLabAPI:
    def __init__(self, url, token, timeout):
        self.URL_API = url + '/api/v4/'
        self.HEADERS = {"PRIVATE-TOKEN": token}
        self.TIMEOUT = timeout

    def projets(self):
        return requests.get(URL_API + 'projects', headers=HEADERS).json()
    
    def events(self, project_id):
        return requests.get(URL_API+'projects/'+project_id+'/events', headers=HEADERS).json()
   
     
        
config = json.loads(open('properties.json').read())
# URL API for GitLab
URL_API = config['url']+'/api/v4/'
# Token for GitLab
HEADERS = config['header.token']
# Timeout in seconds
TIMEOUT = int(config['timeout'])

Notify.init("GitLab Notifier")

while True:
    t1 = datetime.utcnow()
    projects = requests.get(URL_API + 'projects', headers=HEADERS).json()
    for project in projects:
        events = requests.get(URL_API+'projects/'+str(project['id'])+'/events', headers=HEADERS).json()
    
        for event in events:
            created_at = event['created_at'] if event['created_at'] is not None else '2000-01-01T00:00:00.000Z'
            if datetime.utcnow() - datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ") > timedelta(seconds=(TIMEOUT+5)):
                continue
            action_name     = event['action_name'] if event['action_name'] != None else ''
            author_username = event['author_username'] if event['author_username'] != None else ''
            target_type     = event['target_type'] if event['target_type'] != None else ''
            target_title    = event['target_title'] if event['target_title'] != None else ''
            push_action     = event['push_data']['action'] if 'push_data' in event else ''
            push_ref_type   = event['push_data']['ref_type'] if 'push_data' in event else ''
            push_ref        = event['push_data']['ref'] if 'push_data' in event else ''
            note_body       = event['note']['body'] if 'note' in event else ''
            
            if (action_name == "pushed to") or (action_name == "deleted"):
                title = author_username + ' ' + action_name + ' ' + target_type
                message = push_action + ' ' + push_ref_type + ' ' + push_ref
            elif action_name == "commented on":
                title = author_username + ' ' + action_name + ' ' + target_type
                message = target_title + '\n' + note_body
            else:
                title = author_username + ' ' + action_name + ' ' + target_type
                message = target_title
    
         
            user_avatar = GdkPixbuf.PixbufLoader()
            user_avatar.write(requests.get(event['author']['avatar_url']).content)
            user_avatar.close()
            
            n = Notify.Notification.new(title, message, icon="dialog-information")
            if user_avatar != None:
                n.set_image_from_pixbuf(user_avatar.get_pixbuf())
            n.show()
    time.sleep(TIMEOUT)
