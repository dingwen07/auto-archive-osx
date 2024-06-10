#!/bin/bash

# functions
trash() { osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$1")\"" > /dev/null; }

echo "PyQt Universal 2 Binary Patch Utility"

if [[ "$(sysctl -n machdep.cpu.brand_string)" != *"Apple"* ]]; then
    echo "This script must be run on an Apple Silicon Mac. Nothing to do."
    echo "PyQt Universal 2 Binary Patch Utility complete."
    exit
fi

echo "Current Directory: $(pwd)"

echo "Activating virtual environment..."
source ./venv/bin/activate

SITE_PACKAGE=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
echo "Site Package: $SITE_PACKAGE"

echo "Patching PyQt6..."
# make a backup, preserve permissions
cp -R $SITE_PACKAGE/PyQt6 $SITE_PACKAGE/PyQt6.bak

# reinstall PyQt6 as arm64
arch -arm64 pip install PyQt6 --force-reinstall

# Patch
cd $SITE_PACKAGE
echo "Converting to Universal Binary..."
find ./PyQt6/Qt6 -type f -perm +111 -exec sh -c 'xcrun lipo -create -output "{}" "{}" "$(echo "{}" | sed "s|^./PyQt6/|./PyQt6.bak/|")"' \;
echo "Patching complete."

deactivate

echo "PyQt Universal 2 Binary Patch Utility complete."
