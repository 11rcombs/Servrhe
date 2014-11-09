from twisted.internet.defer import returnValue

config = {
    "access": "admin",
    "help": ".preview [show] (--previous) (--preview=TIME) (--mp4=DURATION) || .preview prince || Generates a preview image. TIME can be a frame number, HH:MM:SS.MM (must contain period), CHAPTER+SS.MM (chapter should match exactly), or FTP to force an ftp download."
}

def command(guid, manager, irc, channel, user, show, previous = False, preview = None, mp4 = None):
    show = manager.master.modules["showtimes"].resolve(show)

    if not show.folder.ftp:
        raise manager.exception(u"No FTP folder given for {}".format(show.name.english))

    offset = 0 if previous else 1
    episode = show.episode.current + offset

    if preview is not None:
        preview = preview.lower()

    if mp4 is True:
        mp4 = 3.0 # Defaults to 3 seconds
    elif mp4:
        try:
            mp4 = float(mp4)
        except:
            raise manager.exception(u"--mp4 must be the number of seconds the preview should last for. Got \"{}\" instead.".format(mp4))

    folder = "{}/{:02d}".format(show.folder.ftp, episode)
    manager.dispatch("update", guid, u"Caching {}".format(folder))
    yield manager.master.modules["ftp"].download(folder)

    manager.dispatch("update", guid, u"Determining last modified mkv file")
    premux = yield manager.master.modules["ftp"].getLatest(folder, "*.mkv")

    manager.dispatch("update", guid, u"Downloading {}".format(premux))
    yield manager.master.modules["ftp"].get(folder, premux, guid)

    preview = yield manager.master.modules["subs"].preview(guid, folder, premux, preview, mp4)

    if preview["text"] is not None:
        irc.msg(channel, u"Best line at given time: {}".format(preview["text"]))
    else:
        irc.msg(channel, u"No lines spoken at given time")

    irc.msg(channel, u"Preview image: {}".format(preview["link"]))

    returnValue(preview["link"])
