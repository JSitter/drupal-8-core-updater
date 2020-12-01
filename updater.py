#! /usr/bin/env python3

'''
    Drupal 8 CLI Updater
    Copyright 2020 by Justin Sitter

    Permission is hereby granted, free of charge, to any person 
    obtaining a copy of this software and associated documentation 
    files (the "Software"), to deal in the Software without 
    restriction, including without limitation the rights to use, 
    copy, modify, merge, publish, distribute, sublicense, and/or 
    sell copies of the Software, and to permit persons to whom the 
    Software is furnished to do so, subject to the following 
    conditions:

The above copyright notice and this permission notice shall be 
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS 
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN 
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
'''
import hashlib
from optparse import OptionParser
import os
import os.path as path
import requests
import shutil
import sys
import tarfile
import urllib.request as req
import xml.etree.ElementTree as ET

drupal_server_address = 'https://updates.drupal.org/release-history/drupal/8.x'
home_directory = os.path.dirname(os.path.realpath(__file__))
temp_dir = home_directory + '/.tempdir'

forbidden_folders = {'modules', 'profiles', 'sites', 'themes'}
forbidden_files = {'.htaccess'}

def check_dir(directory):
    if not path.exists(directory):
        os.mkdir(directory)

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

    check_dir(temp_dir)
    check_dir(destination)
    
    tarball = tarfile.open(source, 'r:gz')
    tarball.extractall(path=temp_dir)
    files = os.listdir(temp_source_dir)

    for file in files:
        update_file(temp_source_dir, file, destination, replace)

    if not save_extract:
        shutil.rmtree(temp_source_dir)
    print("Done")

def download_drupal_package(download_url, filename, hash=""):
    check_dir(temp_dir)
    
    destination = "{}/{}".format(temp_dir, filename)
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

def get_drupal_versions(num_of_versions=None):
    response = requests.get(drupal_server_address)

    # debug from saved xml data
    # with open('drupalxml.xml', 'wb') as f:
    #     f.write(response.content)
    # root = ET.parse('drupalxml.xml').getroot()
    
    # Parse XML response
    root = ET.fromstring(response.content)
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
    if num_of_versions is not None and num_of_versions < len(release_order):
        release_dict["order"] = release_order[:num_of_versions]
    else:
        release_dict["order"] = release_order
    return release_dict

if __name__ == "__main__":
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--download",
                        help="Download specified version from Drupal.org. If no version is specified most recent version will be chosen",
                        action="store_true",
                        dest="download")

    parser.add_option("-f", "--file",
                        help="Use local installation package. (Must be tar.gz)",
                        dest="local_path")

    parser.add_option("--replace",
                        help="Replace all existing files when installing. **WARNING!** This will replace any custom modules, themes, and file uploads. Use with caution.",
                        action="store_true",
                        dest="replace")
    
    parser.add_option("-l", "--list",
                        help="List available versions of Drupal. Defaults to all versions but add optional argument to limit to most recent N versions.",
                        action="store_true",
                        dest="list")
    
    parser.add_option("-i", "--install",
                        help="Location of local Drupal installation",
                        dest="install")
    
    (options, args) = parser.parse_args()

    if options.list:
        if args:
            num_of_versions = int(args[0])
            versions = get_drupal_versions(num_of_versions)
            print("Showing most recent {} versions".format(num_of_versions))
            for version in versions['order']:
                print(version)
        else:
            versions = get_drupal_versions()
            print("{} available versions".format(len(versions['order'])))

            for version in versions['order']:
                print(version)

    elif options.download:
        versions = get_drupal_versions()
        if args:
            if args[0] not in versions:
                print("Version not available")
                sys.exit(1)
            else:
                if versions[args[0]]['security'] == "Insecure":
                    user_choice = input("Version {} is insecure. Proceed anyway? [Y/n]")
                    if user_choice != 'Y':
                        print("Aborting Installation")
                        sys.exit(1)
                version = versions[args[0]]
        else:
            version = versions[versions["order"][0]]
        print("Downloading {}".format(version["name"]))
        download_url = version['url']
        download_filename = version['filename']
        download_hash = version['hash']
        download_drupal_package(download_url, download_filename, download_hash)
        if options.install:
            destination = options.install
            print("destination: {}".format(destination))
        else:
            destination = input("Enter installation location: ")
            print("destination: {}".format(destination))
        source = "{}/{}".format(temp_dir, download_filename)
        if options.replace:
            unpack_gz_into(source, destination, replace=True)
        else:
            unpack_gz_into(source, destination)

    elif options.local_path:
        if options.install:
            destination = options.install
        else:
            destination = input("Enter installation location: ")
        print("Installing into {}".format(destination))
        if options.replace:
            unpack_gz_into(options.local_path, destination, replace=True)
        else:
            unpack_gz_into(options.local_path, destination)

    else:
        parser.print_help()         
