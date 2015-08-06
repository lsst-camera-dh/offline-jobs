#!/usr/bin/env python

'''
producer_vendorIngest.py - jobHarness script for use by eTraveler to ingest vendor data

Tentative Conventions:
1. ITL data arrives at SLAC as ITL-<sensorID>.tar.gz along with ITL-<sensorID>.md5
2. e2v data arrives at SLAC as e2v_<sensorID>.tar.bz2 along with e2v_<sensorID>.md5sum
3. LSST-CAM ID for a newly arrived sensor shall be <vendor>-<vendorSerialNo>, e.g., ITL-98765
4. New hardware must be registered in the eTraveler DB prior to running this traveler
5. eTraveler "LSSTCAM serial" corresponds to LCATR_UNIT_ID, e.g., ITL-98765
6. eTraveler "Hardware Type" corresponds to LCATR_UNIT_TYPE ("ITL-CCD" or "e2v-CCD")

=====================================================================================
=====================================================================================
=====================================================================================

Where is everything?

LSSTROOT = /nfs/farm/g/lsst/u1

** Original copy of vendor delivery (maybe):
$LSSTROOT/vendorData/FTP/<vendor>/<deliveryDate>

where vendor = {e2v,ITL}

** Archive copy of vendor delivery:
$LSSTROOT/vendorData/FTP/<vendor>/delivery/<deliveryDate>/*.{tar.bz2, md5sum}

where deliveryDate = YYYYMMDD or YYYYMMDD{a-z} if multiple deliveries on same day

** Unpacked copy of vendor delivery (after eTraveler SR-RCV-1):
$LSSTROOT/vendorData/<vendor>/<sensorID>/<eTmode>/<JHinstance>/...

where
  sensorID = official LSST sensorID, e.g., e2v-11093-10-04

  eTmode = {Prod, Dev}

  JHinstance = the unique LCATR_JOB_ID value when the harnessed job is running

** dataCatalog location

/LSST/vendorData/<vendor>/<sensorID>/<eTmode>/<JHinstance>/...

=====================================================================================
=====================================================================================
=====================================================================================


'''
import os,sys, shutil
import hashlib
import subprocess, shlex
import datetime
import tarfile


debug = False


print '\n\nIngest LSST Vendor Data.'
start = datetime.datetime.now()
print 'Configuration:\n============='
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
####################################################################################
####################################################################################


