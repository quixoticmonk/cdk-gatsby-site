from aws_cdk import (
    aws_s3 as _s3,
    aws_cloudfront as _cfront,
    aws_s3_deployment as _deployment,
    aws_cloudfront_origins as _origins,
    aws_iam as _iam
)
from aws_cdk.core import (
    Construct,
    Stack,
    RemovalPolicy,
    CfnOutput
)

from aws_cdk.aws_cloudfront import (
    Distribution,
    CfnCloudFrontOriginAccessIdentity,
    SecurityPolicyProtocol,
    PriceClass,
    BehaviorOptions,
    CachePolicy,
    AllowedMethods
)

from aws_cdk.aws_s3 import (
    Bucket,
    BucketEncryption,
)


class S3StaticSiteConstruct(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id)

        _access_logs_bucket = self.get_access_logs_bucket(stage)
        _staticsite_bucket = self.create_bucket(_access_logs_bucket, stage)
        _cfront_oai = self.create_origin_access_identity()
        _policy_statement = self.create_s3_cfront_policy(_staticsite_bucket, _cfront_oai)
        _staticsite_bucket.add_to_resource_policy(_policy_statement)

        _cfront_dist = _cfront.CloudFrontWebDistribution(
            self,
            "staticsitedistribution",
            http_version=_cfront.HttpVersion.HTTP2,
            origin_configs=[
                _cfront.SourceConfiguration(
                    behaviors=[
                        _cfront.Behavior(
                            allowed_methods=_cfront.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                            is_default_behavior=True
                        )
                    ],
                    s3_origin_source=_cfront.S3OriginConfig(
                        s3_bucket_source=_staticsite_bucket
                    ),
                )
            ],
            default_root_object="index.html",
            viewer_protocol_policy=_cfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            price_class=_cfront.PriceClass.PRICE_CLASS_ALL,
            enable_ip_v6=False,
        )

        self.bucket = _staticsite_bucket
        self.access_logs_bucket = _access_logs_bucket
        self.cfront_dist = _cfront_dist

        self.sourcebucketname = CfnOutput(self, "sourceBucketName", value=_staticsite_bucket.bucket_name)

    @property
    def main_source_bucket(self) -> _s3.IBucket:
        return self.bucket

    @property
    def main_access_logs_bucket(self) -> _s3.IBucket:
        return self.access_logs_bucket

    @property
    def main_cfront_dist(self) -> _cfront.IDistribution:
        return self.cfront_dist

    def get_access_logs_bucket(self, stage):
        return Bucket(
            self,
            "accesslogsbucket",
            bucket_name="access-logs-bucket-202104" + stage,
            encryption=BucketEncryption.KMS_MANAGED
        )

    def create_bucket(self, _access_logs_bucket: Bucket, stage):
        return Bucket(
            self,
            "S3bucket",
            bucket_name="staticsite202104" + stage,
            encryption=BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
            website_index_document="index.html",
            website_error_document="index.html",
            server_access_logs_bucket=_access_logs_bucket,
            server_access_logs_prefix="gatsbystaticsite",
            block_public_access=_s3.BlockPublicAccess(
                block_public_policy=True,
                block_public_acls=True,
                ignore_public_acls=True,
                restrict_public_buckets=True
            )
        )

    def create_origin_access_identity(self):
        return _cfront.OriginAccessIdentity(
            self,
            "oai",
            comment="Cloudfront access to S3"
        )

    @staticmethod
    def create_s3_cfront_policy(_bucket: Bucket, _cfront_oai: _cfront.OriginAccessIdentity):
        _policy_statement = _iam.PolicyStatement()
        _policy_statement.add_actions('s3:GetBucket*')
        _policy_statement.add_actions('s3:GetObject*')
        _policy_statement.add_actions('s3:List*')
        _policy_statement.add_resources(_bucket.bucket_arn)
        _policy_statement.add_resources(f"{_bucket.bucket_arn}/*")
        _policy_statement.add_canonical_user_principal(
            _cfront_oai.cloud_front_origin_access_identity_s3_canonical_user_id)
        return _policy_statement
