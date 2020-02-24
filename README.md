# RMCLoader
Create a postgresql database from Reaxys RMC data files
<br>
0. download RMC files and unzip them<br>
1. create a postgresql database<br>
2. modify database/owner name in rmc.dump file to your system<br>
3. create the tables with psql < rmc.dump <br>
4. modify dbname and rmc version in version.py<br>
5. run the program createdb.py.  This runs all of the loader for the various tables<br>
6. enjoy!

