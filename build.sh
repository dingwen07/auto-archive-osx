#!/bin/bash
/opt/homebrew/bin/trash ./build ./dist
/opt/homebrew/bin/trash ./test/AutoArchive.app

source ./venv/bin/activate

python3 setup.py py2app
cp -R ./dist/AutoArchive.app ./test/AutoArchive.app
