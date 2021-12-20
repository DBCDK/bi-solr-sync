# Some info about how to use Microsoft Graph API for uploading files to sharepoint

## Prerequisites

Before trying to upload files to the Microsoft Graph API you need the following attributes:
```
${CLIENT_ID}
${CLIENT_SECRET}
${TENANT_ID}
```
These values must be supplied by you Microsoft administrator.

When a new app is created in Sharepoint three values will be returned:
- Client it
- Value
- Secret

`${CLIENT_ID}` is client id but `${CLIENT_SECRET}` is **value** (not secret).

If you intend to upload to the main site then the tenant id is of the main site. However, if you want to upload to e.g. a Team page then you need to find the tenant id of the team. That value can either be supplied by your Microsoft administrator or found using this request:
```
https://<tenant>.sharepoint.com/sites/<site-url>/_api/site/id
```
Note that the request requires a bearer token for authentication. 

`<tenant>` here is not the same tenant id. For this request it is the "root url" of the company's sharepoint site, e.g. `company.sharepoint.com`.

`<site-url>` is the name of the team, e.g. `my-awesome-team` or `DEVELOPMENT`

So a full url could look something like `https://company.sharepoint.com/sites/my-awesome-team/_api/site/id`.

## Generating a bearer token

First generate a bearer token with this request:

```
curl -X POST 'https://login.microsoftonline.com/dbc4.onmicrosoft.com/oauth2/v2.0/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'scope=https://graph.microsoft.com/.default' \
--data-urlencode 'client_Id=${CLIENT_ID}' \
--data-urlencode 'client_secret=${CLIENT_SECRET}'
```

If successful you will get a reply which looks something like this:
```
{
    "token_type": "Bearer",
    "expires_in": 3599,
    "ext_expires_in": 3599,
    "access_token": <A very long sting>
}
```

The value of `expires_in` means the token is value for 1 hour. The value of `access_token` is the `${BEARER_TOKEN}` value which you must use for all subsequent requests.


### A note about grant_type
When getting the token the first time the value of grant_type should be `client_credentials`. But when refreshing the token the value `something_else` should be used.

## Getting drive id

Before uploading a file you have to know the drive id

```
curl 'https://graph.microsoft.com/v1.0/sites/${TENANT_ID}/drives' \
--header 'Authorization: Bearer ${BEARER_TOKEN}'
```

The reply will look something like:

```
{
    "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#drives",
    "value": [
        {
            "createdDateTime": "2021-09-18T23:45:36Z",
            "description": "",
            "id": <drive_id>,
            "lastModifiedDateTime": "2021-12-10T12:51:16Z",
            "name": "Documents",
            "webUrl": "https://<tenant>.sharepoint.com/teams/<site-url>/My%20documents",
            "driveType": "documentLibrary",
            "createdBy": {
                "user": {
                    "displayName": "Systemkonto"
                }
            },
            "lastModifiedBy": {
                "user": {
                    "displayName": "Systemkonto"
                }
            },
            "owner": {
                "group": {
                    "email": "<site-url>@<tenant>.onmicrosoft.com",
                    "id": <group id>,
                    "displayName": "<site-url>-owners"
                }
            },
            "quota": {
                "deleted": 33752094,
                "remaining": 27486024349804,
                "state": "normal",
                "total": 27487790694400,
                "used": 1732592502
            }
        }
    ]
}
```

You want the `<drive_id>` as `${DRIVE_ID}` value for the next requests

# Uploading files

Files smaller than 4 MB are uploaded with a simple PUT request, while large files has to be uploaded using a session.

## Files smaller than 4 MB

Smaller files are uploaded with this request:

```
curl -X PUT 'https://graph.microsoft.com/v1.0/drives/${DRIVE_ID}/items/root:/<folder name>/<file name>:/content' \
--header 'Content-Type: multipart/form-data' \
--header 'Authorization: Bearer ${BEARER_TOKEN} \
--data-binary '@/path/to/file'
```

If you are uploading to the root folder of the drive the url is 
```
https://graph.microsoft.com/v1.0/drives/${DRIVE_ID}/items/root:/<file name>:/content
```
Note that the colon after root and file name are very important

## Files bigger than 4 MB

...
