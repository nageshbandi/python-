#!/usr/bin/env python

import sys
import getopt
import os, subprocess
import string
import zipfile
import re
import shutil



"""
Defining global variables required to deploy MRNG INT package
"""
# pkgFile = ""
envName = ""
profile = ""
release = ""
database = ""
currDir = os.path.dirname(os.path.realpath(__file__))
releaseDir = ""
RED_COLOR="\x1B[31;40m"
NO_COLOR="\x1B[0m"


"""
Load package paramters to deploy
"""
def usage():
    return "Usage: python deployIntegrationPackage.py -e <envName> -r <releaseFolder> -d <database>"

"""
Build Mrng Intergeration package
"""
def LoadPkgArgs(argv):

    # global pkgFile
    global envName
    global release
    global profile
    global database
    global releaseDir

    try:
        opts, args = getopt.getopt(argv, "he:r:d:", ["env=","rel=","database="])
    except getopt.GetoptError:
        printErrorAndExit( usage() )


    for opt, arg in opts:
        if opt == '-h':
            printErrorAndExit( usage() )
        elif opt in ("-e","--env"):
            envName = arg.lower()
        elif opt in ("-r","--rel"):
            release = arg.strip()
        elif opt in ("-d","--database"):
            database = arg.upper()

    if len(database) == 0:
        printErrorAndExit( usage() )

    profile=envName.translate(None, string.digits)+"Profile_template"

    releaseDir = getReleaseDir()

def getReleaseDir():
    if not os.path.isfile("../config/mrngProfile"):
        printErrorAndExit ("Failed to source {0} to get rootDir. Package deployment exiting.....".format("../config/mrngProfile"))

    command = ['bash', '-c', 'source ../config/mrngProfile && env']
    proc = subprocess.Popen(command, stdout = subprocess.PIPE)
    for line in proc.stdout:
        if line.startswith("MRNG_INTEGRATE="):
            (key, _, value) = line.partition("=")
            print("Pulled from ../config/mrngProfile, MRNG_INTEGRATE={0}".format(value.rstrip()))
            return value.rstrip()

    printErrorAndExit ("MRNG_INTEGRATE value not found in ../config/mrngProfile. Deployment exiting....")


"""
Just deploy already unzipped release to provided environment
"""
def releaseDeploy():
    print ("In releaseDeploy from release folder.........."  )
    if not os.path.exists(releaseDir):
        printErrorAndExit ("Release folder {0} does not exist. Package deployment exiting.....".format(releaseDir))

    changeRuntimeFilePermissions()


"""
Unzip supplied package:
Pick release number and create folder if not exist
unzip the package
set permissions on files required
"""

"""
def unzipPkg():

    if not os.path.exists(releaseDir):
        os.makedirs(releaseDir)

    packageZipFile=currDir+os.path.sep+pkgFile

    print("Checking if file(s) in existing release folder but NOT in package zip file, if not then remove....")
    cleanRemovedFiles(packageZipFile,releaseDir)

    print("Unzipping {0} file to {1}".format(pkgFile,releaseDir))
    zipRef = zipfile.ZipFile(packageZipFile,'r')
    zipRef.extractall(releaseDir)
    zipRef.close()

    changeRuntimeFilePermissions()

    print("{0} package is unzipped successfully ....".format(pkgFile))
"""

def changeRuntimeFilePermissions():

    scriptFolder=releaseDir+os.path.sep+"scripts"
    os.chmod(scriptFolder,0755)
    for path, dirs, files in os.walk(scriptFolder):
        for name in files:
            os.chmod(os.path.join(path,name),0755)

    postinstallFolder=releaseDir+os.path.sep+"postinstall_scripts"
    os.chmod(postinstallFolder,0755)
    for path, dirs, files in os.walk(postinstallFolder):
        for name in files:
            os.chmod(os.path.join(path,name),0755)

    libFolder=releaseDir+os.path.sep+"lib"
    os.chmod(libFolder,0755)
    for path, dirs, files in os.walk(libFolder):
        for name in files:
            os.chmod(os.path.join(path,name),0755)


def cleanRemovedFiles(packageZipFile,releaseDir):

    zipFileList = []
    zf = zipfile.ZipFile(packageZipFile)
    for filename in zf.namelist():
        zipFileList.append(os.path.join(releaseDir,filename))

    for path, dirs, files in os.walk(releaseDir, topdown=True):
        for name in files:
            absFileName=os.path.join(path,name)
            if absFileName not in zipFileList:
                print ("File {0} not found in {1}, removing extra file in release folder:".format(absFileName,packageZipFile))
                os.remove(absFileName)

