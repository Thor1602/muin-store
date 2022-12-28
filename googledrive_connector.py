from __future__ import print_function

import os.path
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
import mimetypes



def google_drive_connect(func):
    def wrapper(*args, **kwargs):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ['https://www.googleapis.com/auth/drive']

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'gitignore/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        try:
            wrapper.service = build('drive', 'v3', credentials=creds)
            return func(*args, **kwargs)
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')

    return wrapper


@google_drive_connect
def list_all_files(return_name=True, return_id=True, parent=''):
    """
    Returns the names and ids of all files the user has access to.
    """
    query=''
    if parent != '':
        file_id = search_file_by_name(parent)
        query = f"parents = '{file_id}'"
    files = []
    page_token = None
    while True:
        # pylint: disable=maybe-no-member
        response = list_all_files.service.files().list(q=query,
                                        spaces='drive',
                                        fields='nextPageToken, '
                                               'files(id, name, webViewLink, webContentLink)',
                                        pageToken=page_token).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    if return_name and return_id:
        return files
    elif return_name:
        return [x['name'] for x in files]
    elif return_id:
        return [x['id'] for x in files]
    else:
        return []

@google_drive_connect
def upload_image(file):
    """Insert new file.
    Returns : Id's of the file uploaded
    """

    file_metadata = {
        'name': file.filename,
        'parents': ['1aIwPpPQdBoqdOQO-IIhwXOIrEi_kyqSs']
    }
    m_type = mimetypes.guess_type(file.filename)
    media = MediaIoBaseUpload(file,
                            mimetype=m_type[0],
                            resumable=True)
    upload_image.service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()

@google_drive_connect
def upload_invoice(file):
    """Insert new file.
    Returns : Id's of the file uploaded
    """
    # if parent == 'supplier':
    #     invoices_folder_id = "1-0pXc_fS8B6y50rarljtG9InVEWFSnq3"
    # elif parent == 'customer':
    #     invoices_folder_id = "1k9Qt-HGc4rYgainpOp2gx5f2weSGezwZ"
    # else:
    #     invoices_folder_id = "1xD0ulrlmgMu8SJCIA-MBOXkErzBYlmz0"
    file_metadata = {
        'name': file.filename,
        'parents': ['1-0pXc_fS8B6y50rarljtG9InVEWFSnq3']
    }
    m_type = mimetypes.guess_type(file.filename)
    media = MediaIoBaseUpload(file,
                              mimetype=m_type[0],
                              resumable=True)
    upload_invoice.service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()


@google_drive_connect
def download_file(file_id):
    """Downloads a file
    Args:
        file_id: ID of the file to download
    Returns : IO object with location.
    """
    request = download_file.service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(F'Download {int(status.progress() * 100)}.')

    return file




@google_drive_connect
def search_file_by_name(filename):
    """Search file in drive location
    """
    response = search_file_by_name.service.files().list(spaces='drive',
                                                        fields='nextPageToken, files(id, name)').execute()
    file_id = None
    for file in response.get('files', []):
        if file['name'] == filename:
            file_id = file['id']
    return file_id


@google_drive_connect
def search_file_by_id(fileid):
    """Search file in drive location
    """
    response = search_file_by_id.service.files().list(spaces='drive', fields='nextPageToken, files(id, name)').execute()
    file_name = None
    for file in response.get('files', []):
        if file['id'] == fileid:
            file_name = file['name']
    return file_name


@google_drive_connect
def change_name_from_id(file_id, new_filename):
    change_name_from_id.service.files().update(
        fileId=file_id,
        supportsAllDrives='true',
        body={'name': new_filename}
    ).execute()


@google_drive_connect
def change_name(old_name, new_name):
    change_name.service.files().update(
        fileId=search_file_by_name(old_name),
        supportsAllDrives='true',
        body={'name': new_name}
    ).execute()

@google_drive_connect
def delete_file(file_id):
    delete_file.service.files().delete(fileId=file_id).execute()

if __name__ == '__main__':
    print('google drive connector---------------------------------------')
    # upload_file('choco-macaron.jpg','D:\\Users\\Thorben\\OneDrive - University of the People\\PycharmProjects\\bakery\\static\\img\\choco-macaron-2.jpg')
    # download_file('1kkoIXnosma7uGmq9YIMOVWvUYCprM9gW')
