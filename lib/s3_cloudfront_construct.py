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
    RemovalPolicy
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
    BlockPublicAccess
)


class S3StaticSiteConstruct(Stack):
    def __init__(self, scope: Construct, construct_id: str, asset_bucket: _s3.Bucket,
                 **kwargs) -> None:
        super().__init__(scope, construct_id)

        _access_logs_bucket = self.get_access_logs_bucket()
        _staticsite_bucket = self.create_bucket(_access_logs_bucket)
        _bucket_origin = _origins.S3Origin(_staticsite_bucket)
        _cfront_oai = self.create_origin_access_identity()
        _cfront_behavior_options = self.create_behavior_options(_bucket_origin)
        _cfront_dist = self.create_distribution(_cfront_behavior_options, _access_logs_bucket)

        _staticsite_bucket.add_to_resource_policy(
            self.create_s3_cfront_policy(_staticsite_bucket, _cfront_oai))

        _deployment.BucketDeployment(
            self,
            "bucketdeployment",
            destination_bucket=_staticsite_bucket,
            destination_key_prefix="",
            sources=[_deployment.Source.bucket(bucket=asset_bucket)],
            retain_on_delete=False,
            distribution=_cfront_dist,
            distribution_paths=["*"],
            prune=True,
        )

        # self.create_deployment(_staticsite_bucket, _cfront_dist, "*")

        self.bucket = _staticsite_bucket
        self.access_logs_bucket = _access_logs_bucket
        self.cfront_dist = _cfront_dist

    @property
    def main_source_bucket(self) -> _s3.IBucket:
        return self.bucket

    @property
    def main_access_logs_bucket(self) -> _s3.IBucket:
        return self.access_logs_bucket

    @property
    def main_cfront_dist(self) -> _cfront.IDistribution:
        return self.cfront_dist

    def get_access_logs_bucket(self):
        return Bucket(
            self,
            "accesslogsbucket",
            bucket_name="access-logs-bucket-202104",
            encryption=BucketEncryption.KMS_MANAGED
        )

    def create_bucket(self, _access_logs_bucket: Bucket):
        return Bucket(
            self,
            "S3bucket",
            bucket_name="staticsite202104",
            encryption=BucketEncryption.KMS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
            website_index_document="index.html",
            website_error_document="index.html",
            block_public_access=BlockPublicAccess.BLOCK_ALL,
            server_access_logs_bucket=_access_logs_bucket,
            server_access_logs_prefix="gatsbystaticsite"
        )

    def create_origin_access_identity(self):
        return CfnCloudFrontOriginAccessIdentity(
            self,
            "oai",
            cloud_front_origin_access_identity_config={
                "comment": "cloudfront access to S3"
            }
        )

    @staticmethod
    def create_behavior_options(_bucket_origin):
        return BehaviorOptions(
            allowed_methods=AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            cache_policy=CachePolicy.CACHING_OPTIMIZED,
            origin=_bucket_origin
        )

    def create_distribution(self, _cfront_behavior_options: BehaviorOptions, _access_logs_bucket: Bucket):
        return Distribution(
            self,
            "staticsitedistribution",
            default_behavior=_cfront_behavior_options,
            enabled=True,
            enable_logging=True,
            enable_ipv6=True,
            minimum_protocol_version=SecurityPolicyProtocol.TLS_V1_2_2019,
            price_class=PriceClass.PRICE_CLASS_ALL,
            default_root_object="",
            comment="",
            log_bucket=_access_logs_bucket,
            log_includes_cookies=False,
            log_file_prefix="cfront-staticsite",
            # web_acl_id="",
            # certificate=,
            # geo_restriction=_cfront.GeoRestriction
        )

    @staticmethod
    def create_s3_cfront_policy(
            _bucket: Bucket, _cfront_oai: CfnCloudFrontOriginAccessIdentity):
        _policy_statement = _iam.PolicyStatement()
        _policy_statement.add_actions('s3:GetBucket*')
        _policy_statement.add_actions('s3:GetObject*')
        _policy_statement.add_actions('s3:List*')
        _policy_statement.add_resources(_bucket.bucket_arn)
        _policy_statement.add_resources(f"{_bucket.bucket_arn}/*")
        _policy_statement.add_canonical_user_principal(
            _cfront_oai.attr_s3_canonical_user_id)
        return _policy_statement

    def create_deployment(
            self, dest_bucket: Bucket,
            distribution: Distribution, distribution_path: str):
        return _deployment.BucketDeployment(
            self,
            "bucketdeployment",
            destination_bucket=dest_bucket,
            destination_key_prefix="",
            sources=[_deployment.Source.asset("")],
            retain_on_delete=False,
            distribution=distribution,
            distribution_paths=[distribution_path],
            prune=True,
        )