def passwordSet():

    configDir=os.path.join(releaseDir,"config")
    profileFile=os.path.join(configDir,profile);
    win_host=""
    try:
        hand = open(profileFile)
    except IOError as e:
        print RED_COLOR
        traceback.print_exc(file=sys.stdout)
        print NO_COLOR
        sys.exit(2)
    for line in hand:
        line=line.rstrip()
        if re.search('^WIN_HOST=',line) :
            win_host=line.replace("WIN_HOST","").replace("export","").replace(";","").replace("=","").strip()
            break

    if len(win_host) == 0 :
        printErrorAndExit("WIN_HOST is not defined in {0} file, deployment process is exiting ....".format(profileFile))


    os.chdir(os.path.join(releaseDir,"postinstall_scripts"))
    cmd = "./updateProdPassword.pl -w {0}  -p rdrPassword".format(win_host)
    retCode = os.system(cmd)
    if retCode > 0:
        printErrorAndExit("Deployment process is failed and exiting ........");

    print("Password update process finished successfully .....")

def getDatabaseHostIP():
    configDir=os.path.join(releaseDir,"config")
    print("Reading {0} to get RDR database IP.".format(configDir+"/odbc.ini"))
    with open (configDir+"/odbc.ini",'r') as infile:
         lines = infile.readlines()
         for i in range(0,len(lines)):
              if lines[i].rstrip().startswith( "["+database+"]" ):
                   for t in range(i,len(lines)):
                        if( lines[t].rstrip().startswith( "Servername" ) ):
                             return lines[t].rstrip().split("=")[1].strip()

                   return None

    return None

def createProfile() :

    print ("Creating environment specific environmnet......")
    configDir=os.path.join(releaseDir,"config")
    sourceProfile=os.path.join(configDir,profile)
    targetProfile=os.path.join(configDir,envName+"Profile")

    if not os.path.exists(sourceProfile):
        printErrorAndExit("{0} - Template profile doest not exist.".format(sourceProfile))


    ENV_MARKER = envName.upper()[:1]

    if envName == "prd":
        AUTOSYS_MARKER="P1"
    elif envName == "dr":
        AUTOSYS_MARKER="R1"
    elif envName == "dr77":
        AUTOSYS_MARKER="R77"
    else:
        AUTOSYS_MARKER=ENV_MARKER + envName.translate(None, string.letters)

    DB_MARKER = database.replace("RDR_","")

    RDR_DB_IP = getDatabaseHostIP()
    if RDR_DB_IP is None:
         printErrorAndExit("IP address OR entry for database {0} does not exist in odbc.ini file.".format(database))

    if os.path.exists(targetProfile):
        os.remove(targetProfile)

    prodShareFolder=None
    prodShareFolderEnv=None
    out_file = open(targetProfile,"w")
    hand = open(sourceProfile)
    for line in hand:
        if ( line.strip().startswith("PRODGSShareLocation")) :
            prodShareFolder=line.strip().split("=")[1]
        elif ( line.strip().startswith("PROD_SHARED_PATH_ENV")) :
            prodShareFolderEnv=line.strip().split("=")[1]
        elif ( line.strip().startswith("LINUX_SHARED_PATH_GS") and (envName.upper() in prodShareFolderEnv) )  :
            gsPath="LINUX_SHARED_PATH_GS="+prodShareFolder+" export LINUX_SHARED_PATH_GS"
            line=gsPath
            print ("Replaced LINUX_SHARED_PATH_GS with PROD_SHARED_PATH_ENV")
        elif re.search(ENV_MARKER+"XX",line) :
            line=line.replace(ENV_MARKER+"XX",DB_MARKER)
        elif  re.search(ENV_MARKER.lower()+"xx",line) :
            line=line.replace(ENV_MARKER.lower()+"xx",envName)
        elif re.search("XX",line) :
            line=line.replace("XX",AUTOSYS_MARKER)
        elif (re.search(ENV_MARKER+"X",line)) and (re.search("LINUX",line) is None) :
                        line=line.replace(ENV_MARKER+"X",AUTOSYS_MARKER)
        elif (re.search("[ODBC_INI_IP_ADDRESS]",line)):
            line=line.replace("[ODBC_INI_IP_ADDRESS]",RDR_DB_IP)

        out_file.write(line)


    out_file.close()
    hand.close()

    print ("Created profile {0} from {1}".format(targetProfile,sourceProfile))


