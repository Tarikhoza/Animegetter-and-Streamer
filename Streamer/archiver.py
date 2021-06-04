import py7zr
import os
import shutil


errors=[]


def unpack(filename,src,dest):
    free=shutil.disk_usage("/").free
    filesize=os.path.getsize("{}/{}.7z".format(src,filename))
    print("Unpacking {}".format(filename))
    if free>filesize:
        with py7zr.SevenZipFile("{}/{}.7z".format(src,filename), 'r') as archive:
            archive.extract(path="{}/".format(dest))
        os.remove("{}/{}.7z".format(src,filename))
        print("{} sucessful unpacked".format(filename))
    else:
        errors.append("{}.zip is to big to unpack!!!".format(filename))


def pack(filename,src,dest):
    free=shutil.disk_usage("/").free
    filesize=os.path.getsize("{}/{}".format(src,filename))
    print("Archiving {}".format(filename))
    print(free,filesize)
    if free>filesize*2:
        with py7zr.SevenZipFile("{}/{}.7z".format(dest,filename), 'w') as archive:
            archive.writeall("{}/{}".format(src,filename),filename)
        shutil.rmtree("{}/{}".format(src,filename))
        print("{} sucessful archived".format(filename))
    else:
        errors.append("{} is to big to archive!!!".format(filename))
