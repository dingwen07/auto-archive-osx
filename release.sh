#!/bin/bash

# functions
trash() { osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$1")\"" > /dev/null; }

# Apple Developer constants
APPLE_ID=$(op read "op://Private/z4sp6gvcgzeejgvf6mufvqwrme/username")
APP_PASSWORD=$(op read "op://Private/z4sp6gvcgzeejgvf6mufvqwrme/App Password/App Password")
TEAM_ID=$(op read "op://Personal/z4sp6gvcgzeejgvf6mufvqwrme/Developer/Team ID")

# App constants
APP_NAME="AutoArchive"
APP_DIRNAME="$APP_NAME.app"

# Hello
echo "$APP_NAME Release Utility"

source=${1:-"./dist/$APP_DIRNAME"}
source=$(realpath "$source")
source_parent=$(dirname "$source")
bundle_id=$(defaults read "$source/Contents/Info.plist" CFBundleIdentifier)
version=$(defaults read "$source/Contents/Info.plist" CFBundleShortVersionString)

echo "App: $source"
echo "Bundle ID: $bundle_id"
echo "Version: $version"

read -p "Press Enter to continue to codesign"

# codesign
CODESIGN_VARS="--deep --force --verify --verbose --timestamp --options runtime"
echo Codesigning libraries...
find $source/ -name "*.so" -exec codesign $CODESIGN_VARS -s "$TEAM_ID" {} \;
find $source/ -name "*.dylib" -exec codesign $CODESIGN_VARS -s "$TEAM_ID" {} \;
echo Codesigning executables...
find $source/ -type f -perm +111 -exec codesign $CODESIGN_VARS -s "$TEAM_ID" {} \;
codesign $CODESIGN_VARS -s "$TEAM_ID" $source

echo .
echo Codesigning complete:
codesign -dvvv $source

# notarization
/usr/bin/ditto -c -k --keepParent $source $source_parent/AutoArchive.zip

read -p "Press enter to submit for Notarization"

xcrun notarytool submit --apple-id $APPLE_ID --password $APP_PASSWORD --team-id $TEAM_ID --wait $source_parent/AutoArchive.zip

read -p "Press enter to Staple"

xcrun stapler staple $source
spctl -vvv --assess --type exec $source

trash $source_parent/AutoArchive.zip
/usr/bin/ditto -c -k --keepParent $source $source_parent/AutoArchive.zip
mkdir -p $source_parent/AutoArchive
cp -R $source $source_parent/AutoArchive/AutoArchive.app
