#! /usr/bin/env python3

from optparse import OptionParser
import os
import os.path as path
import shutil
import sys
import tarfile
import urllib.request
import zipfile

drupal_server_address = 'https://updates.drupal.org/release-history/drupal/8.x'
home_directory = os.path.dirname(os.path.realpath(__file__))
temp_dir = './.tempdir'
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

if __name__ == "__main__":
    usage = "usage: %prog [options] drupal_installation_location"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--download",
                        help="Download version from Drupal.org",
                        action="store_true",
                        dest="download")

    parser.add_option("-l", "--local",
                        help="Use local package",
                        dest="local_path")

    parser.add_option("-r", "--replace",
                        help="Replace existing files",
                        destination="replace")
    
    (options, args) = parser.parse_args()
    home_directory = path.dirname(path.realpath(__file__))
