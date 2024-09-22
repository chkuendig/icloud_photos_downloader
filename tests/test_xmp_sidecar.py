from typing import Any, Dict
from unittest import TestCase

from icloudpd.xmp_sidecar import build_exiftool_arguments


class BuildExifToolArguments(TestCase):
    def test_build_exiftool_arguments(self) -> None:
        assetRecordStub: Dict[str,Dict[str,Any]] = {
            'fields': {
                "captionEnc": {
                    "value": "VGl0bGUgSGVyZQ==",
                    "type": "ENCRYPTED_BYTES"
                },
                "extendedDescEnc": {
                    "value": "Q2FwdGlvbiBIZXJl",
                    "type": "ENCRYPTED_BYTES"
                },
                'orientation':  {
                    "value" : 6,
                    "type" : "INT64"
                },
                'assetSubtypeV2' :  {
                    "value" : 2,
                    "type" : "INT64"
                },
                "keywordsEnc": {
                    "value": "YnBsaXN0MDChAVxzb21lIGtleXdvcmQICgAAAAAAAAEBAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAX",
                    "type": "ENCRYPTED_BYTES"
                },
                'locationEnc':  {
                    "value" :    "YnBsaXN0MDDYAQIDBAUGBwgJCQoLCQwNCVZjb3Vyc2VVc3BlZWRTYWx0U2xvbld2ZXJ0QWNjU2xhdFl0aW1lc3RhbXBXaG9yekFjYyMAAAAAAAAAACNAdG9H6P0fpCNAWL2oZnRhiiNAMtKmTC+DezMAAAAAAAAAAAgZICYqLjY6RExVXmdwAAAAAAAAAQEAAAAAAAAADgAAAAAAAAAAAAAAAAAAAHk=",
                    "type" : "ENCRYPTED_BYTES"
                },
                'assetDate' : {
                    "value" : 1532951050176,
                    "type" : "TIMESTAMP"    
                },
                'isHidden': {
                    "value" : 0,
                    "type" : "INT64"
                },
                'isDeleted':  {
                    "value" : 0,
                    "type" : "INT64"
                },
                'isFavorite':   {
                    "value" : 0,
                    "type" : "INT64"
                },  
            },
        }

        # Test full stub record
        args = build_exiftool_arguments(assetRecordStub)
        self.assertCountEqual(args , [
            '-Title=Title Here',
            '-Description=Caption Here',
            '-IPTC:keywords=some keyword',
            '-GPSAltitude=326.9550561797753',
            '-GPSLatitude=18.82285',
            '-GPSLongitude=98.96340333333333',
            '-GPSSpeed=0.0',
            '-exif:GPSDateTime=2001:01:01 00:00:00.000000',
            '-XMP-photoshop:DateCreated=2018:07:30 11:44:10.176000+00:00',
            '-CreateDate=2018:07:30 11:44:10.176000+00:00',
            '-Orientation=6'
        ])

        # Test Screenshot Tagging
        assetRecordStub['fields']['assetSubtypeV2']['value'] = 3
        args = build_exiftool_arguments(assetRecordStub)
        assert "-Make=Screenshot" in args
        assert "-DigitalSourceType=screenCapture" in args

        # Test Favorites
        assetRecordStub['fields']['isFavorite']['value'] = 1
        args = build_exiftool_arguments(assetRecordStub)
        assert "-Rating=5" in args

        # Test Deleted
        assetRecordStub['fields']['isDeleted']['value'] = 1
        args = build_exiftool_arguments(assetRecordStub)
        assert "-Rating=-1" in args

        # Test Hidden
        assetRecordStub['fields']['isDeleted']['value'] = 0
        assetRecordStub['fields']['isHidden']['value'] = 1
        args = build_exiftool_arguments(assetRecordStub)
        assert "-Rating=-1" in args
