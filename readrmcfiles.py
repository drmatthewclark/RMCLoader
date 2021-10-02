#!/usr/bin/python3

# this is designed to run from the RMC version directory, e.g. 201857.
# it further assumes that the loader information is in a directory ../loader from
# that directory

# owner of database or db to connect to
debug = False
CHUNKSIZE = 100000

import xml.etree.ElementTree as ET
import psycopg2 as psql
from   psycopg2.extensions import AsIs
import glob
import gzip
import rdkit
from   rdkit import Chem
from   rdkit import RDLogger
from pathlib import Path
import os
from dbconnect import getConnection

# global db of hash of all lines added to databae
lines = set()

# shared cache of sql to execute
insertcache = set()


def readfile(fname, key, sql):
    """ 
    read an xml file into the designated database
    fname - xml file to read
    key - field for the object key
    sql - template sql statement to execute for storing the data
    """
    print(fname)
    tree = ET.parse(gzip.open(fname));
    root = tree.getroot()
    cur = conn.cursor()

    for elem in root:
       id = elem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
       id = id[id.find('#')+1:].strip()  # the number is after the pound sign
       data = {}
       data[key] = id

       for subelem in elem:
          prefix, has_namespace, tag = subelem.tag.partition('}')
          value = subelem.text

          if has_namespace:
              tag = tag.strip()  # strip all namespaces

          if tag.startswith('has'):
              tag = tag[tag.find('has')+3:]
              value = subelem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
              value = value[value.find('#')+1:].strip()  # the number is after the pound sign
              data[tag] = value; 

          if (tag != 'Copyright'):
             data[tag] = value
        # some file have sub-sub elements
          for selm in subelem:
              for subsubelem in selm:
                prefix, has_namespace, postfix = subsubelem.tag.partition('}')
                value = subsubelem.text.strip();
                if has_namespace:
                    tag = postfix.strip()  # strip all namespaces
                # create array of data when multiple values are present
                if tag in data:
                   newlist = data[tag]
                   newlist.append(value) 
                   data[tag] = newlist
                else:
                    newlist = list()
                    newlist.append(value)
                    data[tag] = newlist 

       writedb(conn, data, sql)

    flush(conn) 
    print("\t%i records" % (len(lines)))


def sqlfromfile(schemafile):
    conn2 = getConnection()
    with open(schemafile, 'r') as schema:
        print('executing sql from', schemafile)
        command = schema.read()
        with conn2.cursor() as cur:
             cur.execute(command)
             conn2.commit()
    conn2.close()

def initdb():

    """ initialize the database"""
    drop  = "drop schema rmc cascade;"
    schemafile = '../RMCLoader/rmc_schema'
    with conn.cursor() as cur:
      try :
        cur.execute(drop)
        print("dropped existing schema")
      except:
        print("failed to drop schema")

    conn.commit()
    sqlfromfile(schemafile)
   

def readassay():
  """ read the assay data files into the assay table """

  sql = 'insert into rmc.assay (%s) values %s;'
  for filepath in glob.iglob('./*_assays_*.xml.gz'):
    readfile(filepath, 'aid', sql)


def readcitation():
  """ read the citation files into the citation table """
  sql = 'insert into rmc.citation (%s) values %s;'
  for filepath in glob.iglob('./*_citations_*.xml.gz'):
    readfile(filepath, 'cid', sql)


def readdatapoint():
  """ read the datapoint files into the datapoint table """

  sql = 'insert into rmc.datapoint (%s) values %s;'
  for filepath in glob.iglob( './*_datapoints_*.xml.gz'):
    readfile(filepath, 'did', sql)


def readfact():
  """ read the facts file into the fact table """
  sql = 'insert into rmc.fact (%s) values %s;'
  for filepath in glob.iglob('./*_facts_*.xml.gz'):
    readfile(filepath, 'rxid', sql)


def readtarget():
    """ read the targets file into the target table
    """
    sql = 'insert into rmc.target (%s) values %s;'
    for filepath in glob.iglob('./*_targets*.xml.gz'):
        readfile(filepath, 'tid', sql)

