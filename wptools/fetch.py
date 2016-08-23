# -*- coding:utf-8 -*-

"""
WPTools Fetch module.
"""

from __future__ import print_function

import pycurl
import sys

from . import __title__, __contact__, __version__
from io import BytesIO
from string import Template


class WPToolsFetch:

    ACTION = {
        "parse": Template((
            "https://${WIKI}/w/api.php?action=parse"
            "&contentmodel=text"
            "&disableeditsection="
            "&disablelimitreport="
            "&disabletoc="
            "&format=json"
            "&formatversion=2"
            "&page=${thing}"
            "&prop="
            "text|iwlinks|parsetree|wikitext|displaytitle|properties"
            "&redirects")),
        "query": Template((
            "https://${WIKI}/w/api.php?action=query"
            "&exintro"
            "&format=json"
            "&formatversion=2"
            "&inprop=displaytitle|url|watchers"
            "&list=random"
            "&prop=extracts|images|info|pageimages"
            "&rnlimit=1"
            "&rnnamespace=0"
            "&titles=${thing}"
            "&redirects")),
        "random": Template((
            "https://${WIKI}/w/api.php?action=query"
            "&format=json"
            "&formatversion=2"
            "&list=random"
            "&rnlimit=1"
            "&rnnamespace=0")),
        "wikidata": Template((
            "https://${WIKI}/w/api.php?action=wbgetentities"
            "&format=json"
            "&ids=${thing}"
            "&languages=${lang}"
            "&props=info|claims|descriptions|labels|sitelinks"))
    }

    timeout = 5
    title = None

    def __init__(self, lang='en', verbose=False, wiki=None):
        self.lang = lang
        self.verbose = verbose
        self.wiki = wiki or self.target()
        self.curl_setup()

    def __del__(self):
        self.cobj.close()

    def curl(self, url):
        """
        in favor of python-requests for speed
        """

        # consistently faster than requests by 3x
        #
        # r = requests.get(url,
        #                  timeout=self.TIMEOUT,
        #                  headers={'User-Agent': self.user_agent})
        # return r.text

        crl = self.cobj
        try:
            crl.setopt(crl.URL, url)
        except UnicodeEncodeError:
            crl.setopt(crl.URL, url.encode('utf-8'))
        print("%s (action=%s) %s" % (self.wiki, self.action, self.thing),
              file=sys.stderr)
        return self.curl_perform(crl)

    def curl_perform(self, crl):
        """
        performs HTTP GET and returns body of response
        """
        try:
            bfr = BytesIO()
            crl.setopt(crl.WRITEFUNCTION, bfr.write)
            crl.perform()
            info = self.curl_info(crl)
            if info:
                if self.verbose:
                    for item in sorted(info):
                        print("  %s: %s" % (item, info[item]))
                self.info = info
            body = bfr.getvalue()
            bfr.close()
            return body
        except Exception as detail:
            raise detail
            return "Caught exception: %s" % detail

    def curl_info(self, crl):
        """
        returns curl (response) info
        """
        kbps = crl.getinfo(crl.SPEED_DOWNLOAD) / 1000.0
        url = crl.getinfo(crl.EFFECTIVE_URL)
        url = url.replace("&format=json", '')
        url = url.replace("&formatversion=2", '')
        return {"url": url,
                "user-agent": self.user_agent(),
                "content": crl.getinfo(crl.CONTENT_TYPE),
                "status": crl.getinfo(crl.RESPONSE_CODE),
                "bytes": crl.getinfo(crl.SIZE_DOWNLOAD),
                "seconds": "%5.3f" % crl.getinfo(crl.TOTAL_TIME),
                "kB/s": "%3.1f" % kbps}

    def curl_setup(self):
        """
        set curl options
        """
        crl = pycurl.Curl()
        crl.setopt(crl.USERAGENT, self.user_agent())
        crl.setopt(crl.FOLLOWLOCATION, True)
        crl.setopt(crl.CONNECTTIMEOUT, self.timeout)
        self.cobj = crl

    def get(self, action, title):
        """
        returns GET result from API
        """
        obj = WPToolsFetch()
        return obj.curl(obj.query(action, title))

    def query(self, action, thing, pageid=False):
        """
        returns API query string
        """
        self.thing = thing
        self.action = action
        self.wiki = self.target(action)
        if action == 'wikidata':
            qry = self.ACTION[action].substitute(WIKI=self.wiki,
                                                 lang=self.lang,
                                                 thing=self.thing)
        else:
            qry = self.ACTION[action].substitute(WIKI=self.wiki,
                                                 thing=self.thing)
        if action == 'query' and pageid:
            qry = qry.replace('&titles=', '&pageids=')
        return qry

    def target(self, action=None):
        """
        returns target domain
        """
        if action == "wikidata":
            return "www.wikidata.org"
        return "%s.wikipedia.org" % self.lang

    def user_agent(self):
        """
        returns the wptools user-agent string
        """
        return "%s/%s (+%s)" % (__title__, __version__, __contact__)
