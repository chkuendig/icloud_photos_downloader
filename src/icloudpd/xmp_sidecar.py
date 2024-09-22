"""Generate XMP sidecar file from photo asset record"""

from __future__ import annotations

import base64
import logging
import plistlib
from datetime import datetime
from typing import Any

import dateutil.tz
from exiftool import ExifToolHelper

exif_tool = None
def init_exiftool(logger: logging.Logger) -> None:
    """Initialize ExifTool"""
    global exif_tool
    if not exif_tool:
        try:
            exif_tool = ExifToolHelper(logger=logging.getLogger(__name__))
        except FileNotFoundError as err:
            logger.warning(err)
            logger.warning("XMP sidecar files will not be generated")
    else: 
        raise Exception("ExifTool already initialized") 

def build_exiftool_arguments(asset_record: dict[str, Any]) -> list[str]:
    xmp_metadata: dict[str, str|int] = {}
    if 'captionEnc' in asset_record['fields']:
        xmp_metadata['Title'] = base64.b64decode(asset_record['fields']['captionEnc']['value']).decode('utf-8')
    if 'extendedDescEnc' in asset_record['fields']:
        xmp_metadata['Description'] = base64.b64decode(asset_record['fields']['extendedDescEnc']['value']).decode('utf-8')
    if 'orientation' in asset_record['fields']:
        xmp_metadata['Orientation'] = asset_record['fields']['orientation']['value']
    if 'assetSubtypeV2' in asset_record['fields'] and int(asset_record['fields']['assetSubtypeV2']['value']) == 3:
        xmp_metadata["Make"] = "Screenshot"
        xmp_metadata["DigitalSourceType"] = "screenCapture"
    if 'keywordsEnc' in asset_record['fields']:
        keywords = plistlib.loads(base64.b64decode(asset_record['fields']['keywordsEnc']['value']), fmt=plistlib.FMT_BINARY)
        if(len(keywords) > 0):
            xmp_metadata["IPTC:keywords"] = ",".join(keywords)
    if 'locationEnc' in asset_record['fields']:
        locationDec = plistlib.loads(base64.b64decode(asset_record['fields']['locationEnc']['value']), fmt=plistlib.FMT_BINARY)
        if('alt' in locationDec):
            xmp_metadata["GPSAltitude"] = locationDec['alt']
        if('lat' in locationDec):
            xmp_metadata["GPSLatitude"] = locationDec['lat']
        if('lon' in locationDec):
            xmp_metadata["GPSLongitude"] = locationDec['lon']
        if('speed' in locationDec):
            xmp_metadata["GPSSpeed"] = locationDec['speed']
        if('timestamp' in locationDec and isinstance(locationDec['timestamp'], datetime)):
            xmp_metadata["exif:GPSDateTime"] = locationDec['timestamp'].strftime("%Y:%m:%d %H:%M:%S.%f%z")
    if 'assetDate' in asset_record['fields']:
        timeZoneOffset = 0
        if timeZoneOffset in asset_record['fields']:
            timeZoneOffset = int(asset_record['fields']['timeZoneOffset']['value'])
        assetDate = datetime.fromtimestamp(int(asset_record['fields']['assetDate']['value'])/1000,tz=dateutil.tz.tzoffset(None, timeZoneOffset))
        assetDateString = assetDate.strftime("%Y:%m:%d %H:%M:%S.%f%z")
        assetDateString = f"{assetDateString[:-2]}:{assetDateString[-2:]}" # Add a colon to timezone offset
        xmp_metadata["XMP-photoshop:DateCreated"] = assetDateString # Apple Photos uses this field when exporting an XMP sidecar
        xmp_metadata["CreateDate"] = assetDateString
    # Hidden or Deleted Photos should be marked as rejected (needs running as --album "Hidden" or --album "Recently Deleted")
    if (('isHidden' in asset_record['fields'] and asset_record['fields']['isHidden']['value'] == 1) or 
        ('isDeleted' in asset_record['fields'] and   asset_record['fields']['isDeleted']['value'] == 1)): 
        # -1 means rejected: https://www.iptc.org/std/photometadata/specification/IPTC-PhotoMetadata#image-rating 
        xmp_metadata["Rating"] = -1 
    elif asset_record['fields']['isFavorite']['value'] == 1: #only mark photo as favorite if not hidden or deleted
        xmp_metadata["Rating"] = 5
    
    args = ["-" + k + "=" + str(xmp_metadata[k]) for k in xmp_metadata]
    return args

def generate_xmp_file(logger: logging.Logger, download_path: str, asset_record: dict[str, Any]) -> None:
    """Generate XMP sidecar file from photo asset record"""
    if exif_tool:
        args = build_exiftool_arguments(asset_record)
        # json.dump(asset_record['fields'], open(download_path+".ar.json", "w"), indent=4)
        exif_tool.execute("-overwrite_original", download_path+".xmp", *args)
