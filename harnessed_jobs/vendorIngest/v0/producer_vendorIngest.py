#!/usr/bin/env python

"""
producer_vendorIngest.py - jobHarness script for use by eTraveler to
ingest vendor data for science raft and corner raft sensors

Tentative Conventions:
1. LSST-CAM ID for a newly arrived sensor shall be <vendor>-<model>-<vendorSerialNo>,
     e.g., ITL-3800C-126
2. New hardware must be registered in the eTraveler DB prior to running this traveler
3. eTraveler "LSSTCAM serial" corresponds to LCATR_UNIT_ID, e.g., ITL-3800C-126
4. eTraveler "Hardware Type" corresponds to LCATR_UNIT_TYPE ("ITL-CCD" or
     "ITL-Wavefront-CCD" or "e2v-CCD")

=====================================================================================
=====================================================================================
=====================================================================================

Where is everything?


** Original copy of vendor delivery
***    Vendors push data via (s)ftp to lsst-ftp.slac.stanford.edu
***    Space managed by vendors
LSST-FTP = /nfs/farm/g/lsst/u2
$LSST-FTP/<vendor>

where vendor = {e2v,E2V,ITL}

** Archive copy of vendor delivery:
LSSTROOT = /nfs/farm/g/lsst/u1
$LSSTROOT/vendorData/FTP/<vendor>/delivery/<deliveryDate>/*.{tar.bz2, md5sum, md5}

where deliveryDate = YYYYMMDD or YYYYMMDD{a-z} if multiple deliveries on same day

  ---> ONLY a single sensor's data per delivery directory!

** Unpacked copy of vendor delivery (after eTraveler SR-RCV-01 or CR-RCV-01):
$LSSTROOT/vendorData/<vendor>/<LSSTsensorID>/<eTmode>/<JHinstance>/...

where
  LSSTsensorID = official LSST sensorID, e.g., ITL-3800C-126

  eTmode = {Prod, Dev}

  JHinstance = the unique LCATR_JOB_ID value when the harnessed job is running

** dataCatalog location

/LSST/vendorData/<vendor>/<sensorID>/<eTmode>/<JHinstance>/...

=====================================================================================
=====================================================================================
=====================================================================================


"""
import os,sys, shutil
import hashlib
import subprocess, shlex
import datetime
import tarfile
import registry


debug = False
dryrun = False


print '\n\nIngest LSST Vendor Data.'
start = datetime.datetime.now()
print 'Configuration:\n============='
print 'Now Running ',sys.argv[0]
print 'Start time: ',start
print 'Current working directory (os.environ): ',os.environ['PWD']
#rc = os.system('printenv|grep -i lcatr')
if debug: rc = os.system('echo ALL ENVIRONMENT VARIABLES;printenv|sort;echo END ENVVAR LIST')



# Determine true working directory and extract JOB_ID from final path element
#   (Note: this took a huge amount of trial and error because os.environ['PWD']
#    incorrectly reports the current directory as the one the lcatr command
#    was executed from -- not the correct directory with the instance #)
cmd = 'printenv PWD'
pwd = subprocess.check_output(cmd, shell=True).strip()
print 'True current working directory: ',pwd
jobid = os.path.basename(pwd)
try:
   foo = int(jobid)
except:
   print '%ERROR: Failure to parse jobHarness version number from PWD: ',jobid
   sys.exit(1)
   pass
print 'JobHarness ID = ',jobid

# Determine eTraveler mode (e.g., "Prod" or "Dev")
#http://lsst-camera.slac.stanford.edu:80/eTraveler/Dev
eTmode = os.path.basename(os.environ['LCATR_LIMS_URL']).strip()
print 'eTraveler mode: ',eTmode


# Determine vendor
vendor = os.environ['LCATR_UNIT_ID'].split('-')[0]
LSSTID = os.environ['LCATR_UNIT_ID']
print 'Vendor: ',vendor
print 'SensorID: ',LSSTID

LCAROOT = '/nfs/farm/g/lsst/u1'    ## ROOT of all LSST Camera data at SLAC

vendorFTPdir = os.path.join(LCAROOT,'vendorData/FTP',vendor,LSSTID) ## physical location of tarball
vendorDir = os.path.join(LCAROOT,'vendorData',vendor,LSSTID,eTmode,jobid) ## physical location to store
vendorLDir = os.path.join('/LSST/vendorData/',vendor,LSSTID,eTmode,jobid) ## dataCatalog location

