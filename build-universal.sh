#!/bin/bash

# functions
trash() { osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$1")\"" > /dev/null; }

BUILD_DIR=./build/universal
mkdir -p $BUILD_DIR
BUILD_DIR=$(realpath $BUILD_DIR)
BUILD_TMP_DIR=/tmp/autoarchive-build-universal-$(date +%s)
PYTHON=/usr/bin/python3
export PATH=/usr/bin:$PATH

# Hello
echo "AutoArchive Universal Build Utility"

if [ "$(arch)" == "arm64" ]; then
  echo "Running on arm64, switching to x86_64"
  arch -x86_64 $0
  exit
fi
echo "Running on $(arch)"
echo "Build Directory: $BUILD_DIR"

echo "Copy to temporary directory: $BUILD_TMP_DIR"
if [ -d "./build" ]; then
  trash ./build
fi
mkdir $BUILD_TMP_DIR
cp -R ./ $BUILD_TMP_DIR
echo "Move files to $BUILD_DIR"
mkdir -p $BUILD_DIR
mv $BUILD_TMP_DIR/* $BUILD_DIR/
cd $BUILD_DIR
echo "Current Directory: $(pwd)"
echo "Deleting obsolete files..."
# if exist ./dist, ./test ./venv, delete them
if [ -d "./dist" ]; then
  trash ./dist
fi
if [ -d "./test" ]; then
  trash ./test
fi
if [ -d "./venv" ]; then
  trash ./venv
fi

mkdir ./dist
mkdir ./test

echo "Creating virtual environment..."
$PYTHON -m venv ./venv
echo "Installing dependencies..."
source ./venv/bin/activate
pip install -r requirements.txt
deactivate

echo "Running Build Utility..."
./build.sh

echo "Build Utility complete."
echo "Run 'cd ./build/universal' for next steps."
