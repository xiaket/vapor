#!/usr/bin/env python3
#from vapor import Stack
from vapor import S3


class S3Bucket(S3.Bucket):
    BucketName = "website-bucket-name-o1dc0de"
    VersionControlConfiguration = {"Status": "Enabled"}
    PublicAccessBlockConfiguration = {
        "BlockPublicAcls": True,
        "BlockPublicPolicy": True,
        "IgnorePublicAcls": True,
        "RestrictPublicBuckets": True,
    }
    BucketEncryption = {
        "ServerSideEncryptionConfiguration": [
            {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
        ]
    }


class S3BucketReal:
    def __init__(self):
        self.resource_type = "AWS::S3::Bucket"
        self.properties = {
            "BucketName": "website-bucket-name-o1dc0de",
            "VersionControlConfiguration": {"Status": "Enabled"},
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                ]
            }
        }





"""
class MyStack(Stack):
    Description = "Cloudfront Stack for websites served by cfr and s3"
    Resources = [S3Bucket]
    Parameters = {
        "WebsiteBucketName": {
            "Type": "String",
            "MaxLength": 63,
            "Description": "The bucket name",
        }
    }
    DeploymentOptions = {
        "parameters": {},
        "tags": {},
    }
"""



if __name__ == "__main__":
    res = S3Bucket()
    #stack = S3CfrStack()
    #print(stack.yaml)
    # stack.deploy()
