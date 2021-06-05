#!/usr/bin/env python3
from vapor import S3, Stack


class Bucket(S3.Bucket):
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


class S3Bucket(Bucket):
    BucketName = "website-bucket-name-o1dc0de"


class MyStack(Stack):
    Description = "Minimal stack with a single S3 bucket."
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


if __name__ == "__main__":
    res = S3Bucket()
    stack = MyStack()
    print(stack.yaml)
    print("-" * 88)
    print(stack.json)
