#
# read facts
#
import xml.dom.minidom
import xml.etree.ElementTree as ET
import psycopg2 as psql
from psycopg2.extensions import AsIs
import glob
from version import rmcversion

def main():
  for filepath in glob.iglob('./' + rmcversion + '_facts_*.xml'):
    readfile(filepath)

def readfile(fname):
  print(fname)
  conn=psql.connect(user='mclark')
  tree = ET.parse(fname);
  root = tree.getroot()
  sql = 'insert into rmc.fact (%s) values %s'
  for elem in root:
     id = elem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
     id = id[id.find('#')+1:].strip()  # the number is after the pound sign
     data = {}
     data['rxid'] = id
     for subelem in elem:
        prefix, has_namespace, postfix = subelem.tag.partition('}')
        if has_namespace:
            tag = postfix.strip()  # strip all namespaces
        if (tag != 'Copyright'):
           data[tag] = subelem.text.strip()
     with conn.cursor() as cur:
         columns = data.keys()
         values = [data[column] for column in columns]
         #print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
         cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))

  conn.commit()
  conn.close()

main()
