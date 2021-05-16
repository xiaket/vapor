#!/usr/bin/env python3
from vapor import Stack
from vapor.cfn import S3, Cloudfront
from vapor.functions import GetAtt, Join, Ref, Sub


class WebsiteS3Bucket(S3.Bucket):
    BucketName = Ref("WebsiteBucketName")
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


class OAI(Cloudfront.CloudFrontOriginAccessIdentity):
    CloudFrontOriginAccessIdentityConfig = {
        "Comment": Sub("CloudFront OAI for {aws.stack_name}")
    }


class BucketPolicy(S3.BucketPolicy):
    Bucket = WebsiteS3Bucket
    PolicyDocument = {
        "Statement": [
            {
                "Action": "s3:GetObject",
                "Effect": "Allow",
                "Resource": Sub("arn:aws:s3:::{WebsiteS3Bucket}/*"),
                "Principal": {
                    "CanonicalUser": GetAtt(OAI, "S3CanonicalUserId")
                },
            }
        ]
    }


class Distribution(Cloudfront.Distribution):
    DistributionConfig = {
        "Aliases": Ref("CloudFrontCNames"),
        "Origins": [
            {
                "DomainName": GetAtt(WebsiteS3Bucket, "RegionalDomainName"),
                "Id": "S3Origin",
                "S3OriginConfig": {
                    "OriginAccessIdentity": Join(
                        "",
                        "origin-access-identity/cloudfront/",
                        Ref(OAI),
                    )
                },
            }
        ],
        "Enabled": True,
        "HttpVersion": "http2",
        "PriceClass": "PriceClass_All",
        "DefaultCacheBehavior": {
            "AllowedMethods": ["GET", "HEAD"],
            "TargetOriginId": "S3Origin",
            "ViewerProtocolPolicy": "https-only",
            "ForwardedValues": {
                "QueryString": True,
                "Cookies": {
                    "Forward": None,
                },
            },
        },
        "ViewerCertificate": {
            "SslSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2018",
            "AcmCertificateArn": Ref("Certificate"),
        },
        "CustomErrorResponses": [
            {
                "ErrorCode": "403",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": "10",
                "ResponsePagePath": "/index.html",
            }
        ],
    }


class S3CfrStack(Stack):
    Description = ("Cloudfront Stack for websites served by cfr and s3",)
    Resources = ([WebsiteS3Bucket, OAI, BucketPolicy, Distribution],)
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
    stack = S3CfrStack()
    print(stack.yaml)
    #stack.deploy()
