# -*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import CookieAgent, FileBodyProducer
from twisted.web.http_headers import Headers
from StringIO import StringIO
import cookielib, os, random, re, urllib

dependencies = ["config", "commands", "utils", "multipart"]

class Module(object):
    def __init__(self, master):
        self.master = master
        self.config = master.modules["config"].interface("nyaa")
        self.codes =  {
            418: "I'm a teapot (You're doing it wrong)",
            460: "Missing Announce URL",
            461: "Already Exists",
            462: "Invalid File",
            463: "Missing Data",
            520: "Configuration Broken"
        }

    def stop(self):
        pass

    @inlineCallbacks
    def upload(self, folder, filename):
        exception = self.master.modules["commands"].exception
        user = yield self.config.get("user")
        passwd = yield self.config.get("pass")
        twitters = yield self.config.get("twitter", {"jdp": "johnnydickpants"})
        nyaagent = CookieAgent(self.master.agent, cookielib.CookieJar())

        if user is None or passwd is None:
            raise exception(u"No NT username or password in config")

        response = yield nyaagent.request("POST","http://www.nyaa.se/?page=login",
            Headers({'Content-Type': ['application/x-www-form-urlencoded']}),
            FileBodyProducer(StringIO(urllib.urlencode({"method": "1", "login": user,"password": passwd}))))

        body = yield self.master.modules["utils"].returnBody(response)
        if "Login successful" not in body:
            raise exception(u"Couldn't login to Nyaa.")

        name, twitter = random.choice(twitters.items())
        twitter_list = self.master.modules["utils"].rheinbowify('[b]Follow [u][url="https://twitter.com/RHExcelion"]@RHExcelion[/url][/u], [u][url="https://twitter.com/{}"]@{}[/url][/u], and the rest of Commie at [u][url="https://twitter.com/RHExcelion/commie-devs"]@Commie-Devs[/url][/u].[/b]'.format(twitter, name))

        post_data = self.master.modules["multipart"].MultiPartProducer({"torrent": os.path.join(folder, filename)},{
            "name": filename,
            "catid": "1_37",
            "info": "#commie-subs@irc.rizon.net",
            "description": "Visit us at [url]http://commiesubs.com[/url] for the latest updates and news.\n{}".format(twitter_list),
            "remake": "0",
            "anonymous": "0",
            "hidden": "0",
            "rules": "1",
            "submit": "Upload"
        })

        response = yield nyaagent.request("POST","http://www.nyaa.se/?page=upload", Headers({'Content-Type': ['multipart/form-data; boundary={}'.format(post_data.boundary)]}), post_data)
        if response.code != 200:
            raise exception(u"Couldn't upload torrent to Nyaa. Error #{:d}: {}".format(response.code, self.codes[response.code]))

        body = yield self.master.modules["utils"].returnBody(response)
        match = re.search("http://www.nyaa.se/\?page=view&#38;tid=[0-9]+", body)
        if not match:
            raise exception(u"Couldn't find torrent link in Nyaa's response.")

        info_link = match.group(0).replace("&#38;","&")
        download_link = info_link.replace("view","download")

        returnValue((info_link, download_link))
