#!/bin/bash

# functions
trash() { osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$1")\"" > /dev/null; }

# if not exist ./test, create it
if [ ! -d "./test" ]; then
  mkdir ./test
fi
trash ./build ./dist
trash ./test/AutoArchive.app
trash ./dist/AutoArchive.zip

source ./venv/bin/activate

python3 setup.py py2app
cp -R ./dist/AutoArchive.app ./test/AutoArchive.app
