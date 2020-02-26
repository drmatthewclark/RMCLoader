#
# impott the set of RMC files into a postgres database.
# this assumes that the current directory is the one with the file set.
#
# reads the unzipped gz file as supplied by Elsevier
#
import readrmcfiles as rmc


rmc.readassay()
rmc.readcitation()
rmc.readdatapoint()
rmc.readfact()
rmc.readtarget()
rmc.readsdfile()