def regFiles(targetDir,targetLDirRoot,deliveryTime):

   ## Register files in dataCatalog
   if debug: print '===\nEntering regFiles(',targetDir,',',targetLDirRoot,',',deliveryTime,')'

   ## Path to new RESTful dataCatalog client code (and dependency)
   #dc1 = '/afs/slac.stanford.edu/u/gl/srs/datacat/dev/0.3/lib'
   #sys.path.append(dc1)

   ## Initialize dataCatalog RESTful client interface
   from datacat import Client
   from datacat.auth import HMACAuthSRS

   url = "http://srs.slac.stanford.edu/datacat-v0.3/r"
   key_id = "2299c5cc-bbba-4009-8ea9-8ec61c7fb13d"
   secret_key = "pcda/8JUnCsK7vSENGxP3zMjbdaIUIeOXpBF8PlHXvQ6GNzJ4d4vBghyHHCUOZ+D14LBxMGRqy3aphk5M2LJ1w=="
   auth_strategy = HMACAuthSRS(key_id=key_id, secret_key=secret_key, url=url)
   client = Client(url, auth_strategy=auth_strategy)

   print 'targetLDirRoot = ',targetLDirRoot
   site = 'slac.lca.archive'
   print 'site = ',site

   try:
      client.mkdir(targetLDirRoot,parents=True)
   except Exception as e:
      ekeys = e.__dict__.keys()
      print "\n%ERROR: Failed to create dataCatalog folder: ",targetLDirRoot
      print "Exception keys: ",ekeys
      for key in ekeys:
         if key == 'raw': continue
         print ' ',key,': ',getattr(e,key)
         pass
      sys.exit(1)
      

   dType = 'LSSTVENDORDATA'
   filetypeMap = {'fits':'fits','fit':'fits','txt':'txt','jpg':'jpg','png':'png','pdf':'pdf','html':'html','htm':'html'}
   metaData = {"vendorDeliveryTime":deliveryTime}

   for root,dirs,files in os.walk(targetDir):
      print '-----------------'
      if debug:
         print 'root = ',root
         print 'dirs = ',dirs
         print 'files = ',files
         pass
      root = root.replace(' ','_').replace('(','').replace(')','')  #####################
      
      for dir in dirs:       ## Loop over all vendor directories, create logical folders in dataCat
         dir = dir.replace(' ','_').replace('(','').replace(')','')  #####################
         if root == targetDir:
            if debug: print 'root == targetDir'
            newDir = os.path.join(targetLDirRoot,dir)
         else:
            if debug: print 'root <> targetDir'
            newDir = os.path.join(targetLDirRoot,os.path.relpath(root,targetDir),dir)
            pass
         
         if not client.exists(newDir):
            print 'Creating dataCat folder: ',newDir
            try:
               client.mkdir(newDir, parents=True)
            except Exception as e:
               ekeys = e.__dict__.keys()
               print "\n%ERROR: Failed to create dataCat folder: ",newDir
               print "Exception keys: ",ekeys
               for key in ekeys:
                  if key == 'raw': continue
                  print ' ',key,': ',getattr(e,key)
                  pass
               sys.exit(1)
            pass
         else:
            print "dataCatalog folder already exists: ",newDir
            pass
         pass

      for file in files:                   ## Loop over all vendor files and register in dataCat
         file = file.replace(' ','_').replace('(','').replace(')','') ##################
         print 'Registering file: ',file
         vFile = os.path.join(root,file)   ## vendor file physical location
         relpath = os.path.relpath(root,targetDir)
         if relpath == '.':
            dPath = targetLDirRoot
         else:
            dPath = os.path.join(targetLDirRoot,os.path.relpath(root,targetDir)) ## logical location within dataCatalog
            pass

         ext = os.path.splitext(file)[1].strip('.')
         if ext in filetypeMap:
            fType = filetypeMap[ext]
         else:
            fType = 'dat'
            pass

         if debug:
            print 'vFile = ',vFile
            print 'dPath = ',dPath
            print 'fType = ',fType
            pass

         try:
            client.create_dataset(dPath, file, dType, fType, site=site, resource=vFile, versionMetadata=metaData)
         except Exception as e:
            ekeys = e.__dict__.keys()
            print "\n%ERROR: Failed to register dataset: ",file
            print "Exception keys: ",ekeys
            for key in ekeys:
               if key == 'raw': continue
               print ' ',key,': ',getattr(e,key)
               pass
            sys.exit(1)
         pass
      pass
   return




####################################################################
###########    ITL    ##############################################
####################################################################
if vendor == 'ITL':

# Check FTP area if Vendor Data is present
#    Require both a compressed tarball (data) and md5 checksum files
#    File recognition recipe may need to change...
   incomingFTPdir = '/afs/slac/public/incoming/lsst/ITL'
   print 'incomingFTPdir = ',incomingFTPdir

   try:
      flist = os.listdir(incomingFTPdir)
   except:
      print '\n%ERROR: Failure to find vendor ftp directory ',incomingFTPdir
      sys.exit(1)
      pass

   print 'There are ',len(flist),' files found in ',incomingFTPdir

   ## File naming convention for ITL as of May 2015
   vendorID = LSSTID.split('-',1)[1]
   md5file = 'ID-'+vendorID+'.md5'
   datafile = 'ID-'+vendorID+'.tar.gz'

   print 'md5file:  ',md5file
   print 'datafile: ',datafile

   if md5file not in flist or datafile not in flist:
      print '\n%ERROR: Unable to find expected files in FTP area'
      print ' Full ftp directory listing (',incomingFTPdir,'):'
      for file in flist:
         print file
         pass
      sys.exit(1)
      
# Create target directory for Vendor Data (format = YYYYMMDD.HHMMSS)
   deliveryTime = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
   targetDir = os.path.join(vendorDir,deliveryTime)
   print 'targetDir = ',targetDir
   os.makedirs(targetDir)


# md5 checksum comparison, pre- and post-ftp
   md5file = os.path.join(incomingFTPdir,md5file)
   datafile = os.path.join(incomingFTPdir,datafile)

   md5old = open(md5file).read().split()
   if len(md5old) == 1:                   ## ITL has changed the format of its md5 file...
      md5old = md5old[0].upper()
   elif len(md5old) >= 3:
      md5old = open(md5file).read().split()[2].upper()
   else:
      print '\n%ERROR: Unable to parse supplied md5 file: ',md5file
      sys.exit(1)
      
   md5new = hashlib.md5(open(datafile).read()).hexdigest().upper()
   if md5old != md5new:
      print '\n%ERROR: Checksum error in vendor tarball:\n old md5 = ',md5old,'\n new md5 = ',md5new
      sys.exit(1)
      pass


