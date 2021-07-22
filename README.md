# RMCLoader
Create a postgresql database from Reaxys RMC data files.<br>
Access to the RMC data files is by licence from Elsevier.
<br>
requires RDkit to convert the SDfiles into SMILES strings
<br><br>
1. download RMC files from Elsevier. Do not uncompress<br>
4. modify dbname in readrmcfiles.py<br>
5. run readrmcfiles.py, it will create the database, load the files, and apply indices<br>
6. enjoy!<br>