print 'vendorFTPdir (input)       = ',vendorFTPdir
print 'vendorDir (output)         = ',vendorDir
print 'vendorLDir (registration)  = ',vendorLDir
print '==================================================\n'

####################################################################################
## Setup RESTful dataCatalog client
####################################################################################
myDC = registry.registry(debug=debug,dryrun=dryrun)

myDC.init()

myDC.dumpConfig()

sys.stdout.flush()



####################################################################################
####################################################################################
####################################################################################

def sanitize(path):
   """Remove offending characters from string"""
   newPath = path.replace(' ','_').replace('(','').replace(')','')
   if debug: print 'original  string[',len(path),']: ',path
   if debug: print 'sanitized string[',len(newPath),']: ',newPath
   return newPath



def regVendorFiles(targetDirRoot,targetLDirRoot,deliveryTime):
   """Register vendor files at SLAC in dataCatalog"""
   if debug: print '===\nEntering regVendorFiles(',targetDirRoot,',',targetLDirRoot,',',deliveryTime,')'
   site = 'slac.lca.archive'

   myDC.dumpConfig()

   dType = 'LSSTVENDORDATA'
   filetypeMap = {'fits':'fits','fit':'fits','txt':'txt','jpg':'jpg','png':'png','pdf':'pdf','html':'html','htm':'html','xls':'xls'}
   metaData = {"vendorDeliveryTime":deliveryTime}

   for root,dirs,files in os.walk(targetDirRoot):
      print '-----------------'
      sys.stdout.flush()
      if debug:
         print 'root = ',root
         print '# dirs = ',len(dirs)
         print '# files = ',len(files)
         pass

      commonPath = os.path.relpath(root,targetDirRoot)
      if commonPath == '.': commonPath=''
      if debug:print 'commonPath = ',commonPath

      for file in files:                   ## Loop over all vendor files and register in dataCat
         if debug: print 'Adding dataCatalog registration for file: ',file

         filePath = os.path.join(root,file)
         dcFolder = os.path.join(targetLDirRoot,sanitize(commonPath))
         
         # Extract file extension and assign dataCatalog "file type"
         ext = os.path.splitext(file)[1].strip('.')
         if ext in filetypeMap:
            fType = filetypeMap[ext]
         else:
            fType = 'dat'
            pass
 
         if debug:
            print '\n Add registry data:'
            print 'filePath = ',filePath
            print 'dcFolder = ',dcFolder
            print 'site     = ',site
            print 'fType    = ',fType
            print 'dType    = ',dType
            pass

         myDC.register(filePath, dcFolder, site, fType, dType, metaData=metaData)
         sys.stdout.flush()
         pass
      pass
   myDC.dumpStats()
   return


def unpackTarfile(vendorFTPdir,datafile,md5file):

# md5 checksum comparison, pre- and post-ftp
   print '\nVerify md5 checksums: ',md5file
   print datetime.datetime.now()

   md5file = os.path.join(vendorFTPdir,md5file)
   datafile = os.path.join(vendorFTPdir,datafile)

   md5old = open(md5file).read().split()
   if len(md5old) == 1 or len(md5old) == 2:      ## Current e2v and ITL practice
      md5old = md5old[0].upper()
   elif len(md5old) >= 3:
      md5old = open(md5file).read().split()[2].upper()
   else:
      print '\n%ERROR: Unable to parse supplied md5 file: ',md5file
      sys.exit(1)

   md5new = hashlib.md5(open(datafile).read()).hexdigest().upper()
   print 'Old e2v checksum = ',md5old
   print 'New md5 checksum = ',md5new
   if md5old != md5new:
      print '\n%ERROR: Checksum error in vendor tarball:\n old md5 = ',md5old,'\n new md5 = ',md5new
      sys.exit(1)
      pass
   print 'Checksums match.'

# Uncompress/untar into target directory
   print 'Uncompress and unpack tarball: ',datafile
   print datetime.datetime.now()
   sys.stdout.flush()

   try:
      tarfile.open(datafile,'r').extractall(vendorDir)
   except:
      print '\n%ERROR: Failed to extractall from vendor tarball', filename
      sys.exit(1)
      pass
   return

######################## end of unpackTarfile() #############################








####################################################################
###########    e2v or E2V or ITL   ########################################
####################################################################
if vendor == 'e2v' or vendor == 'E2V' or vendor == 'ITL':

