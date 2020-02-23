#
# read targets
#
import xml.dom.minidom
import xml.etree.ElementTree as ET
import psycopg2 as psql
from psycopg2.extensions import AsIs
import glob
from version import rmcversion

def main():
    for filepath in glob.iglob('./' + rmcversion + '_targets*.xml'):
        readfile(filepath)

def readfile(fname):
  print(fname)
  conn=psql.connect(user='mclark')
  tree = ET.parse(fname);
  root = tree.getroot()
  sql = 'insert into rmc.target (%s) values %s'
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
           data[tag] = subelem.text.strip()

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


     with conn.cursor() as cur:
         columns = data.keys()
         values = [data[column] for column in columns]
         #print(cur.mogrify(sql, (AsIs(','.join(columns)), tuple(values))))
         cur.execute(sql, (AsIs(','.join(columns)), tuple(values)))

  conn.commit()
  conn.close()

main()
