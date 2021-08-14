# vapor

![build](https://github.com/xiaket/vapor/workflows/build/badge.svg)
![PyPI version](https://badge.fury.io/py/vapor.svg)
![Coverage](https://coveralls.io/repos/github/xiaket/vapor/badge.svg)
![license](https://img.shields.io/pypi/l/vapor)

**Vapor** is a library that was designed to replace CDK.

```python
#!/usr/bin/env python3
from vapor import S3, Stack, Ref


class Bucket(S3.Bucket):
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
    BucketName = Ref("WebsiteBucketName")


class WebsiteStack(Stack):
    Description = "Minimal stack with a single S3 bucket."
    Resources = [S3Bucket]
    Parameters = {
        "WebsiteBucketName": {
            "Type": "String",
            "MaxLength": 63,
        }
    }
    DeploymentOptions = {
        "parameters": {},
        "tags": {},
    }


if __name__ == "__main__":
    stack = WebSiteStack()
    stack.deploy()
```

You'll construct you Cloudformation resources/stack as Python classes(thus have all the flexibility of Python), define the deployment options in the stack class, then you can simply deploy the stack with a simple deploy call. Please see [examples](/examples) directory for more examples.

## Notable features

- Generate clean json/yaml templates
- Import existing Cloudformation templates to be a Python script.
- Integration with cfn-lint.
- Nice cloudformation events during deployment.
- Easy to do inheritance so as to enforce organisational security policies.

## Installation

vapor is available on PyPI:

```console
$ python -m pip install vapor
```

You'll need to have Python 3.9+ to use all features in vapor.

## Documentation

- [getting started guide](/doc/getting_started.md)
- [defining resource](/doc/resource.md)
- [use cfn functions](/doc/cfn-functions.md)
- [defining stack](/doc/stack.md)
- [deployment options](/doc/deployment_options.md)
- [cfn-lint](/doc/cfn-lint.md)
- [create hooks](/doc/hooks.md)
- [examples](/examples)

## Contribute

Please use Github Issues/Pull requests to contribute to the project. Please consult [How to setup and run tests](/doc/development.md)

## License

This project is licensed under the MIT license.
