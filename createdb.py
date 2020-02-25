#
# impott the set of RMC files into a postgres database.
# this assumes that the current directory is the one with the file set.
#
# TODO: enhance so one does not have to unzip the files first
#
import readrmcfiles as rmc


rmc.readassay()
rmc.readcitation()
rmc.readdatapoint()
rmc.readfact()
rmc.readtarget()
rmc.readsdfile()
