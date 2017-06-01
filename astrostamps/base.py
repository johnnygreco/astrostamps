from io import BytesIO
import abc
import six
import requests


@six.add_metaclass(abc.ABCMeta)
class StampFactory(object):

    """A base class for collecting stamps"""
    baseurl = None

    def __init__(self, *args, **kwargs):
        self.session = requests.Session()

    def _download(self, params):
        r = self.session.get(self.baseurl, params=params)
        if r.ok:
            return BytesIO(r.content)
        else:
            r.raise_for_status()

    @abc.abstractmethod
    def fetch(self, input):
        return NotImplementedError("")

    @abs.abstractmethod
    def make_rgb_image(self, input):
        return NotImplementedError("")


class SDSS(StampFactory):
    baseurl = "http://skyserver.sdss.org/dr13/SkyServerWS/ImgCutout/getjpeg?"
    def fetch(self, ra, dec, size):
        params = dict(ra=ra, dec=dec, width=size, height=size)
        # return image