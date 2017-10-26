#!/usr/bin/env python2.7
# 

# pip-2.7 install --user --upgrade google-api-python-client

# code are mainly from 
# -- https://developers.google.com/drive/v3/web/quickstart/python

# before runing this code, make sure you have created credential via the following link: 
# https://console.developers.google.com/start/api?id=drive

from __future__ import print_function
import httplib2
import os, sys, io, re

from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

#try:
#    import argparse
#    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
#except ImportError:
#    flags = None



class CAAP_Google_Drive_Operator(object):
    # 
    def __init__(self):
        self.scopes = 'https://www.googleapis.com/auth/drive.readonly'
        self.credential_dir = '.' # os.path.join(os.path.expanduser('~'), '.caap')
        self.credential_dir = os.path.join(os.path.expanduser('~'), '.caap')
        #self.credential_file = os.path.join(self.credential_dir, 'Key_for_Google_Drive_from_A3COSMOS.json')
        #self.credential_file = os.path.join(self.credential_dir, 'CAAP Google Drive Operator-e11311ed8811.json') # rw but not added to member list on Team Drive
        self.credential_file = os.path.join(self.credential_dir, 'CAAP Google Drive Operator-93fcdd7331f1.json') # r
        self.client_email = 'a3cosmos-readonly@a3cosmos-team-drive-operator.iam.gserviceaccount.com'
        self.quota_user = '93fcdd7331f160847e41cab94524c9a7edcbb928' # 'a3cosmos-readonly'+'-'+datetime.today().strftime('%Y%m%d-%H%M%S.%f')
        self.credential_store = None
        self.application_name = 'CAAP Google Drive Operator'
        self.credential = None
        self.http = None
        self.service = None
        self.team_drive = None
        self.team_drive_name = 'A3COSMOS'
        self.get_credential()
        self.get_team_drive()
    # 
    def get_credential(self):
        if not os.path.exists(self.credential_dir):
            os.makedirs(self.credential_dir)
        if not os.path.exists(self.credential_file):
            print('Error! Key "%s" was not found! Please ask A3COSMOS for the "Key_for_Google_Drive_from_A3COSMOS.json"!'%(self.credential_file))
            sys.exit()
        #if not os.path.exists(self.credential_file+'.ok'):
            #self.credential_store = Storage(self.credential_file)
            #self.credential = []
            #flow = client.flow_from_clientsecrets(self.credential_file, self.scopes)
            #flow.user_agent = self.application_name
            #if flags:
            #    credential = tools.run_flow(flow, self.credential_store, flags)
            #else: # Needed only for compatibility with Python 2.6
            #    credential = tools.run(flow, self.credential_store)
            #print('Storing credential to ' + self.credential_file)
            #os.system('touch "%s"'%(self.credential_file+'.ok'))
            # 
        #self.credential_store = Storage(self.credential_file)
        #self.credential = self.credential_store.get()
        # --
        # -- 20171023
        # -- use serveraccount
        # -- https://developers.google.com/drive/v3/web/handle-errors (403: Rate Limit Exceeded)
        # -- https://developers.google.com/identity/protocols/OAuth2ServiceAccount (Preparing to make an authorized API call)
        self.credential = ServiceAccountCredentials.from_json_keyfile_name(self.credential_file, scopes=self.scopes)
        # 
        self.http = self.credential.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=self.http)
        #print(self.service)
        #self.print_files_in_drive()
    # 
    def print_files_in_drive(self):
        if self.service:
            time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
            results = self.service.files().list(pageSize=30, 
                                                fields="nextPageToken, files(id, name, size, mimeType, parents, md5Checksum)", 
                                                quotaUser=self.quota_user
                                                ).execute()
            items = results.get('files', [])
            if not items:
                print('No files found.')
            else:
                print('Files:')
                for item in items:
                    print('{0} ({1})'.format(item['name'], item['id']))
    # 
    def get_team_drive(self):
        # Teamdrives
        # -- https://developers.google.com/drive/v3/reference/teamdrives
        # -- https://developers.google.com/drive/v3/reference/teamdrives/list
        if self.service:
            self.team_drive = None
            token = None
            while True:
                try:
                    time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                    query = self.service.teamdrives().list(pageSize=1, 
                                                            pageToken=token, 
                                                            quotaUser=self.quota_user
                                                        ).execute()
                    #print(query)
                    for item in query.get('teamDrives'):
                        #print('Team Drive Id: %s; Name: %s;'%(item['id'], item['name']))
                        if item['name'] == self.team_drive_name:
                            self.team_drive = item
                            break
                    token = query.get('nextPageToken')
                    if not token:
                        break
                except errors.HttpError, error:
                    print('An error occurred: %s'%(error))
                    break
                token = query.get('nextPageToken', None)
            if not self.team_drive:
                print('Error! Failed to find the Team Drive "%s"!'%(self.team_drive_name))
                return
            # 
            #print('Team Drive: "%s" (Id: %s)'%(self.team_drive['name'], self.team_drive['id']))
    # 
    def get_parents(self, input_resource):
        # Search for Files
        # -- https://developers.google.com/drive/v3/reference/files/list
        # -- https://developers.google.com/drive/v3/web/search-parameters
        output_parents = []
        if self.service and self.team_drive and len(input_resource)>0:
            # 
            item_id = input_resource.get('id')
            while item_id is not None:
                # 
                try:
                    time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                    query = self.service.files().get(
                                                        fileId=item_id, 
                                                        supportsTeamDrives=True, 
                                                        fields="id, name, size, mimeType, parents, md5Checksum", 
                                                        quotaUser=self.quota_user
                                                    ).execute()
                    #print(query)
                    if query is not None:
                        item = query
                        item_parents = item.get('parents')
                        if item_parents is not None:
                            item_id = item_parents[0]
                            if item_id != input_resource.get('id'):
                                output_parents.insert(0,item)
                        else:
                            item_id = None
                            break
                except errors.HttpError, error:
                    print('An error occurred: %s'%(error))
                    break
        # 
        return output_parents
    # 
    def get_folder_by_name(self, folder_name, verbose = True):
        # File List Search
        # -- https://developers.google.com/drive/v3/reference/files/list
        # -- https://developers.google.com/drive/v3/web/search-parameters
        folder_resources = []
        if self.service and self.team_drive and len(folder_name)>0:
            # 
            if folder_name == '*':
                return folder_resources
            # 
            if folder_name.find('/')>=0:
                folder_paths = folder_name.split('/')
                for folder_pathi in range(len(folder_paths)):
                    folder_name = folder_paths[folder_pathi]
            else:
                folder_paths = []
            # 
            if folder_name.find('*')>=0:
                folder_names = folder_name.split('*')
                query_str = "trashed = false and mimeType='application/vnd.google-apps.folder'"
                for folder_namei in range(len(folder_names)):
                    if folder_names[folder_namei] != '':
                        query_str = query_str + " and name contains '"+folder_names[folder_namei]+"'"
            else:
                query_str = "trashed = false and mimeType='application/vnd.google-apps.folder' and name = '"+folder_name+"'"
            # 
            if len(folder_paths)>=2:
                folder_pathi = len(folder_paths)-2
                # len(folder_paths)-2 is the parent directory of the last element [len(folder_paths)-1]
                if folder_paths[folder_pathi] != '*' and folder_paths[folder_pathi] != '':
                    folder_parents = self.get_folder_by_name(folder_paths[folder_pathi], verbose = verbose)
                    if len(folder_parents)>0:
                        query_str = query_str + str(' and ('%(folder_parent.get('id')))
                        for folder_parenti in range(len(folder_parents)):
                            folder_parent = folder_parents[folder_parenti]
                            if folder_parenti != len(folder_parents)-1:
                                query_str = query_str + str('\'%s\' in parents or '%(folder_parent.get('id')))
                            else:
                                query_str = query_str + str('\'%s\' in parents)'%(folder_parent.get('id')))
                        else:
                            print('Error! "%s" could not be found! Because its parent directory could not be found!'%('/'.join(folder_paths)))
                            sys.exit()
            # 
            if verbose:
                print('Query with: "%s"'%(query_str))
            # 
            token = None
            while True:
                try:
                    time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                    query = self.service.files().list(
                                                        q=query_str, 
                                                        supportsTeamDrives=True, 
                                                        includeTeamDriveItems=True, 
                                                        teamDriveId=self.team_drive['id'], 
                                                        corpora='teamDrive', 
                                                        fields='nextPageToken, files(id, name, size, mimeType, parents, md5Checksum)', 
                                                        pageSize=10, 
                                                        pageToken=token, 
                                                        quotaUser=self.quota_user
                                                    ).execute()
                    #print(query)
                    for item in query.get('files'):
                        if verbose:
                            print('Found folder: "%s" (Id: %s)' % (item.get('name'), item.get('id')))
                        folder_resources.append(item)
                        #break
                    # 
                    token = query.get('nextPageToken')
                    if not token:
                        break
                except errors.HttpError, error:
                    print('An error occurred: %s'%(error))
                    break
                token = query.get('nextPageToken', None)
            # 
            # check parent directories are consistent with the input if len(folder_paths)>=3
            if len(folder_paths)>=3:
                folder_itemi = 0
                while folder_itemi < len(folder_resources):
                    folder_item = folder_resources[folder_itemi]
                    folder_check = True
                    # now we need to get the all the folder_parents for folder_item
                    folder_parents = self.get_parents(folder_item)
                    folder_pathi = 3
                    while folder_pathi <= len(folder_paths):
                        folder_pathj = len(folder_paths) - folder_pathi
                        folder_pathk = len(folder_parents) - folder_pathi
                        if folder_pathj>=0 and folder_pathk>=0:
                            folder_name_match = re.match(folder_paths[folder_pathj], folder_parents[folder_pathk].get('name'))
                            if verbose:
                                print('Checking parent directories "%s" to "%s"'%(folder_paths[folder_pathj], folder_parents[folder_pathk].get('name')))
                            if folder_name_match is None:
                                folder_check = False
                                break
                        else:
                            break
                        folder_pathi = folder_pathi + 1
                    # 
                    if folder_check == True:
                        folder_itemi = folder_itemi + 1
                    else:
                        del folder_resources[folder_itemi]
            # 
        return folder_resources
    # 
    def get_file_by_name(self, file_name, verbose = True):
        # File List Search
        # -- https://developers.google.com/drive/v3/reference/files/list
        # -- https://developers.google.com/drive/v3/web/search-parameters
        file_resources = []
        if self.service and self.team_drive and len(file_name)>0:
            # 
            if file_name == '*':
                return file_resources
            # 
            if file_name.find('/')>=0:
                file_paths = file_name.split('/')
                for file_pathi in range(len(file_paths)):
                    file_name = file_paths[file_pathi]
            else:
                file_paths = []
            # 
            if file_name.find('*')>=0:
                file_names = file_name.split('*')
                query_str = "trashed = false"
                for file_namei in range(len(file_names)):
                    if file_names[file_namei] != '':
                        query_str = query_str + " and name contains '"+file_names[file_namei]+"'"
            else:
                query_str = "trashed = false and name = '"+file_name+"'"
            # 
            if len(file_paths)>=2:
                file_pathi = len(file_paths)-2
                # len(file_paths)-2 is the parent directory of the last element [len(file_paths)-1]
                if file_paths[file_pathi] != '*' and file_paths[file_pathi] != '':
                    file_parents = self.get_folder_by_name(file_paths[file_pathi], verbose = verbose)
                    if len(file_parents)>0:
                        query_str = query_str + str(' and (')
                        for file_parenti in range(len(file_parents)):
                            file_parent = file_parents[file_parenti]
                            if file_parenti != len(file_parents)-1:
                                query_str = query_str + str('\'%s\' in parents or '%(file_parent.get('id')))
                            else:
                                query_str = query_str + str('\'%s\' in parents)'%(file_parent.get('id')))
                    else:
                        print('Error! "%s" could not be found! Because its parent directory could not be found!'%('/'.join(file_paths)))
                        sys.exit()
            # 
            if verbose:
                print('Query with: "%s"'%(query_str))
            # 
            token = None
            while True:
                try:
                    time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                    query = self.service.files().list(
                                                        q=query_str, 
                                                        supportsTeamDrives=True, 
                                                        includeTeamDriveItems=True, 
                                                        teamDriveId=self.team_drive['id'], 
                                                        corpora='teamDrive', 
                                                        fields='nextPageToken, files(id, name, size, mimeType, parents, md5Checksum)', 
                                                        pageSize=10, 
                                                        pageToken=token, 
                                                        quotaUser=self.quota_user
                                                    ).execute()
                    #print(query)
                    for item in query.get('files'):
                        if verbose:
                            print('Found file: "%s" (Id: %s; MD5: %s)' % (item.get('name'), item.get('id'), item.get('md5Checksum')))
                        file_resources.append(item)
                        #break
                    # 
                    token = query.get('nextPageToken')
                    if not token:
                        break
                except errors.HttpError, error:
                    print('An error occurred: %s'%(error))
                    break
                token = query.get('nextPageToken', None)
            # 
            # check parent directories are consistent with the input if len(file_paths)>=3
            if len(file_paths)>=3:
                file_itemi = 0
                while file_itemi < len(file_resources):
                    file_item = file_resources[file_itemi]
                    file_check = True
                    # now we need to get the all the file_parents for file_item
                    file_parents = self.get_parents(file_item)
                    file_pathi = 3
                    while file_pathi <= len(file_paths):
                        file_pathj = len(file_paths) - file_pathi
                        file_pathk = len(file_parents) - file_pathi
                        if file_pathj>=0 and file_pathk>=0:
                            file_name_match = re.match(file_paths[file_pathj], file_parents[file_pathk].get('name'))
                            if verbose:
                                print('Checking parent directories "%s" to "%s"'%(file_paths[file_pathj], file_parents[file_pathk].get('name')))
                            if file_name_match is None:
                                file_check = False
                                break
                        else:
                            break
                        file_pathi = file_pathi + 1
                    # 
                    if file_check == True:
                        file_itemi = file_itemi + 1
                    else:
                        del file_resources[file_itemi]
            # 
        return file_resources
    # 
    def print_files_in_folder(self, folder_name):
        # File List Search
        # -- https://developers.google.com/drive/v3/reference/files/list
        # -- https://developers.google.com/drive/v3/web/search-parameters
        file_resources = []
        # 
        if self.service and self.team_drive and len(folder_name)>0:
            # 
            folder_resources = self.get_folder_by_name(folder_name)
            if len(folder_resources)==0:
                print('Error! Folder "%s" was not found!'%(folder_name))
                return
            # 
            query_str = '('
            for folder_resource_i in range(len(folder_resources)):
                folder_resource = folder_resources[folder_resource_i]
                if folder_resource_i == 0:
                    query_str = query_str + str('\'%s\' in parents'%(folder_resource.get('id')))
                else:
                    query_str = query_str + str(' or \'%s\' in parents'%(folder_resource.get('id')))
            query_str = query_str + ')'
            # 
            token = None
            while True:
                try:
                    time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                    query = self.service.files().list(
                                                        q=query_str, 
                                                        supportsTeamDrives=True, 
                                                        includeTeamDriveItems=True, 
                                                        teamDriveId=self.team_drive['id'], 
                                                        corpora='teamDrive', 
                                                        fields='nextPageToken, files(id, name, size, mimeType, parents, md5Checksum)', 
                                                        pageSize=100, 
                                                        pageToken=token, 
                                                        quotaUser=self.quota_user
                                                    ).execute()
                    #print(query)
                    for item in query.get('files'):
                        print('Found File in the Folder: "%s" (Id: %s, MimeType: %s)' % (item.get('name'), item.get('id'), item.get('mimeType')))
                        file_resources.append(item)
                    # 
                    token = query.get('nextPageToken')
                    if not token:
                        break
                except errors.HttpError, error:
                    print('An error occurred: %s'%(error))
                    break
                token = query.get('nextPageToken', None)
            # 
            return file_resources
    # 
    def find_file_in_folder(self, folder_name, file_name):
        # File List Search
        # -- https://developers.google.com/drive/v3/reference/files/list
        # -- https://developers.google.com/drive/v3/web/search-parameters
        file_resources = []
        # 
        if self.service and self.team_drive and len(folder_name)>0 and len(file_name)>0:
            # 
            folder_resources = self.get_folder_by_name(folder_name)
            if len(folder_resources)==0:
                print('Error! Folder "%s" was not found!'%(folder_name))
                return file_resources
            # 
            query_str = '('
            for folder_resource_i in range(len(folder_resources)):
                folder_resource = folder_resources[folder_resource_i]
                if folder_resource_i == 0:
                    query_str = query_str + str('\'%s\' in parents'%(folder_resource.get('id')))
                else:
                    query_str = query_str + str(' or \'%s\' in parents'%(folder_resource.get('id')))
            query_str = query_str + ')'
            # 
            if file_name.find('*')>=0:
                file_name_split = file_name.split('*')
                for file_name_split_item in file_name_split:
                    if file_name_split_item != '':
                        query_str = query_str + str(' and name contains \'%s\''%(file_name_split_item))
            else:
                query_str = query_str + str(' and name = \'%s\''%(file_name))
            print('Query str: %s'%(query_str))
            # 
            token = None
            while True:
                try:
                    time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                    query = self.service.files().list(
                                                        q=query_str, 
                                                        supportsTeamDrives=True, 
                                                        includeTeamDriveItems=True, 
                                                        teamDriveId=self.team_drive['id'], 
                                                        corpora='teamDrive', 
                                                        fields='nextPageToken, files(id, name, size, mimeType, parents, md5Checksum)', 
                                                        pageSize=100, 
                                                        pageToken=token, 
                                                        quotaUser=self.quota_user
                                                    ).execute()
                    #print(query)
                    for item in query.get('files'):
                        print('Found File in the Folder: "%s" (Id: %s, MimeType: %s)' % (item.get('name'), item.get('id'), item.get('mimeType')))
                        file_resources.append(item)
                    # 
                    token = query.get('nextPageToken')
                    if not token:
                        break
                except errors.HttpError, error:
                    print('An error occurred: %s'%(error))
                    break
                token = query.get('nextPageToken', None)
            # 
            return file_resources
    # 
    def download_files(self,file_resources):
        # Download
        # -- https://developers.google.com/drive/v3/web/manage-downloads
        if self.service and self.team_drive:
            if type(file_resources) is not list:
                file_resources = [file_resources]
            for file_resource in file_resources:
                file_id = file_resource.get('id')
                time.sleep(0.25) # Google Drive has a limit of 10 query per second per user
                request = self.service.files().get_media(fileId=file_id, quotaUser=self.quota_user)
                #fh = io.BytesIO()
                fh = io.FileIO(file_resource.get('name'), mode='wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print('Downloading "%s" (%.0f%%)' % (file_resource.get('name'), status.progress()*100.0))
                # verify downloaded file
                if done:
                    file_size = file_resource.get('size')
                    file_size_downloaded = os.path.getsize(file_resource.get('name'))
                    print('Checking file size %s and downloaded size %s'%(file_size, file_size_downloaded))
                    if long(file_size_downloaded) != long(file_size):
                        print('Error! File size %s is different from the downloaded size %s! Delete the failed download and please re-try!'%(file_size, file_size_downloaded))
                        os.system('rm "%s"'%(file_resource.get('name')))
                    else:
                        print('OK!')










