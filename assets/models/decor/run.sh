#!/bin/bash
# usage: ND_ONLY=Hall,Gate ./run.sh   (quick build of single parts)
cd /c/Dev/4M-tycoon/assets/models/decor
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python build_NinjaDojo.py -- C:/Dev/4M-tycoon/assets/models/decor/out/NinjaDojo 2>&1 | grep -E "TALLY|FIT|EXPORTED|WARN|Error|error|Traceback|File |TRIS|line [0-9]+"
