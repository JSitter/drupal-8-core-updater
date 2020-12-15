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
import math
from optparse import OptionParser
import os
import os.path as path
import shutil
import sys
import tarfile
import time
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

def download_report_hook(count, chunk_size, total_size):
    global start_time
    global progress
    current_time = time.time()
    if count == 0:
        start_time = current_time
        progress = int(chunk_size)
        return
    duration = current_time - start_time
    progress += int(chunk_size)
    speed = int(progress / (1024 * duration))
    if speed > 799:
        speed = speed / 1000
        speed_scale = "MB/s"
    else:
        speed_scale = "KB/s"
    percent = progress * 100 / total_size
    progress_mb = progress / (1024 * 1024)
    percent_scale = int(math.floor(percent)/4)
    vis_downloaded = "=" * percent_scale
    vis_remaining = "." * (25 - percent_scale) + '|'
    CURSOR_UP = '\x1b[1A'
    CLEAR_LINE = '\x1b[2k'

    sys.stdout.write("{}{}\r{}>{}               \n".format(CURSOR_UP, CLEAR_LINE, vis_downloaded, vis_remaining))
    sys.stdout.write("\r{}{} {:.2f}% -- {:.2f}MB out of {:.2f}MB {:.0f}s          ".format(speed, speed_scale, percent, progress_mb, total_size/1000000, duration))
    sys.stdout.flush()

def download_drupal_version(download_url, destination):
    retry = True
    user_affirmative = {"Y", "y"}
    while retry:
        retry = False
        try:
            print("Downloading {}".format(destination.split('/')[-1]))
            req.urlretrieve(download_url, destination, download_report_hook)
        except:
            user_retry = input("Failed to complete download. Retry? [Y/n] ")
            if user_retry in user_affirmative:
                retry = True
            else:
                sys.exit(1)
        else:
            time_completed = time.time() - start_time
            sys.stdout.write("\rDownload Complete in {:.1f} seconds.                                \n".format(time_completed))
            sys.stdout.flush()

def handle_drupal_download(download_url, filename, source_hash=""):
    check_dir(temp_dir)
    user_affirmative = {"Y", "y"}
    destination = "{}/{}".format(temp_dir, filename)
    # Allow user to retry if package fails to download

    if not path.exists(destination):
        download_drupal_version(download_url, destination)
    else:
        print("Using local file.")
    
    retry = True
    while retry:
        retry = False
        f = open(destination, 'rb')
        print("Verifying package authenticity.")
        file_hash = hashlib.md5(f.read()).hexdigest()
        f.close()
        if file_hash != source_hash:
            user_retry_download = input("Warning! Hash Mismatch. Retry download? [Y/n] ")
            remove_file(destination)
            if user_retry_download in user_affirmative:
                download_drupal_version(download_url, destination)
                retry = True
            else:
                sys.exit(1)

def get_xml_urllib(url):
    res = req.urlopen(url)
    xml = res.read()
    return ET.fromstring(xml)

def get_drupal_versions(num_of_versions=None):
    root = get_xml_urllib(drupal_server_address)

    # debug from saved xml data
    # with open('drupalxml.xml', 'wb') as f:
    #     f.write(response.content)
    # root = ET.parse('drupalxml.xml').getroot()
    
    # Parse XML response
    
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
                    user_choice = input("Version {} is insecure. Proceed anyway? [Y/n] ".format(args[0]))
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
        handle_drupal_download(download_url, download_filename, download_hash)
        if options.install:
            destination = options.install
            print("Installing into: {}".format(destination))
        else:
            destination = input("Enter installation location: ")
            print("Installing into: {}".format(destination))
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
