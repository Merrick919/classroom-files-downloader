from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import os.path
from os import path
import pprint

def main():

    service = get_classroom_service()
    courses = service.courses().list(pageSize=2).execute()
    
    downd_files=list()

    for course in courses['courses']:

        course_name = course['name']
        course_id = course['id']

        if not (path.exists(course_name)):
            # Replace invalid characters.
            course_name = (course_name
                .replace("\\", "-")
                .replace("/", "-")
                .replace(":", "-")
                .replace("*", "-")
                .replace("?", "-")
                .replace("\"", "-")
                .replace("<", "-")
                .replace(">", "-")
                .replace("|", "-"))
            
            os.mkdir('./' + course_name)

            # I don't know what this is for.
            os.mkdir('./' + course_name + "/cours")
            os.mkdir('./' + course_name + "/td")
        else:
            print("{} already exists".format(course_name))

        anoncs = service.courses().announcements().list(
            courseId=course_id).execute()
        work = service.courses().courseWork().list(
            courseId=course_id).execute()

        downd_files = downd_files + download_announce_files(anoncs, course_name)
        downd_files = downd_files + download_works_files(work, course_name)
    pprint.pprint(downd_files)

def get_classroom_service():

    SCOPES = [
        'https://www.googleapis.com/auth/classroom.courses.readonly',
        'https://www.googleapis.com/auth/classroom.announcements.readonly',
        'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly'
    ]
    # Shows basic usage of the Classroom API.
    # Prints the names of the first 10 courses the user has access to.
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials-classroom.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds)
    return service


def download_file(file_id, file_name, course_name):

    SCOPES = ['https://www.googleapis.com/auth/drive']
    # Shows basic usage of the Drive v3 API.
    # Prints the names and ids of the first 10 files the user has access to.
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickledrive'):
        with open('token.pickledrive', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials-drive.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickledrive', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    request = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    

    while done is False:
        try:
            status, done = downloader.next_chunk()
            print("Download %d%%" % int(status.progress() * 100))
        except:
            print("Error downloading, ignoring")
            break

    fh.seek(0)

    with open(os.path.join('./', course_name, file_name), 'wb') as f:
        f.write(fh.read())
        f.close()



def download_announce_files(announcements, course_name):
    announce_list = announcements.keys()
    downloaded = list()
    if (len(announce_list) != 0):
        present_files = getListOfFiles(os.path.join('./', course_name))

        for announcement in announcements['announcements']:
            try:  # If this announcements contain a file then do this
                for val in announcement['materials']:
                    file_id = val['driveFile']['driveFile']['id']
                    file_name = val['driveFile']['driveFile']['title']
                    extension = (
                        os.path.splitext(file_name)
                    )[1]  # The extension exists in second elemnts of returned tuple
                    path_str = os.path.join('./', course_name, file_name)

                    if ((valid(extension[1:])) and (file_name not in present_files)) :
                        print("Downloading ", file_name)
                        download_file(file_id, file_name, course_name)
                        downloaded.append("Announcement: " + course_name + ': ' + file_name)                        
                    else:
                        print(file_name, "already exists")
            except KeyError as e:
                continue
    return downloaded

def download_works_files(works, course_name):
    works_list = works.keys()
    downloaded = list()
    if (len(works_list) != 0):
        present_files = getListOfFiles(os.path.join('./', course_name))

        for work in works['courseWork']:
            try:  # If this announcements contain a file then do this
                for val in work['materials']:
                    file_id = val['driveFile']['driveFile']['id']
                    file_name = val['driveFile']['driveFile']['title']

                    if (file_name[0:10] == "[Template]"):
                        file_altern_link = val['driveFile']['driveFile']['alternateLink']

                        file_id = file_altern_link[file_altern_link.find('=')+1:]
                    extension = (
                        os.path.splitext(file_name)
                    )[1]  # The extension exists in second elemnts of returned tuple
                    path_str = os.path.join('./', course_name, file_name)
                    if ((valid(extension[1:])) and (file_name not in present_files)) :
                        print("Downloading ", file_name)
                        download_file(file_id, file_name, course_name)
                        downloaded.append("Devoir: " + course_name + ': ' + file_name)                        
                    else:
                        print(file_name, "already exists")
            except KeyError as e:
                continue
    return downloaded


def valid(ch):
    return ch in [
        'pdf', 'docx', 'pptx', 'png', 'jpg', 'jpeg', 'jfif', 'html', 'css', 'js', 'py', 'java',
        'class', 'txt', 'md', 'r', 'm', 'sql', 'doc', 'mp3', 'mp4', 'rar', 'zip', 'exe',
        'webp', 'webm', 'mov', 'ogg', 'mkv'
    ]


def getListOfFiles(dirName):
    # Create a list of file and sub directories 
    # Names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return [ch[ch.rfind('/')+1:] for ch in allFiles]

if __name__ == '__main__':
    main()
