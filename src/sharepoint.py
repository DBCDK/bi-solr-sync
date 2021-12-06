import json
from datetime import *
import os

import requests


class SharepointConnector:

    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires = None

    def __check_token(self):
        url = 'https://login.microsoftonline.com/%(tenant_id)s.onmicrosoft.com/oauth2/v2.0/token' % {
            'tenant_id': self.tenant_id
        }
        if self.token is None:
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://graph.microsoft.com/.default',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, data=data, headers=headers)

            if response.status_code != 200:
                raise Exception(
                    'Got status code %s from %s with message %s' % (response.status_code, url, response.text))

            received_token = response.json()

            self.token = received_token['access_token']
            self.token_expires = datetime.now() + timedelta(minutes=received_token['expires_in'])

    def upload_delta(self, drive_id, file_name):
        self.__check_token()
        url = 'https://graph.microsoft.com/v1.0/drives/%(drive_id)s/items/root:/%(file_name)s:/content' % \
              {
                  'drive_id': drive_id,
                  'file_name': file_name
              }

        headers = {
            "Authorization": "Bearer " + self.token,
            'Content-type': 'multipart/form-data'
        }

        file_size = os.path.getsize(file_name)
        if file_size > 4 * 1024 * 1024:
            raise Exception('The file %s is too big at be uploaded as delta', file_name)


        with open(file_name, 'rb') as json_file:
            json_content = json.load(json_file)

        response = requests.put(url, data=json.dumps(json_content), headers=headers)

        if response.status_code != 201:
            raise Exception('Got unexpected status code: %s with message %s' % (response.status_code, response.text))

    # This function doesn't actually work (yet)
    def start_upload(self, drive_id, file_name, json_content):
        self.__check_token()
        url = 'https://graph.microsoft.com/v1.0/drives/%(drive_id)s/items/root/createUploadSession' % \
              {'drive_id': drive_id}
        print(url)
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-type": "text/plain"
        }

        data = {
            "item": {
                "@odata.type": "microsoft.graph.driveItemUploadableProperties",
                "@microsoft.graph.conflictBehavior": "replace",
                "name": file_name
            }
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code != 200:
            raise Exception(
                'Got status code %s from %s with message %s' % (response.status_code, url, response.text))

        j = response.json()
        print(j)
        upload_url = j['uploadUrl']
        print('upload_url', upload_url)
        self.upload(upload_url, json_content)

    # This function doesn't actually work (yet)
    def upload(self, upload_url, json_content):
        data = json.dumps(json_content)
        data_length = len(data)
        headers = {
            'Content-Length': data_length,
            'Content-Range': '0-%s/%s' % (data_length - 1, data_length)
        }

        response = requests.put(upload_url, data=data, headers=headers)
        print(response)
        if response.status_code != 202:
            raise Exception(
                'Got status code %s with message %s' % (response.status_code, response.text))
