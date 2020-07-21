from .sftp import SFTP

from pymongo import MongoClient

mongo_uri = "mongodb+srv://vignesh:Fjm4mhgiObuVDGDO@cluster0-ppgkd.mongodb.net/test?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client.arlocam

with SFTP() as sftp:
    snapshots = db.snapshots.find()
    print(snapshots.count())
    lcount = []
    count = 1
    fname = snapshots[0]["file_name"]
    fdate = snapshots[0]["created_date"].replace(second=0)
    for shot in snapshots[1:]:
        cur_fname = shot["file_name"]
        cur_fdate = shot["created_date"].replace(second=0)
        if cur_fdate == fdate:
            count += 1
            # db.snapshots.delete_one(shot)
            # sftp.sftp.remove(sftp.remote_snaphot_path + cur_fname)
        else:
            print(count)
            count = 1
            fname = cur_fname
            fdate = cur_fdate
