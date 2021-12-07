# bi-solr-sync

## Getting started
The script requires python3

Activate venv:
```
source bin/activate
```

Run the script
```
./main.py --help                                                                                                                                                                                                                                                                   ✔  bi-solr-sync   10:47:03  
usage: main.py [-h] [--output OUTPUT] [--since SINCE] [--upload] url

This script extracts documents from solr and formats them in a way the new DWH/BI solution understands.

positional arguments:
  url              Full solr ur, must include collection and /select.

optional arguments:
  -h, --help       show this help message and exit
  --output OUTPUT  Name of output file (should end with .json). If not supplied output will be done to the console instead.
  --since SINCE    If set the query will only find documents since the given date. Must be formatted in a way Solr understands, e.g. '2021-10-11T07:00:00Z'.
  --upload         If set the file is uploaded to sharepoint
```
Note that if --upload is set the following environment variables must be set as well:
```
SHAREPOINT_TENANT
SHAREPOINT_CLIENT_ID
SHAREPOINT_CLIENT_SECRET
SHAREPOINT_DRIVE_ID
```

Example without upload:
```
./main.py --since 2021-10-01T07:00:00Z --output data.json http://solr.dbc.dk:8983/solr/collection/select\?q\=\*:\*
```
Example with upload:
```
export SHAREPOINT_TENANT=...
export SHAREPOINT_CLIENT_ID=...
export SHAREPOINT_CLIENT_SECRET=...
export SHAREPOINT_DRIVE_ID=...

./main.py --since 2021-10-01T07:00:00Z --output data.json --upload http://solr.dbc.dk:8983/solr/collection/select\?q\=\*:\*
```
