#!/usr/bin/env python

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

vendor = 'ITL'
incomingFTPdir = '/afs/slac/public/incoming/lsst/p277'

#vendor = 'e2v'
#incomingFTPdir = '/afs/slac/public/incoming/lsst/???'


vendorDir = os.path.join('/nfs/farm/g/lsst/u1/vendorData/',vendor)    ## physical location
vendorLDir = os.path.join('/LSST/vendorData/',vendor)                 ## dataCatalog

print 'vendor = ',vendor
print 'incomingFTPdir = ',incomingFTPdir
print 'vendorDir = ',vendorDir
print 'vendorLDir = ',vendorLDir



# Check if Vendor Data is present
#    Require both a compressed tarball (data) and md5 checksum files
#    File recognition recipe may need to change...

try:
   flist = os.listdir(incomingFTPdir)
except:
   print 'Failure to find vendor ftp directory ',incomingFTPdir
   sys.exit(1)
   pass

print 'There are ',len(flist),' files found in ',incomingFTPdir

md5file = ''
datafile = ''
for file in flist:
   if file.endswith('.md5'):md5file = os.path.join(incomingFTPdir,file)
   if file.endswith('.gz'):datafile = os.path.join(incomingFTPdir,file)
   pass

if md5file ==  '' or datafile == '':
   print 'Expected vendor files not found in ftp directory'
   sys.exit(1)
   pass

print '  md5file = ',md5file
print '  datafile = ',datafile


# Create target directory for Vendor Data (format = YYYYMMDD.HHMMSS)

deliveryTime = datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
targetDir = os.path.join(vendorDir,deliveryTime)
print 'targetDir = ',targetDir
os.makedirs(targetDir)


# md5 checksum comparison, pre- and post-ftp

md5old = open(md5file).read().split()[0]
md5new = hashlib.md5(open(datafile).read()).hexdigest()
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

vendorPointer = './vendorData'
if os.access(vendorPointer,os.F_OK):
   print 'ERROR: pointer to vendor data already exists in working directory'
   sys.exit(1)
   pass

try:
   os.symlink(targetDir,'./vendorData')
except:
   print 'Unable to create link to vendorData...this should not happen.'
   sys.exit(1)
   pass


# Clean up incoming ftp area

trashDir = os.path.join(os.path.dirname(vendorDir),'FTP',vendor,deliveryTime)
print 'trashDir =', trashDir
try:
   os.makedirs(trashDir)
   shutil.move(datafile,os.path.join(trashDir,os.path.basename(datafile)))
   shutil.move(md5file,os.path.join(trashDir,os.path.basename(md5file)))
except:
   print 'Failed to cleanup incoming ftp directory'
   pass



# Register files in newly created directory tree

print '\n Register vendor datasets in dataCat'
targetLDirRoot = os.path.join(vendorLDir,deliveryTime)
print 'targetLDirRoot = ',targetLDirRoot
site = 'slac.lca.archive'
print 'site = ',site

sys.exit(0) ######################################### TEMPORARY ################################################







import datacat
client = datacat.Client(CONFIG_URL("lsst",mode="prod"))

for root,dirs,files in os.walk(targetDir):
   for dir in dirs:                     ## Loop over all vendor directories, create logical folders in dataCat
      newDir = os.path.join(targetLDirRoot,os.path.relpath(root,targetDir))
      foo = client.mkdir(newDir)
      pass

   for file in files:                   ## Loop over all vendor files and register in dataCat
      vFile = os.path.join(root,file)   ## vendor file physical location
      dPath = os.path.join(targetLDirRoot,os.path.relpath(root,targetDir)) ## logical location within dataCatalog
      print 'vFile = ',vFile
      print 'dFile = ',dFile

      dType = 'LSSTVENDORDATA'
      filetypeMap = {'fits':'fits','fit':'fits','txt':'txt','jpg':'jpg','png':'png','pdf':'pdf','html':'html','htm':'html'}
      ext = os.path.splitext(file)[1].strip('.')
      if ext in filetypeMap:
         fType = filetypeMap[ext]
      else:
         fType = 'dat'
         pass
      print 'fType = ',fType

      foo = client.create_dataset(dPath, file, dType, fType, site=site, resource=vFile)
      pass
   pass




# Done.
sys.exit(0)