nl = '\n'  # newline; cound be \r\n if necessary

def readnextSDfile(file):
    """ read the next SDFile from the file of concatenated SDfiles
    return a dictionary with the SDFile tags and data, and the SDFile
    """
    line = '' # file.readline()
    global notEof
    sdfile = 'Molname'
    tags = {}
    blanklinecount = 0

    while  line != '$$$$':
        if line.startswith('>  <'):  # data tag
            tag = line[8:len(line)-1] # skip IDE. part of tag
            data = file.readline().strip().decode()
            sdfile = sdfile + nl + data
            file.readline()  # blank line at end
            sdfile = sdfile + nl
            if tag != 'RIGHT':   # skip copyright
                tags[tag] = data

        line = file.readline().rstrip().decode()

        if (len(line.strip()) == 0):
           blanklinecount += 1
           if blanklinecount > 3:
              return  'EOF'
        else:
           blanklinecount = 0

        sdfile = sdfile + line+ nl

    sdfile = sdfile.strip()[:sdfile.find('M  END')+6]
    # create smiles as it is much more compact than the sdfile
    # one can add the sdfile too if you want
    smiles = ''

    # one particular file seems to be problematic
    if tags is not None and 'XRN' in tags.keys() and tags['XRN'] == '21291617':
        sdfile = ''   
      
    try: 
        mol = Chem.MolFromMolBlock(sdfile)
        if mol:
           smiles = Chem.MolToSmiles(mol, isomericSmiles=True,canonical=True)
           tags['smiles'] = smiles
        else:
           mol = '' 
    except:
        mol = ''
    if debug:
        print(tags) 
    return tags # dictionary 



def readsdfiles(fname):
    """ read all of the individual SDFiles from the concatenated SDFile """
    print('readsdfile ', fname)
    sql = 'insert into rmc.sdfile (%s) values %s;'
    lg = RDLogger.logger()
    lg.setLevel(RDLogger.CRITICAL)
    count = 0
    with gzip.open(fname, 'r') as file:

        while True:
            sdrecord = readnextSDfile(file)
            if sdrecord != 'EOF':
                writedb(conn, sdrecord, sql)
                count += 1
                if (count % 50000 == 0):
                    print('readsdfiles records',count)
            else:
               break

    flush(conn)
    print("wrote ", count, " records")



def writedb(conn, data, sql):
     """ write a SDFile record the database """
    # if  not 'XRN' in data.keys() or data['XRN'] == None or data['XRN'] == '':
    #     return

     with conn.cursor() as cur:
         columns = data.keys()
         values = [data[column] for column in columns]
         cmd = cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))).decode('utf-8')

         h = hash(cmd)
         if not h in lines:
            lines.add(h)
            insertcache.add(cmd)
            if len(insertcache) >= CHUNKSIZE:
                flush(conn)
   
def flush(conn):
  """ flush the data cache to the database """
  if (debug):
      print('flushed cache of ', len(insertcache) )

  statement = '\n'.join(insertcache) 
  with conn.cursor() as cur:
      if len(statement) > 1:
        cur.execute(statement)

  conn.commit()
  insertcache.clear()



def readsdfile():
  """ read the SDFiles. This requires special functions because this is not an XML file
  """
  path = './*.sdf.gz' 
  print(path)
  for filepath in glob.iglob(path):
    readsdfiles(filepath)



#
# import the set of RMC files into a postgres database.
# this assumes that the current directory is the one with the file set.
#
# reads the unzipped gz file as supplied by Elsevier
#

def load():

    path = Path('.')
    version = os.path.basename(path.parent.absolute())
    print('loading version', version)

    with conn.cursor() as cur:
       cur.execute('insert into rmc.version (version) values (%s);', (version,))
       conn.commit()

    readassay()
    readcitation()
    readdatapoint()
    readfact()
    readtarget()
    readsdfile()

conn=getConnection()
initdb()
load()
# apply indices
sqlfromfile('../RMCLoader/rmc_index')

print('completed')
