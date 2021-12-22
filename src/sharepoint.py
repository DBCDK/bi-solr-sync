import logging
import os
from datetime import *

import requests


class SharepointConnector:

    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires = None
        self.proxy = None
        if os.environ.get('PROXY_HOSTNAME') is not None:
            proxy_hostname = os.environ.get('PROXY_HOSTNAME')
            proxy_port = os.environ.get('PROXY_PORT')
            proxy_username = os.environ.get('PROXY_USERNAME')
            proxy_password = os.environ.get('PROXY_PASSWORD')

            if proxy_port is None:
                proxy_port = '1080'
            if proxy_username is None or proxy_password is None:
                raise Exception('PROXY_HOSTNAME is set so using socks proxy, but username or password is missing')

            proxy_url = 'socks5://{}:{}@{}:{}'.format(proxy_username,
                                                      proxy_password,
                                                      proxy_hostname,
                                                      proxy_port)

            self.proxy = {'http': proxy_url,
                          'https': proxy_url}
        logging.info('Sharepoint connector initialized. Using proxy: %s' % (self.proxy is not None))

    def upload(self, drive_id, file_name, folder_name=None):
        upload_url = self.__start_upload(drive_id, file_name, folder_name=folder_name)
        self.__upload_segments(upload_url, file_name)

    def __check_token(self):
        url = 'https://login.microsoftonline.com/%(tenant_id)s.onmicrosoft.com/oauth2/v2.0/token' % {
            'tenant_id': self.tenant_id
        }
        # TODO also check if token is expired
        if self.token is None:
            logging.info('Getting new token')
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://graph.microsoft.com/.default',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, data=data, headers=headers, proxies=self.proxy)

            if response.status_code != 200:
                raise Exception(
                    'Got status code %s from %s with message %s' % (response.status_code, url, response.text))

            received_token = response.json()

            self.token = received_token['access_token']
            self.token_expires = datetime.now() + timedelta(minutes=received_token['expires_in'])

    def __start_upload(self, drive_id, file_name, folder_name=None):
        self.__check_token()

        if folder_name is None:
            url = 'https://graph.microsoft.com/v1.0/drives/%(drive_id)s/items/root:/%(file_name)s:/createUploadSession' % \
                  {
                      'drive_id': drive_id,
                      'file_name': file_name
                  }
            logging.info('Uploading %s to sharepoint' % file_name)
        else:
            url = 'https://graph.microsoft.com/v1.0/drives/%(drive_id)s/items/root:/%(folder_name)s/%(file_name)s:/createUploadSession' % \
                  {
                      'drive_id': drive_id,
                      'folder_name': folder_name,
                      'file_name': file_name
                  }
            logging.info('Uploading %s in folder %s to sharepoint' % (file_name, folder_name))

        headers = {
            'Authorization': 'Bearer ' + self.token
        }

        response = requests.post(url, headers=headers)

        if response.status_code != 200:
            raise Exception(
                'Got status code %s from %s with message %s' % (response.status_code, url, response.text))

        j = response.json()
        logging.info("Using upload url %s" % j['uploadUrl'])

        return j['uploadUrl']

    def __upload_segments(self, upload_url, file_name):
        self.__check_token()

        # From https://docs.microsoft.com/en-us/graph/api/driveitem-createuploadsession?view=graph-rest-1.0
        # To upload the file, or a portion of the file, your app makes a PUT request to the uploadUrl value received in
        # the createUploadSession response. You can upload the entire file, or split the file into multiple byte ranges,
        # as long as the maximum bytes in any given request is less than 60 MiB.
        #
        # The fragments of the file must be uploaded sequentially in order. Uploading fragments out of order will result
        # in an error.
        #
        # Note: If your app splits a file into multiple byte ranges, the size of each byte range MUST be a multiple of
        # 320 KiB (327,680 bytes). Using a fragment size that does not divide evenly by 320 KiB will result in errors
        # committing some files.
        segment_size = 327680 * 100

        file_size = os.path.getsize(file_name)
        logging.info('File size: %s' % file_size)
        with open(file_name, 'rb') as file:
            data = file.read()

        position = 0

        while position < file_size:
            start_byte = position
            end_byte = position + segment_size
            try:
                self.__upload_segment(upload_url, data[start_byte:end_byte], start_byte, file_size)
                position += segment_size
            except Exception as err:
                logging.error('Got exception: %s' % err)
                logging.info('It is most likely Connection reset by peer, so lets just try once more')
                self.__upload_segment(upload_url, data[start_byte:end_byte], start_byte, file_size)

    def __upload_segment(self, upload_url, data_segment, offset, total_size):
        self.__check_token()

        segment_size = len(data_segment)
        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Content-Length': '%s' % segment_size,
            'Content-Range': 'bytes %s-%s/%s' % (offset, offset + segment_size - 1, total_size)
        }

        logging.info('Content-Length: %s - Uploading bytes %s-%s/%s' % (
            segment_size, offset, offset + segment_size - 1, total_size))

        response = requests.put(upload_url, data=data_segment, headers=headers)

        # While uploading the segments 202 is returned. But the status code of the last segment can be both 200 and 201
        if response.status_code not in [200, 201, 202]:
            raise Exception(
                'Got status code %s with message %s' % (response.status_code, response.text))
