from twisted.internet.defer import returnValue
from twisted.internet.utils import getProcessOutputAndValue
import os, re

config = {
    "access": "superadmin",
    "help": ".update || .update || Pulls in latest changes from github.",
}

def command(guid, manager, irc, channel, user):
    manager.dispatch("update", guid, u"Updating Git repository")
    out, err, code = yield getProcessOutputAndValue(manager.master.modules["utils"].getPath("git"), args=["pull"], env=os.environ)
    if code != 0:
        manager.log(out)
        manager.log(err)
        raise manager.exception(u"Aborted updating: Couldn't pull from github")

    # Reload everything but IRC so the bot doesn't flicker
    manager.dispatch("update", guid, u"Reloading modules")
    yield manager.master.loadModules(["irc"], True)