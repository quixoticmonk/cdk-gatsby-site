from aws_cdk.core import Construct, Stage, Environment, Stack
from aws_cdk import aws_s3 as _s3
from .s3_cloudfront_construct import S3StaticSiteConstruct


class ApplicationStage(Stage):
    def __init__(self, scope: Construct, id: str, stage: str,
                 env: Environment, asset_bucket: _s3.Bucket , **kwargs):
        super().__init__(scope, id, **kwargs)

        AppStack(self, id, stage, env=env, asset_bucket=asset_bucket)


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, asset_bucket: _s3.Bucket,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        S3StaticSiteConstruct(self, "staticsite",asset_bucket)
