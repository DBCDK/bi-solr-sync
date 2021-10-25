#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys

import argcomplete
import requests

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser(
        description='This script extracts documents from solr and formats them in a way the new DWH/BI solution understands.')
    parser.add_argument('url', help='Full solr ur, must include collection and /select.')
    parser.add_argument('--output',
                        help='Name of output file (should end with .json). If not supplied output will be done to the console instead.')
    parser.add_argument('--since',
                        help='If set the query will only find documents since the given date. Must be formatted in a way Solr understands, e.g. \'2021-10-11T07:00:00Z\'.',
                        )
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def generate_query(since=None):
    q = '(marc.001b:870970 OR marc.001b:870971)'

    if since is not None:
        q += ' AND marc.001d:[%s TO NOW]' % since

    return q


def get_count(base_url, query):
    params = {
        "q": query,
        "rows": 0,
        "wt": json
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise Exception('Error from solr: %s' % response.text)

    return response.json()['response']['numFound']


def get_docs(base_url, query, extra_fields=None):
    fields = ["marc.001a001b"]

    if extra_fields is not None:
        fields = fields + extra_fields

    params = {
        'q': query,
        'wt': 'json',
        'fl': fields,
        'rows': 99999999
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception('Error from solr: %s' % response.text)

    return response.json()['response']['docs']


def get_fields():
    with open('fields.txt', 'r') as key_file:
        data = key_file.read()

    keys = data.split('\n')
    # Remove empty string
    keys = [x for x in keys if x]

    return keys


def get_solr_url(raw_url):
    if '/select' not in raw_url:
        raise Exception(
            'Solr url has wrong format. Url must contain \'/select\', e.g. http://rawrepo.solr.dbc.dk:8983/solr/basis-collection/select\?q\=\*:\*')

    # Strip the query args from the url
    head, sep, tail = raw_url.partition('/select')

    return head + sep


if __name__ == "__main__":
    try:
        args = parse_args()
        url = args.url
        output_filename = args.output
        since = args.since

        solr_url = get_solr_url(url)
        query = generate_query(since)
        fields = get_fields()

        logging.info("Getting document count ...")
        count = get_count(solr_url, query)

        logging.info("Found %s documents" % count)

        logging.info("Starting solr extraction ...")
        docs = get_docs(solr_url, query, extra_fields=fields)
        logging.info("Solr extraction done")

        if output_filename is not None:
            logging.info("Writing result to file ...")
            with open(output_filename, 'w') as output:
                json.dump(docs, output)
        else:
            logging.info("Writing result to console ...")
            print(json.dumps(docs))
        logging.info("Job done!")
    except Exception as e:
        print("Unexpected exception: {}"
              .format(e), file=sys.stderr)
        sys.exit(1)
    sys.exit(os.EX_OK)
