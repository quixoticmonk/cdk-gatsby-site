from aws_cdk.core import Construct, Stage, Environment, Stack
from aws_cdk import aws_s3 as _s3
from .s3_cloudfront_construct import S3StaticSiteConstruct


class ApplicationStage(Stage):
    def __init__(self, scope: Construct, id: str, stage: str,
                 env: Environment, **kwargs):
        super().__init__(scope, id, **kwargs)

        stack = AppStack(self, id, stage, env=env)

        self.sourceBucketName = stack.sourceBucketName


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        staticsite = S3StaticSiteConstruct(self, "staticsite")

        self.sourceBucketName = staticsite.sourcebucketname
