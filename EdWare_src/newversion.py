#!/usr/bin/env python

import sys
import os
import os.path
import shutil


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print "Error -- the new version must be specified on the command line"
        sys.exit(1)

    newVersion = sys.argv[1]
    print "Creating version", newVersion
    newProgram = "edware_" + newVersion
    newInstaller = "edware-installer_" + newVersion
    
    # create the directory
    dirName = os.path.join("..", newProgram)
    os.mkdir(dirName)
    instName = os.path.join('..', newInstaller)
    #os.mkdir(instName)
    
    # copy everything over
    shutil.copy('edware.py', dirName)
    shutil.copy('edware.ico', dirName)
    shutil.copy('edware.icns', dirName)
    shutil.copy('tass.py', dirName)
    shutil.copy('Click.wav', dirName)

    shutil.copytree("gui", os.path.join(dirName, "gui"), ignore=shutil.ignore_patterns('*.pyc', 'old_brics', '#*', '~*'))
    shutil.copytree("docs", os.path.join(dirName, "docs"))
    shutil.copytree('My Programs', os.path.join(dirName, 'My Programs'), ignore=shutil.ignore_patterns('*.pyc'))
    
    shutil.copytree("installer", instName)
    
    # TODO -- fix up the version name
    print "Fix up gui/about.py"
    print "Fix up installer versions"
