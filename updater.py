#! /usr/bin/env python3

from optparse import OptionParser
import os
import os.path as path
import shutil
import sys
import tarfile
import urllib.request as req
import zipfile
import xml.etree.ElementTree as ET
import requests
import curses
import hashlib

drupal_server_address = 'https://updates.drupal.org/release-history/drupal/8.x'
home_directory = os.path.dirname(os.path.realpath(__file__))
temp_dir = home_directory + '/.tempdir'
zipped_package_location = None

forbidden_folders = {'sites'}
forbidden_files = {'.htaccess'}

def check_temp_dir():
    if not path.exists(temp_dir):
        os.mkdir(temp_dir)

def remove_directory(source):
    print("Removing {}".format(source))
    shutil.rmtree(source)

def remove_file(source):
    print("Removing {}".format(source))
    os.remove(source)

def replace_item(source, destination):
    if path.isdir(destination):
        remove_directory(destination)
    else:
        remove_file(destination)
    
    shutil.move(source, destination)

def update_file(temp_location, file, destination, replace=False):
    file_destination = "{}/{}".format(destination, file)
    temp_file_location = "{}/{}".format(temp_location, file)

    if not path.exists(file_destination):
        shutil.move(temp_file_location, destination)
    elif replace:
        replace_item(temp_file_location, file_destination)
    else:
        if file in forbidden_folders or file in forbidden_files:
            print("Skipping {}. File already exists.".format(file))
        else:
            try:
                replace_item(temp_file_location, file_destination)
                print("Replaced {}".format(file))
            except:
                print("{} locked".format(file))

def unpack_gz_into(source, destination, replace=False, save_extract=False):
    tar = tarfile.open(source, 'r:gz')
    allfiles = tar.getnames()
    temp_source_dir = "{}/{}".format(temp_dir, allfiles[0])

    if not path.exists(temp_dir):
        os.mkdir(temp_dir)
    
    tarball = tarfile.open(source, 'r:gz')
    tarball.extractall(path=temp_dir)
    files = os.listdir(temp_source_dir)

    for file in files:
        update_file(temp_source_dir, file, destination, replace)

    if not save_extract:
        shutil.rmtree(temp_source_dir)
    print("Done")

def download_drupal_package(download_url, destination, hash=""):
    if not path.exists(destination):
        print("Downloading {}".format(destination.split('/')[-1]))
        req.urlretrieve(download_url, destination)
    else:
        print("Using local file.")
    
    f = open(destination, 'rb')
    print("Verifying package authenticity.")
    file_hash = hashlib.md5(f.read()).hexdigest()
    f.close()
    if file_hash != hash:
        print("Warning! Hash Mismatch")
        remove_file(destination)
    else:
        print("Package authenticity established")

def get_drupal_versions():
    # response = requests.get(drupal_server_address)
    # with open('drupalxml.xml', 'wb') as f:
    #     f.write(response.content)

    # debugging from saved xml data
    root = ET.parse('drupalxml.xml').getroot()
    

    # Parse XML response
    # root = ET.fromstring(response.content)
    release_order = []

    release_dict = {}
    releases = root.findall('releases/release')
    for release in releases:
        release_types = release.findall("terms/term")
        security = None
        for release_type in release_types:
            try:
                release_type = release_type.find('value').text
                if release_type == "Insecure":
                    security = release_type
            except:
                release_type = ""
        
        release_name = release.find("name").text
        release_url = release.find("download_link").text
        release_hash = release.find("mdhash").text
        release_version = release.find("version").text
        release_order.append(release_version)
        cur_release = {"name": release_name, 
                        "type": release_type, 
                        "url": release_url, 
                        "hash": release_hash,
                        "filename": release_url.split("/")[-1],
                        "security": security}

        release_dict[release_version] = cur_release
    release_dict["order"] = release_order
    return release_dict

if __name__ == "__main__":
    usage = "usage: %prog [options] drupal_installation_location"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--download",
                        help="Download version from Drupal.org",
                        action="store_true",
                        dest="download")

    parser.add_option("-f", "--file",
                        help="Use local package",
                        dest="local_path")

    parser.add_option("-r", "--replace",
                        help="Replace existing files",
                        action="store_true",
                        dest="replace")
    
    parser.add_option("-l", "--list",
                        help="List recent versions",
                        action="store_true",
                        dest="list")
    
    (options, args) = parser.parse_args()
    # home_directory = path.dirname(path.realpath(__file__))

    print(options)
    print(args)

    versions = get_drupal_versions()
    print("Most recent version: {}".format(versions['order'][0]))
    drupal_version = versions[versions['order'][0]]

    download_url = drupal_version['url']
    download_filename = drupal_version['filename']
    download_hash = drupal_version['hash']
    download_full_path = "{}/{}".format(temp_dir, download_filename)

    if not path.exists(temp_dir):
        os.mkdir(temp_dir)

    download_drupal_package(download_url, download_full_path, download_hash)