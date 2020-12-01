# Drupal 8 Core Updater
This project is a command line utility that allows for easily upgrading or downgrading to various versions of Drupal 8.

To use, `cd` into this project directory and run `./updater.py` to see a list of all available options.

## Options
`-h`, `--help` - Show help screen.
`-d`, `--download` - Download version of Drupal from Drupal.org. If no version is specified the updater will download the most recent version available.
`-f LOCAL_PATH`, `--file=LOCAL_PATH` - Install version from specified local package.
`--replace` - Replace all files with new installation files. **Warning** This option will replace any custom or contributed modules, themes, profiles, .htaccess files, and any user uploaded files. Use with caution.
`-l`, `--list` - List all available versions of Drupal 8 or specify a number to limit to most recent N.
`-i INSTALL_LOCATION`, `--install=INSTALL_LOCATION` - Specify directory location to install Drupal into.

## MIT License

Copyright 2020 by Justin Sitter

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
