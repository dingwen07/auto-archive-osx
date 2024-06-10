#!/bin/bash

# functions
trash() { osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$1")\"" > /dev/null; }

# Hello
echo "AutoArchive Build Utility"
echo "Running on $(arch)"

# if not exist ./test, create it
if [ ! -d "./test" ]; then
  mkdir ./test
fi

# if exist ./build, ./dist, ./test/AutoArchive.app, delete them
if [ -d "./build" ]; then
  trash ./build
fi
if [ -d "./dist" ]; then
  trash ./dist
fi
if [ -d "./test/AutoArchive.app" ]; then
  trash ./test/AutoArchive.app
fi

source ./venv/bin/activate

python3 setup.py py2app

deactivate

echo "Copying artifact to ./test"
cp -R ./dist/AutoArchive.app ./test/AutoArchive.app

echo "Build Utility complete."
