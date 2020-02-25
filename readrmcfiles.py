# rmc file release number
rmcversion = 'rx190501'
dbname='mclark'
debug = False

import xml.dom.minidom
import xml.etree.ElementTree as ET
import psycopg2 as psql
from   psycopg2 import sql
from psycopg2.extensions import AsIs
import glob

def readfile(fname, key, dbname, sql):
    """ 
    read an xml file into the designated database

    fname - xml file to read
    key - field for the object key
    dbname - name for the database to store data to
    sql - template sql statement to execute for storing the data
    """
    print(fname)
    conn=psql.connect(user=dbname)
    tree = ET.parse(fname);
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

       columns = data.keys()
       values = [data[column] for column in columns]
       if debug:
           print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
       else:
           cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))

    conn.commit()
    conn.close()


def delete(tablename):
    """ clean out table for re-import """
    if debug:
        return

    conn=psql.connect(user=dbname)
    with conn.cursor() as cur:
        print('deleting records from', tablename)
        query = 'delete from ' + tablename
        cur.execute(query)
    conn.commit()
    conn.close()

   

def readassay():
  """ read the assay data files into the assay table """

  delete('rmc.assay')
  sql = 'insert into rmc.assay (%s) values %s'
  for filepath in glob.iglob('./' + rmcversion + '_assays_*.xml'):
    readfile(filepath, 'aid', dbname, sql)


def readcitation():
  """ read the citation files into the citation table """
  delete('rmc.citation')
  sql = 'insert into rmc.citation (%s) values %s'
  for filepath in glob.iglob('./' + rmcversion + '_citations_*.xml'):
    readfile(filepath, 'cid', dbname, sql)


def readdatapoint():
  """ read the datapoint files into the datapoint table """

  delete('rmc.datapoint')
  sql = 'insert into rmc.datapoint (%s) values %s'
  for filepath in glob.iglob('./' + rmcversion + '_datapoints_*.xml'):
    readfile(filepath, 'did', dbname, sql)


def readfact():
  """ read the facts file into the fact table """
  delete('rmc.fact')
  sql = 'insert into rmc.fact (%s) values %s'
  for filepath in glob.iglob('./' + rmcversion + '_facts_*.xml'):
    readfile(filepath, 'rxid', dbname, sql)


def readtarget():
    """ read the targets file into the target table
    this requires a special function because the XML is nested two
    levels deep
    """
    delete('rmc.target')
    for filepath in glob.iglob('./' + rmcversion + '_targets*.xml'):
        readtargetfile(filepath)

def readtargetfile(fname):
  """ function to read the target file and more complex XML """
  print(fname)
  sql = 'insert into rmc.target (%s) values %s'
  conn=psql.connect(user=dbname)
  tree = ET.parse(fname);
  root = tree.getroot()
  cur = conn.cursor()

  for elem in root:
     id = elem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
     id = id[id.find('#')+1:].strip()  # the number is after the pound sign
     data = {}
     data['tid'] = id
     for subelem in elem:
        prefix, has_namespace, postfix = subelem.tag.partition('}')
        if has_namespace:
            tag = postfix.strip()  # strip all namespaces
        if (tag != 'Copyright'):
           data[tag] = subelem.text

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

        columns = data.keys()
        values = [data[column] for column in columns]
        if debug:
            print (columns, values )
            print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
        else:
            cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))

  conn.commit()
  conn.close()


nl = '\n'  # newline; cound be \r\n if necessary



def readnextSDfile(file):
    """ read the next SDFile from the file of concatenated SDfiles
    return a dictionary with the SDFile tags and data, and the SDFile
    """
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



def readsdfiles(fname):
    """ read all of the individual SDFiles from the concatenated SDFile """
    print(fname)
    lg = RDLogger.logger()
    lg.setLevel(RDLogger.CRITICAL)
    count = 0
    conn=psql.connect(user=dbname)
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
     """ write a SDFile record the database """

     sql = 'insert into rmc.sdfile (%s) values %s'
     with conn.cursor() as cur:
         columns = data.keys()
         values = [data[column] for column in columns]
         if debug:
             print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
         else:
             cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))



def readsdfile():
  """ read the SDFiles. This requires special functions because this is
    not an XML file
  """
  delete('rmc.sdfile')
  for filepath in glob.iglob('./' + rmcversion + '*.sdf'):
    readsdfiles(filepath)
