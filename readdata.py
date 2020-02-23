#
# read datapoints
#
import xml.dom.minidom
import xml.etree.ElementTree as ET
import psycopg2 as psql
from psycopg2.extensions import AsIs
import glob
from version import rmcversion

def main():
  for filepath in glob.iglob('./' + rmcversion + '_datapoints_*.xml'):
    readfile(filepath)

def readfile(fname):
  print(fname)
  conn=psql.connect(user='mclark')
  tree = ET.parse(fname);
  root = tree.getroot()
  sql = 'insert into rmc.datapoint (%s) values %s'

  for elem in root:
     data = {}
     did =  elem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
     did = did[did.find('#')+1:].strip()  # the number is after the pound sign
     data['did'] = did
     for subelem in elem:
        prefix, has_namespace, postfix = subelem.tag.partition('}')
        if has_namespace:
            tag = postfix.strip()  # strip all namespaces

        if tag[0:3] == 'has':
            if (tag == 'hasCitation'):
               value = subelem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
               value = value[value.find('#')+1:].strip()  # the number is after the pound sign
               data['Citation'] = value; 
            if (tag == 'hasSubstance'):
               value = subelem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
               value = value[value.find('#')+1:].strip()  # the number is after the pound sign
               data['Substance'] = value; 
            if (tag == 'hasTarget'):
               value = subelem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
               value = value[value.find('#')+1:].strip()  # the number is after the pound sign
               data['Target'] = value; 
            if (tag == 'hasAssay'):
               value = subelem.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
               value = value[value.find('#')+1:].strip()  # the number is after the pound sign
               data['Assay'] = value; 
         
        elif (tag != 'Copyright' and tag != 'CTYPE' ):
           data[tag] = subelem.text

     with conn.cursor() as cur:
         columns = data.keys()
         values = [data[column] for column in columns]
         #print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
         cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))

  conn.commit()
  conn.close()

main()
