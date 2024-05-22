#!/bin/bash
# Apple Developer variables
APPLE_ID=$(op read "op://Private/z4sp6gvcgzeejgvf6mufvqwrme/username")
APP_PASSWORD=$(op read "op://Private/z4sp6gvcgzeejgvf6mufvqwrme/App Password/App Password")
TEAM_ID=$(op read "op://Personal/z4sp6gvcgzeejgvf6mufvqwrme/Developer/Team ID")


# if not exist ./test, create it
if [ ! -d "./test" ]; then
  mkdir ./test
fi
trash ./build ./dist
trash ./test/AutoArchive.app
trash ./dist/AutoArchive.zip

source ./venv/bin/activate

python3 setup.py py2app

# codesign
CODESIGN_VARS="--deep --force --verify --verbose --timestamp --options runtime"
# find .so under ./dist/AutoArchive.app/
find ./dist/AutoArchive.app/ -name "*.so" -exec codesign $CODESIGN_VARS -s "$TEAM_ID" {} \;
codesign $CODESIGN_VARS -s "$TEAM_ID" ./dist/AutoArchive.app

/usr/bin/ditto -c -k --keepParent ./dist/AutoArchive.app ./dist/AutoArchive.zip
cp -R ./dist/AutoArchive.app ./test/AutoArchive.app

# notarization
read -p "Press enter to submit for Notarization"

xcrun notarytool submit --apple-id $APPLE_ID --password $APP_PASSWORD --team-id $TEAM_ID --wait ./dist/AutoArchive.zip

read -p "Press enter to Staple"

xcrun stapler staple ./dist/AutoArchive.app
spctl -vvv --assess --type exec ./dist/AutoArchive.app

trash ./dist/AutoArchive.zip
/usr/bin/ditto -c -k --keepParent ./dist/AutoArchive.app ./dist/AutoArchive.zip
