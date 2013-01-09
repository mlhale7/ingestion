#!/usr/bin/env python
#
# Usage: python poll_images.py <profiles-glob> <enrichment-service-URI.

import pprint
pp = pprint.PrettyPrinter(indent=4)

import sys, os, glob

# Field name to search for the thumbnail URL.
URL_FIELD_NAME = "preview_source_url"

# Field name used for storing the path to the local filename.
URL_FILE_PATH = "preview_file_path"

# Root directory used for storing images
MAIN_PICTURE_DIRECTORY = "/tmp/main_pic_dir"

def generate_file_path(id, file_number, file_extension):
    """
    Function generates and returns the file path based in provided params.

    The file path is generated using the following algorithm:

        -   convert all not allowed characters from the document id to "_"
        -   to the above string add number and extension getting FILE_NAME
        -   calculate md5 from original id
        -   convert to uppercase
        -   insert "/" between each to characters of this hash getting CALCULATED_PATH
        -   join the MAIN_PATH, CALCULATED_PATH and FILE_NAME
    
    Params:
        id             - document id from couchdb  
        file_number    - the number of the file added just before the extension
        file_extension - extension of the file

    Example:
        Function call:
            generate_file_path('clemsontest--hcc001-hcc016', 1, "jpg")

        Generated values for the algorithm steps:

        CLEARED_ID: clemsontest__hcc001_hcc016
        FILE_NAME:  clemsontest__hcc001_hcc016_1.jpg
        HASHED_ID:  8E393B3B5DA0E0B3A7AEBFB91FE1278A
        PATH:       8E/39/3B/3B/5D/A0/E0/B3/A7/AE/BF/B9/1F/E1/27/8A/
        FULL_NAME:  /tmp/szymon/main_pic_dir/8E/39/3B/3B/5D/A0/E0/B3/A7/AE/BF/B9/1F/E1/27/8A/clemsontest__hcc001_hcc016_1.jpg
    """
    import re
    import hashlib
    import os

    cleared_id = re.sub(r'[-]', '_', id)
    print "Cleared id: " + cleared_id
    
    fname = "%s_%s.%s" % (cleared_id, file_number, file_extension)
    print "File name:  " + fname
    
    md5sum = hashlib.md5(id).hexdigest().upper()
    print "Hashed id:  " + md5sum
    
    path = re.sub("(.{2})", "\\1" + os.sep, md5sum, re.DOTALL)
    print "PATH:       " + path
    
    full_fname = os.path.join(MAIN_PICTURE_DIRECTORY, path, fname)

    return full_fname

def download_image(url, id, file_number):
    """
    Function downloads the thumbnail from the given url and storing it somewhere.

    Current implementation stores the file on disk, other imlementations could 
    be made in the future.

    Params:
        url         - the url of the file for downloading
        id          - document id, used for generating the file name
        file_number - number of the file for this document
    """

    # TODO test it

    def get_file_extension(url):
        return "jpg" #TODO implement

    import urllib
    conn = urllib.urlopen(url)
    if not conn.getcode() % 100 == 2:
        raise Exception("Got % from url: [%s] for document: [%s]" % (conn.getcode(), url, id))
    fname = generate_file_path(id, file_number, file_extension)
    local_file = open(fname, 'w')
    local_file.write(conn.read())
    conn.close()
    local_file.close()

def parse_documents(documents):
    """
    Function converts provided json with documents to a list of dictionariers.
    """
    from StringIO import StringIO
    io = StringIO(documents)
    return json.load(io)

def process_document(document):
    """
    Function processes document:
        - gets the image url
        - downloads the thumbnail
        - uppdates the document
    """
    logging.info("Processing document id = " + document["id"])
    #TODO implement
    #TODO get image url
    #TODO download thumbnail to file
    #TODO update document

from amara.thirdparty import json, httplib2
from amara.lib.iri import join
import logging
import logging.handlers
import logging.config

SCRIPT_NAME = "thumbnails downloader"

def configure_logger():
    """
    Function configured logging.
    Currently this is a very simple imeplemtation,
    it just reads the configuration from a file.
    """
    logging.config.fileConfig("thumbs.logger.config")

def process_config():
    """
    Function reads and uses configurations from the config file.
    """
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.read('dpla-thumbs.ini')
    res = {}
    # the names of config settings expected to be in the config file
    names = ['AKARA_SERVER', 'GET_DOCUMENTS_URL', 'GET_DOCUMENTS_LIMIT', \
            ]
    for name in names:
        res[name] = config.get('thumbs', name)
    return res

def get_documents():
    """
    Downloads a set of documents from couchdb.
    """
    logging.info('Getting documents from akara.')
    h = httplib2.Http()
    h.force_exception_as_status_code = True
    url = join(conf['AKARA_SERVER'], conf['GET_DOCUMENTS_URL'] ) + "?limit=%s" % conf['GET_DOCUMENTS_LIMIT']
    logging.debug('Using akara url: ' + url)
    resp, content = h.request(url, 'GET')
    if str(resp.status).startswith('2'):
        return content
    else:
        logging.error("Couldn't get documents using: " + url)
        exit(1)

def download_thumbs():
    """
    The main function.
        Function downloads documents from couchdb.
        Downloads images.
        Updates the documents.
    """
    # Get documents from couchdb
    documents = get_documents()

    # Convert couchdb reply to json.
    documents = parse_documents(documents)
    logging.info("Got %d documents from akara." % len(documents["rows"]))

    for doc in documents["rows"]:
        #pp.pprint(doc) # RM
        process_document(doc)

if __name__ == '__main__':
    #TODO add option for the config file name
    #TODO add checking if the log directory exists

    conf = process_config()
    configure_logger()
    logging.info("Script started.")

    download_thumbs()