# Check FTP area if Vendor Data is present
#    Require both a compressed tarball (data) and md5 checksum files
#    File recognition recipe may need to change...

   print 'Check for vendor data in FTP directory.'
   try:
      flist = os.listdir(vendorFTPdir)
   except:
      print '\n%ERROR: Failure to find vendor ftp directory ',vendorFTPdir
      sys.exit(1)
      pass

   print 'There are ',len(flist),' files found in ',vendorFTPdir

   ## vendor ID is enforced by sensorID convention
   vendorID = LSSTID.split('-',1)[1]   ## 10/13/2015 unused

   ## Look for data and checksum files (and optional metrology files)
   ## Standard file names are sym links to actual vendor files
   #   fileName = 'ID-'+vendorID
   fileName = LSSTID  ## 10/13/2015 new file naming using "LSSTID" = <vendor>-<model>-<vendorID>
   md5file = ''
   datafile = ''
   metrologyDatafile = ''
   metrologyMd5file = ''
   metrology = False
   
   for file in flist:
      if file.startswith(fileName):
         if file.endswith('.tar.bz2') or file.endswith('.tar.gz'): datafile = file
         if file.endswith('.md5') or file.endswith('.md5sum'): md5file = file
         pass
         
      if file.startswith('metrology'):
         if file.endswith('.tar.bz2') or file.endswith('.tar.gz'): metrologyDatafile = file
         if file.endswith('.md5') or file.endswith('.md5sum'): metrologyMd5file = file
         metrology = True
         pass
      pass

   if len(md5file) == 0 or len(datafile) == 0:
      print '\n%ERROR: Unable to find expected data and/or checksum files in FTP area'
      print ' Filename = ',fileName
      print ' Full ftp directory listing (',vendorFTPdir,'):'
      for file in flist:
         print file
         pass
      sys.exit(1)
      
   print 'Found md5file:  ',md5file
   print 'Found datafile: ',datafile


   if metrology and (len(metrologyMd5file)==0 or len(metrologyDatafile)==0) :
      print '\n%ERROR: Unable to find expected metrology and/or checksum files in FTP area'
      print ' metrology data file = ',metrologyDatafile
      print ' metrology md5 file  = ',metrologyMd5file
      print ' Full ftp directory listing (',vendorFTPdir,'):'
      for file in flist:
         print file
         pass
      sys.exit(1)

   if metrology:
      print ' metrology data file = ',metrologyDatafile
      print ' metrology data file checksum = ',metrologyMd5file
      pass

   
# Create target directory for Vendor Data
   print 'Create target directory for vendor data.'
   if not os.access(vendorDir,os.F_OK): os.makedirs(vendorDir)


# Check MD5 checksums, then unpack tar file
   unpackTarfile(vendorFTPdir,datafile,md5file)

   if metrology: unpackTarfile(vendorFTPdir,metrologyDatafile,metrologyMd5file)


# Create a sym-link containing the delivery time (for posterity)
   deliveryTime = os.readlink(vendorFTPdir)
   deliveryTime = os.path.basename(deliveryTime)
   print 'Create sym link for deliveryTime (from vendorFTPdir) = ',deliveryTime
   os.symlink(deliveryTime,'deliveryTime')
   

# Create pointer to new Vendor Data for subsequent 'validator' step
## As of July 2015 e2v deliveries contain NO subdirectories - all files in top-level
   topOfDelivery = vendorDir

   try:
      os.symlink(topOfDelivery,'vendorData')
      #      os.symlink(targetDir,'vendorData')
      print 'Link to vendor data created.'
   except:
      print '\n%ERROR: Unable to create symbolic link to vendorData.'
      sys.exit(1)
      pass


# Change file permissions and group owner
   print 'Adjust file permissions'
   for dirpath, dirnames, filenames in os.walk(topOfDelivery):
      for dirname in dirnames:
         path = os.path.join(dirpath, dirname)
         os.chmod(path, 0o770)     ## all permissions for owner and group, none for world
         os.lchown(path,-1,2218)
         pass
      for filename in filenames:
         path = os.path.join(dirpath, filename)
         os.chmod(path, 0o660)     ## rw permissions for owner and group, none for world
         os.lchown(path,-1,2218)    ## 2218 = 'lsst'
         pass
      pass


# Register files in dataCatalog
   print '\n===\nRegister vendor data in dataCatalog'
   print datetime.datetime.now()
   regVendorFiles(vendorDir,vendorLDir,deliveryTime)

   pass


####################################################################
###########    unknown    ##########################################
####################################################################
else:
   print 'Unrecognized vendor: ',vendor
   sys.exit(1)


# Done.
fini = datetime.datetime.now()
print fini,"\n\n  Producer done."
print 'Total elapsed time = ',fini-start
print '\n================================================================\n\n'
sys.exit(0)
