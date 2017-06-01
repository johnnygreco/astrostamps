import os
from urllib.request import urlopen
from io import BytesIO
import requests
from getpass import getpass
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np
from matplotlib import image
import astropy.io.fits as fits
from astropy.wcs import WCS
from astropy.visualization import make_lupton_rgb

__all__ = ["project_dir", "fetch_sdss_cutout", "HSCSession", "fetch_galex_cutout"]

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


def fetch_galex_cutout(ra, dec, size=50, survey='AIS'):
    """
    Fetch Galex NUV+FUV cutout image.

    Parameters
    ----------
    ra, dec : float
        Center of cutout in degress
    size : float
        Size of cutout in arcsec
    survey : str
        Galex survey (AIS, MIS, DIS, NGS, GII)

    Returns
    -------
    cutout : PIL.Image.Image
        The cutout image

    Notes
    -----
    - adapted from script by https://github.com/wschoenell
    (https://gist.github.com/wschoenell/ea27e28f271da9b472e51e890b9477ba)
    """
    pixscale = 1.5 # arcsec/pixel
    url = 'http://galex.stsci.edu/gxWS/SIAP/gxSIAP.aspx?POS={},{}&SIZE=0'.format(ra, dec)
    req = requests.request('GET', url)
    data = ET.XML(req.content)
    VOTab = '{http://www.ivoa.net/xml/VOTable/v1.1}'
    resource = data.find(VOTab+'RESOURCE')
    table = resource.find(VOTab+'TABLE').find(VOTab+'DATA').find(VOTab+'TABLEDATA')
    survey_idx = np.argwhere(np.array([t[0].text for t in table])==survey)
    if len(survey_idx)==0:
        print('**** No {} image found at {} {} ****'.format(survey, ra, dec))
        return None
    fits_url = table[survey_idx[0][0]][20].text
    wcs = WCS(fits.getheader(fits_url))
    x, y = wcs.wcs_world2pix(ra, dec, 0)
    jpg_url = table[survey_idx[-1][0]][20].text
    crop_pix = np.floor(size/pixscale/2.0)
    crop = (x - crop_pix, y - crop_pix, x + crop_pix, y + crop_pix)  
    jpg_img = Image.open(BytesIO(requests.request('GET', jpg_url).content))    
    return jpg_img.transpose(Image.FLIP_TOP_BOTTOM).crop(crop)      
