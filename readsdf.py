#
# read sdfiles, store as smiles strings
#
import xml.dom.minidom
import xml.etree.ElementTree as ET
import psycopg2 as psql
from psycopg2.extensions import AsIs
import glob
from version import rmcversion
from rdkit import Chem
from rdkit import RDLogger
import shutil

nl = '\n'

def main():
  for filepath in glob.iglob('./' + rmcversion + '*.sdf'):
    total, used, free = shutil.disk_usage('/')
    print(used, total)
    used = 1.0*used/total
    print("disk use ", used)
    if (used > 0.90):
       break
    readfile(filepath)


def readnextSDfile(file):
    line = '' # file.readline()
    sdfile = 'Molname'
    tags = {}
    blanklinecount = 0

    while line != '$$$$':
        if line.startswith('>  <'):  # data tag
            tag = line[8:len(line)-1] # skip IDE. part of tag
            data = file.readline().strip()
            sdfile = sdfile + nl + data
            file.readline()  # blank line at end
            sdfile = sdfile + nl
            if tag != 'RIGHT':   # skip copyright
                tags[tag] = data

        line = file.readline().rstrip()
        if (line == ''):
           blanklinecount += 1
           if blanklinecount > 4:
              tags = {}
              break
        else:
           blanklinecount = 0

        sdfile = sdfile + line + nl
  
    sdfile = sdfile.strip()[:sdfile.find('M  END')+6]
   
    try: 
        mol = Chem.MolFromMolBlock(sdfile)
        if mol:
           smiles = Chem.MolToSmiles(mol)
           tags['smiles'] = smiles
        else:
           mol = '' 
    except:
        mol = ''
    return tags # dictionary 


def readfile(fname):
    print(fname)
    lg = RDLogger.logger()
    lg.setLevel(RDLogger.CRITICAL)
    count = 0
    conn=psql.connect(user='mclark')
    with open(fname, 'r') as file:
        while True:
            sdrecord = readnextSDfile(file)
            if len(sdrecord) < 2:
                break;
            writedb(conn, sdrecord)
            count += 1
            if (count % 50000 == 0):
                print(count)

    conn.commit()
    conn.close()
    print("wrote ", count, " records")

def writedb(conn, data):
     sql = 'insert into rmc.sdfile (%s) values %s'
     with conn.cursor() as cur:
         columns = data.keys()
         values = [data[column] for column in columns]
         #print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
         cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))

main()
