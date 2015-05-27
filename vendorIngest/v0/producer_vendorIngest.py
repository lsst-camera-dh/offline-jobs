#!/usr/bin/env python

## producer_vendorIngest.py - jobHarness script for use by eTraveler

'''
producer_vendorIngest.py - jobHarness script for use by eTraveler to ingest vendor data

Conventions:
1. ITL data arrives at SLAC as ITL-<sensorID>.tar.gz along with ITL-<sensorID>.md5
2. e2v data conventions are not yet defined
3. LSST-CAM ID for a newly arrived sensor shall be <vendor>-<vendorSerialNo>, e.g., ITL-98765
4. New hardware must be registered in the eTraveler DB prior to running this traveler
5. eTraveler "LSSTCAM serial" corresponds to LCATR_UNIT_ID, e.g., ITL-98765
6. eTraveler "Hardware Type" corresponds to LCATR_UNIT_TYPE ("ITL-CCD" or "e2v-CCD")



'''
import os,sys, shutil
import hashlib
import subprocess, shlex
import datetime
import tarfile

#jobname = os.environ["LCATR_JOB"]
#jobdir = "%s/share/%s/%s" % (os.environ["VIRTUAL_ENV"], jobname,
#                          os.environ["LCATR_VERSION"])

print "Ingest LSST ITL Vendor Data from incoming ftp@SLAC"

#os.system('printenv|sort')
os.system('printenv|grep -i lcatr')

vendor = os.environ['LCATR_UNIT_ID'].split('-')[0]
LSSTID = os.environ['LCATR_UNIT_ID']

print 'Requested vendor: ',vendor
print 'Requested sensor: ',LSSTID

vendorDir = os.path.join('/nfs/farm/g/lsst/u1/vendorData/',vendor)    ## physical location
vendorLDir = os.path.join('/LSST/vendorData/',vendor)                 ## dataCatalog

print 'vendorDir = ',vendorDir
print 'vendorLDir = ',vendorLDir


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
      print 'Failure to find vendor ftp directory ',incomingFTPdir
      sys.exit(1)
      pass

   print 'There are ',len(flist),' files found in ',incomingFTPdir

   ## File naming convention for ITL as of May 2015
   vendorSer = LSSTID.split('-')[1]
   md5file = 'ID-'+vendorSer+'.md5'
   datafile = 'ID-'+vendorSer+'.tar.gz'

   print 'md5file:  ',md5file
   print 'datafile: ',datafile

   if md5file not in flist or datafile not in flist:
      print '\n%ERROR: could not find expected files in FTP area'
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
   md5old = open(md5file).read().split()[2].upper()
   md5new = hashlib.md5(open(datafile).read()).hexdigest().upper()
   if md5old != md5new:
      print 'Checksum error in vendor tarball:\n old md5 = ',md5old,'\n new md5 = ',md5new
      sys.exit(1)
      pass


# Uncompress/untar into target directory
   try:
      tarfile.open(datafile,'r').extractall(targetDir)
   except:
      print 'Failed to extractall from vendor tarball'
      sys.exit(1)
      pass

# Create pointer to new Vendor Data for subsequent 'validator' step
   vendorPointer = os.path.join(os.environ['PWD'],'vendorData')
   print 'vendorPointer = ',vendorPointer
   if os.access(vendorPointer,os.F_OK):
      print 'ERROR: pointer to vendor data already exists in working directory'
      sys.exit(1)
      pass
   try:
      os.symlink(targetDir,vendorPointer)
      print 'Link to vendor data created.'
   except:
      print 'Unable to create link to vendorData...this should not happen.'
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
      print 'Failed to cleanup incoming ftp directory'
      pass




   ## Register files in dataCatalog

   ## Path to new RESTful dataCatalog client code (and dependency)
   dc1 = '/afs/slac.stanford.edu/u/gl/srs/datacat/dev/0.3/lib'
   sys.path.append(dc1)

   ## Initialize dataCatalog RESTful client interface
   from datacat import Client
   from datacat.auth import HMACAuthSRS

   url = "http://srs.slac.stanford.edu/datacat-v0.3/r"
   key_id = "2299c5cc-bbba-4009-8ea9-8ec61c7fb13d"
   secret_key = "pcda/8JUnCsK7vSENGxP3zMjbdaIUIeOXpBF8PlHXvQ6GNzJ4d4vBghyHHCUOZ+D14LBxMGRqy3aphk5M2LJ1w=="
   auth_strategy = HMACAuthSRS(key_id=key_id, secret_key=secret_key, url=url)
   client = Client(url, auth_strategy=auth_strategy)


   print '\n Register vendor datasets in dataCat'
   targetLDirRoot = os.path.join(vendorLDir,deliveryTime)
   print 'targetLDirRoot = ',targetLDirRoot
   site = 'slac.lca.archive'
   print 'site = ',site

   try:
      client.mkdir(targetLDirRoot,parents=True)
   except Exception as e:
      ekeys = e.__dict__.keys()
      print "\n%ERROR: Failed to register dataset: ",file
      print "Exception keys: ",ekeys
      for key in ekeys:
         if key == 'raw': continue
         print ' ',key,': ',getattr(e,key)
         pass
      sys.exit(1)
      

   dType = 'LSSTVENDORDATA'
   filetypeMap = {'fits':'fits','fit':'fits','txt':'txt','jpg':'jpg','png':'png','pdf':'pdf','html':'html','htm':'html'}

   for root,dirs,files in os.walk(targetDir):
      print 'root = ',root
      print 'dirs = ',dirs
      print 'files = ',files

      
      for dir in dirs:                     ## Loop over all vendor directories, create logical folders in dataCat
         newDir = os.path.join(targetLDirRoot,os.path.relpath(root,targetDir))
         print 'Creating dataCat folder: ',newDir
         client.mkdir(newDir)
         pass

      for file in files:                   ## Loop over all vendor files and register in dataCat
         print 'Registering file: ',file
         vFile = os.path.join(root,file)   ## vendor file physical location
         print 'vFile = ',vFile
         print 'targetLDirRoot = ',targetLDirRoot
         relpath = os.path.relpath(root,targetDir)
         if relpath == '.':
            dPath = targetLDirRoot
         else:
            dPath = os.path.join(targetLDirRoot,os.path.relpath(root,targetDir)) ## logical location within dataCatalog
            pass
         print 'dPath = ',dPath

         ext = os.path.splitext(file)[1].strip('.')
         if ext in filetypeMap:
            fType = filetypeMap[ext]
         else:
            fType = 'dat'
            pass
         print 'fType = ',fType

         try:
            client.create_dataset(dPath, file, dType, fType, site=site, resource=vFile)
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
   pass
















####################################################################
###########    e2v    ##############################################
####################################################################
elif vendor == 'e2v':
   print 'e2v data ingest procedure is not yet defined'
   sys.exit(1)


####################################################################
###########    unknown    ##########################################
####################################################################
else:
   print 'Unrecognized vendor: ',vendor
   sys.exit(1)


# Done.
sys.exit(0)
