#!/usr/bin/env python3
import unittest

from vapor import S3, Stack


class TestResource(unittest.TestCase):
    def setUp(self):
        self.cls = type(
            "Bucket",
            (S3.Bucket,),
            {
                "BucketName": "test",
                "VersionControlConfiguration": {"Status": "Enabled"},
            },
        )
        self.resource = self.cls()
        self.stack = type(
            "TestStack",
            (Stack,),
            {
                "Resources": [
                    self.cls,
                ],
                "Description": "Minimal stack with a single S3 bucket.",
            },
        )()

    def test_resource_attrs(self):
        self.assertEqual(self.resource.resource_type, "AWS::S3::Bucket")
        self.assertEqual(self.resource.BucketName, "test")
        self.assertEqual(
            self.resource.VersionControlConfiguration, {"Status": "Enabled"}
        )
        self.assertEqual(self.resource.logical_name, "Bucket")
        self.assertEqual(
            self.resource.properties,
            {
                "BucketName": "test",
                "VersionControlConfiguration": {"Status": "Enabled"},
            },
        )
        self.assertEqual(
            self.resource.template,
            {
                "Bucket": {
                    "Properties": {
                        "BucketName": "test",
                        "VersionControlConfiguration": {"Status": "Enabled"},
                    },
                    "Type": "AWS::S3::Bucket",
                }
            },
        )

    def test_resource_inheritance(self):
        self.child = type(
            "S3Bucket",
            (self.cls,),
            {
                "BucketName": "test-again",
            },
        )
        self.res = self.child()
        self.assertEqual(self.res.resource_type, "AWS::S3::Bucket")
        self.assertEqual(self.res.BucketName, "test-again")
        self.assertEqual(self.res.VersionControlConfiguration, {"Status": "Enabled"})
        self.assertEqual(self.res.logical_name, "S3Bucket")
        self.assertEqual(
            self.res.properties,
            {
                "BucketName": "test-again",
                "VersionControlConfiguration": {"Status": "Enabled"},
            },
        )
        self.assertEqual(
            self.res.template,
            {
                "S3Bucket": {
                    "Properties": {
                        "BucketName": "test-again",
                        "VersionControlConfiguration": {"Status": "Enabled"},
                    },
                    "Type": "AWS::S3::Bucket",
                }
            },
        )

    def test_stack(self):
        self.assertEqual(
            self.stack.template,
            {
                "AWSTemplateFormatVersion": "2010-09-09",
                "Resources": [
                    {
                        "Bucket": {
                            "Properties": {
                                "BucketName": "test",
                                "VersionControlConfiguration": {"Status": "Enabled"},
                            },
                            "Type": "AWS::S3::Bucket",
                        }
                    }
                ],
            },
        )
