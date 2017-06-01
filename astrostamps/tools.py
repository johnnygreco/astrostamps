import os
from urllib.request import urlopen
from io import BytesIO
import requests
from getpass import getpass
import numpy as np
from matplotlib import image
import astropy.io.fits as fits
from astropy.visualization import make_lupton_rgb

__all__ = ["project_dir", "fetch_sdss_cutout", "HSCSession"]

project_dir = os.path.dirname(os.path.dirname(__file__))


def fetch_sdss_cutout(ra, dec, scale=0.4, width=512, height=512, opt=''):
    """Fetch SDSS color cutout image at the given ra, dec
    ra, dec : float
        in degrees
    scale : float
        pixel scale in arcseconds
    width, height : integer
        image width and height in number of pixels
        should be between 64 and 2048
    opt : str
        a set of uppercase characters for options

    Returns numpy array of (width, height, 3).
    The array can be input to matplotlib imshow for an RGB image.

    The following are available opt:

        G	Grid	Draw a N-S E-W grid through the center
        L	Label	Draw the name, scale, ra, and dec on image
        P	PhotoObj	Draw a small cicle around each primary photoObj
        S	SpecObj	Draw a small square around each specObj
        O	Outline	Draw the outline of each photoObj
        B	Bounding Box	Draw the bounding box of each photoObj
        F	Fields	Draw the outline of each field
        M	Masks	Draw the outline of each mask considered to be important
        Q	Plates	Draw the outline of each plate
        I	Invert	Invert the image (B on W)

    This will raise HTTPError if outside SDSS footprint.

    Reference
    - http://skyserver.sdss.org/dr13/en/tools/chart/chartinfo.aspx
    """
    url = ("http://skyserver.sdss.org/dr13/SkyServerWS/ImgCutout"
           "/getjpeg?ra=%.8f&dec=%.8f&scale=%.5f"
           "&width=%i&height=%i&opt=%s" % (
               ra, dec, scale, width, height, opt))
    return image.imread(urlopen(url), format='jpeg')


class HSCSession(object):
    def __init__(self, user, password=None, 
                 base_url='https://hsc-release.mtk.nao.ac.jp/'):
        self.session = requests.Session()
        self.base_url = base_url
        if password is None:
            password = getpass('Enter password: ')
        self.session.auth = (user, password)

    def fetch_hsc_cutout(self, ra, dec, width=2.0, height=2.0, band='R', imageonly=True):
        """Fetch HSC cutout image at the given ra, dec
        ra, dec : float
            in degrees
        width, height : float
            in arcseconds
        band : string of characters
            HSC band names, GRIZY
        imageonly : bool
            return images only not the entire fits hdus
        """
        band = band.upper()
        images = []
        for oneband in band:
            url = (os.path.join(self.base_url, 'das_quarry/')+"/cgi-bin/quarryImage?"
                   "ra=%.6f&dec=%.6f&sw=%.6fasec&sh=%.6fasec"
                   "&type=coadd&image=on&filter=HSC-%s&tract=&rerun=" % (
                       ra, dec, width/2.0, height/2.0, oneband))
            resp = self.session.get(url)
            if resp.ok:
                images.append(fits.open(BytesIO(resp.content)))
        if imageonly:
            images = np.dstack([hdu[1].data for hdu in images])
        return images

    def make_rgb_image(self, ra=None, dec=None, width=2.0, height=2.0, band='irg', 
                       stretch=5, Q=8, images=None):
        """
        Make RGB image.

        Parameters
        ----------
        ra, dec : float
            in degrees
        width, height : float
            in arcseconds
        band : string of characters
            HSC band names for in RGB order
        stretch : float
            Linear stretch of HSC RGB image
        Q : float
            The asinh softening parameter for HSC RGB image
        images : ndarray
            If not None, will make rgb image using these images

        Returns
        -------
        rgb : ndarry
            The RGB image
        """
        if images is None:
            images = self.fetch_hsc_cutout(ra, dec, width, height, band)
        rgb = make_lupton_rgb(images[:, :, 0], images[:, :, 1],
                              images[:, :, 2], stretch=stretch, Q=Q)
        return rgb
