#!/bin/bash

# functions
find_app() {
    # https://stackoverflow.com/a/51806092
    local name_app="$1"
    local path_launchservices="/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
    $path_launchservices -dump | grep -o "/.*${name_app}.app" | grep -v -E "Caches|TimeMachine|Temporary|/Volumes/${name_app}" | uniq
}

trash() { osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$1")\"" > /dev/null; }

# constants
APP_NAME="AutoArchive"
APP_DIRNAME="$APP_NAME.app"

# Hello
echo "$APP_NAME Update Utility"

# Try read source from argument, if not provided, use "./dist/AutoArchive.app"
source=${1:-"./dist/$APP_DIRNAME"}

# Get the absolute path of ./dist/AutoArchive.app
source=$(realpath "$source")
source_bundle_id=$(defaults read "$source/Contents/Info.plist" CFBundleIdentifier)
source_version=$(defaults read "$source/Contents/Info.plist" CFBundleShortVersionString)

# Print source bundle identifier and version
echo "Source: $source"
echo "Source Bundle ID: $source_bundle_id"
echo "Source App Version: $source_version"

echo "Press Enter to continue..."
read

# Find all installations of AutoArchive.app
echo "Finding all $APP_NAME installations..."
apps_path=$(find_app "$APP_NAME")

# Set IFS to newline only
IFS=$'\n'

# Loop through all installations of AutoArchive.app
for target in $apps_path; do
    # Ignore certain paths
    if [[ "$target" == *"/Volumes/.timemachine/"* ]]; then
        echo "Ignoring $target because it is in /Volumes/.timemachine/"
        continue
    fi
    if [[ "$target" == *"/.Trash/"* || "$target" == *"/.Trashes/"* ]]; then
        echo "Ignoring $target because it is in Trash"
        continue
    fi
    if [[ "$target" == "$source" ]]; then
        echo "Ignoring $target because it is the source"
        continue
    fi

    # get bundle id and version
    unset bundle_id version
    bundle_id=$(defaults read "$target/Contents/Info.plist" CFBundleIdentifier)
    version=$(defaults read "$target/Contents/Info.plist" CFBundleShortVersionString)

    if [[ "$bundle_id" != "$source_bundle_id" ]]; then
        echo "Ignoring $target due to Bundle ID mismatch" 
        continue
    fi
    if [[ "$version" == "$source_version" ]]; then
        echo "Ignoring $target because it is the same version"
        continue
    fi

    # Print target bundle identifier and version
    echo "Found target: $target"
    echo "Bundle ID: $bundle_id"
    echo "App Version: $version"

    # Print target path and ask for user confirmation
    read -p "Do you want to replace this app with the new version? [y/n]: " response
    if [[ "$response" != "y" ]]; then
        echo "Skipping replacement for $target"
        continue
    fi

    # Use trash to delete old app safely
    echo "Moving target to trash..."
    trash "$target"

    # Replace target with source
    echo "Copying new version to $target"
    cp -a "$source" "$target"
done
