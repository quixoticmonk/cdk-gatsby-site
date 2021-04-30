from aws_cdk.core import Construct, Stage, Environment, Stack
from .s3_cloudfront_construct import S3StaticSiteConstruct


class ApplicationStage(Stage):
    def __init__(self, scope: Construct, id: str, stage: str,
                 env: Environment, **kwargs):
        super().__init__(scope, id, **kwargs)

        AppStack(self, id, stage, env=env)


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        S3StaticSiteConstruct(self, "staticsite")