# Uncompress/untar into target directory
   try:
      tarfile.open(datafile,'r').extractall(targetDir)
   except:
      print '\n%ERROR: Failed to extractall from vendor tarball'
      sys.exit(1)
      pass

# Create pointer to new Vendor Data for subsequent 'validator' step
   vendorPointer = os.path.join(os.environ['PWD'],'vendorData')
   print 'vendorPointer = ',vendorPointer
   if os.access(vendorPointer,os.F_OK):
      print '\n%ERROR: pointer to vendor data already exists in working directory'
      sys.exit(1)
      pass
   try:
      os.symlink(targetDir,vendorPointer)
      print 'Link to vendor data created.'
   except:
      print '\n%ERROR: Unable to create link to vendorData...this should not happen.'
      sys.exit(1)
      pass


# Backup this delivery and clean up incoming ftp area
   trashDir = os.path.join(os.path.dirname(vendorDir),'FTP',vendor,deliveryTime)
   print 'trashDir =', trashDir
   try:
      os.makedirs(trashDir)
      ##################  DEV ONLY - leave files in FTP area  ####################
      shutil.copyfile(datafile,os.path.join(trashDir,os.path.basename(datafile)))
      shutil.copyfile(md5file,os.path.join(trashDir,os.path.basename(md5file)))
      ##################  RE-ENABLE the following for production  ################
      #      shutil.move(datafile,os.path.join(trashDir,os.path.basename(datafile)))
      #      shutil.move(md5file,os.path.join(trashDir,os.path.basename(md5file)))
   except:
      print '\n%WARNING: Failed to cleanup incoming ftp directory'
      pass

# Register files in dataCatalog
   targetLDirRoot = os.path.join(vendorLDir,LSSTID,deliveryTime)
   regFiles(xxx,targetLDirRoot,deliveryTime)

   pass




####################################################################
###########    e2v    ##############################################
####################################################################
elif vendor == 'e2v':

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

   ## File naming convention for e2v as of June 2015
   ##   e2v files look like, e.g., e2v-11093-02-01.{md5,tar.bz2}
   vendorID = LSSTID.split('-',1)[1]

   ## Look for data and checksum files
   fileName = 'ID-'+vendorID
   md5file = ''
   datafile = ''
   for file in flist:
      if file.startswith(fileName):
         if file.endswith('.tar.bz2') or file.endswith('.tar.gz'): datafile = file
         if file.endswith('.md5') or file.endswith('.md5sum'): md5file = file
         pass
      pass
   if len(md5file) == 0 or len(datafile) == 0:
      print '\n%ERROR: Unable to find expected files in FTP area'
      print ' Full ftp directory listing (',vendorFTPdir,'):'
      for file in flist:
         print file
         pass
      sys.exit(1)
      
   print 'Found md5file:  ',md5file
   print 'Found datafile: ',datafile

   
# Create target directory for Vendor Data
   print 'Create target directory for vendor data.'
   if not os.access(vendorDir,os.F_OK): os.makedirs(vendorDir)

# md5 checksum comparison, pre- and post-ftp
   print 'Verify md5 checksums'
   print datetime.datetime.now()

   md5file = os.path.join(vendorFTPdir,md5file)
   datafile = os.path.join(vendorFTPdir,datafile)

   md5old = open(md5file).read().split()
   if len(md5old) == 2:             ## Current e2v standard format
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
   print 'Uncompress and unpack tarball'
   print datetime.datetime.now()

   try:
      tarfile.open(datafile,'r').extractall(vendorDir)
   except:
      print '\n%ERROR: Failed to extractall from vendor tarball'
      sys.exit(1)
      pass

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
   regFiles(vendorDir,vendorLDir,deliveryTime)

   pass


####################################################################
###########    unknown    ##########################################
####################################################################
else:
   print 'Unrecognized vendor: ',vendor
   sys.exit(1)


# Done.
fini = datetime.datetime.now()
print fini,"   Done."
print 'Total elapsed time = ',fini-start
sys.exit(0)