def postinstall() :

    print("Starting copying profiles into config folder....")
    deployDir="/apps/mrng/"+envName
    if not os.path.exists(deployDir):
        os.makedirs(deployDir)

    deployConfigDir=os.path.join(deployDir,"config")
    if not os.path.exists(deployConfigDir):
        os.makedirs(deployConfigDir)

    sourceConfigDir=os.path.join(releaseDir,"config")

    shutil.copy(os.path.join(sourceConfigDir,envName+"Profile"),deployConfigDir)
    shutil.copy(os.path.join(sourceConfigDir,"mrngProfile"),deployConfigDir)
    shutil.copy(os.path.join(sourceConfigDir,"mipProfile"),deployConfigDir)
    rdrPasswordFile=deployConfigDir + "/" + "rdrPassword"
    shutil.copy(os.path.join(sourceConfigDir,"rdrPassword_temp"),rdrPasswordFile)
    shutil.copy(os.path.join(sourceConfigDir,"archive_files_path.txt"),deployConfigDir)
    shutil.copy(os.path.join(sourceConfigDir,"clean_files_path.txt"),deployConfigDir)
    shutil.copy(os.path.join(sourceConfigDir,"archive_clean_days.txt"),deployConfigDir)

    """
    postistall.pl script require to source /apps/mrng/<env>/<env>Profile
    sourcing in python and then calling perl script is kind of complicated
    Simple solution, create bash shell; source profile and then perl
    """
    os.chdir(os.path.join(releaseDir,"postinstall_scripts"))
    cmd = "./sourcePostinstall.sh {0} {1}".format(envName,releaseDir)

    print("Executing {0}".format(cmd))

    retCode = os.system(cmd)
    if retCode > 0:
        printErrorAndExit("Deployment process is failed because of error in postinstall, exiting ........");


    print("postinstall job finished sucessfully .....")


"""
Deploy JIL scripts listed in config/deployJilScripts.txt
JIL script file names can be added or remove to deploy
without making code changes
"""
def deployJils() :
    print("Deploying JILs to AutoSys........")
    jilScripts=releaseDir+os.path.sep+"config"+os.path.sep+"deployJilScripts.txt"
    if not os.path.exists(jilScripts):
         printErrorAndExit("File {0} containing JIL scripts does not exist, exiting ........".format(jilScripts))

    ENV_MARKER = envName.upper()[:1]
    AUTOSYS_MARKER=ENV_MARKER + envName.translate(None, string.letters)
    deployJILdir="/apps/mrng/"+envName+"/JIL"
    os.chdir(os.path.join(releaseDir,"postinstall_scripts"))

    jils = open(jilScripts)
    for line in jils:
        line=line.rstrip()
        if re.search('[RUN_ENV]',line) :
            jilFile=deployJILdir+os.path.sep+line.replace("[RUN_ENV]",AUTOSYS_MARKER).strip()
            if not os.path.exists(jilFile):
                printErrorAndExit("JIL File {0} does not exist, exiting ........".format(jilFile))

            print("Deploying JIL File {0} ".format(jilFile));
            cmd = "./sourceAutoSys.sh {0} {1}".format(envName,jilFile)
            retCode = os.system(cmd)
            if retCode > 0:
                prompt = query_yes_no("Deployed JIL return with error code not 0 ({0}), Do you want to continue".format(retCode))
                if prompt == False:
                    sys.exit()


def query_yes_no(question, default="yes") :
    valid = {"yes":True, "y":True, "ye":True,
             "no":False, "n":False}

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [n/N] "
    else:
        raise ValueError("Invalid default answer: %s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def printErrorAndExit(errorString):
    print RED_COLOR + errorString + NO_COLOR
    sys.exit(2)

def main(argv):

    if len(argv) < 3:
         printErrorAndExit ( usage() )

    LoadPkgArgs(argv)
    print ("Deployment environment="+envName)
    print ("Database="+database.upper())
    print ("Deployment release folder="+releaseDir)

    releaseDeploy()

    passwordSet()
    createProfile()
    postinstall()

    """
    deployJils()
    """

    os.chdir(currDir);

    print ("Environment deployment process successfully finished..............")


if __name__ == "__main__":
    main(sys.argv[1:])
