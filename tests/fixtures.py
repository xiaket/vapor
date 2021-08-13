#!/usr/bin/env python3
"""
Fixtures used in tests
"""

COMPLEX_RESOURCE = {
    "Type": "AWS::S3::Bucket",
    "Properties": {
        "BucketName": {
            "Fn::Join": [
                "/",
                [
                    "private-app-example.com",
                    {"Fn::Sub": "${Environment}-suffix"},
                    {
                        "Fn::Select": [
                            "3",
                            {"Fn::Split": ["-", {"Ref": "Namespace"}]},
                        ]
                    },
                    {
                        "Fn::Select": [
                            "0",
                            {"Fn::GetAZs": {"Ref": "AWS::Region"}},
                        ]
                    },
                    "system-logs",
                ],
            ]
        }
    },
}

SIMPLE_JSON = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {
        "Bucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": "test",
                "VersioningConfiguration": {"Status": "Suspended"},
            },
        }
    },
}

SIMPLE_YAML = """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Bucket:
    Type: "AWS::S3::Bucket"
    Properties:
      BucketName: test
      VersioningConfiguration:
        Status: Suspended
"""

SIMPLE_OUTPUT = '''
#!/usr/bin/env python3
"""
Generated stack definition for {filename}.
"""
from vapor import Stack, Ref, Fn, S3


class Bucket(S3.Bucket):
    BucketName = 'test'
    VersioningConfiguration = {{'Status': 'Suspended'}}


# Please change the name of the class
class VaporStack(Stack):
    Resources = [Bucket]
    AWSTemplateFormatVersion = '2010-09-09'
'''
