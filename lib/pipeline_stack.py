import json

from aws_cdk import (
    core,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_codecommit as codecommit,
    aws_iam as iam,
    pipelines,
)

from aws_cdk.core import (
    Environment,
    Stack,
    Construct
)

from aws_cdk.aws_codebuild import (
    BuildEnvironment,
    ComputeType,
    LinuxBuildImage
)

from .application_stage import ApplicationStage

_env_non_prod = Environment(account="xxxxx", region="us-east-1")


class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 project_cfg: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        _source_artifact = codepipeline.Artifact()
        _cloud_assembly_artifact = codepipeline.Artifact()
        _repo_dict = dict(self.node.try_get_context("repo"))
        _pipeline_dict = dict(self.node.try_get_context("pipeline"))
        _create_roles = ''
        _synth_accounts = ''

        _additional_policy = self.setup_additional_policy(
            _create_roles,
            _synth_accounts,
            project_cfg
        )
        _repo = self.create_codecommit_repo(_repo_dict)
        _source_action = self.create_source_action(
            _repo,
            _source_artifact
        )
        _synth_action = self.create_synth_action(
            _source_artifact,
            _cloud_assembly_artifact,
            _create_roles,
            _synth_accounts,
            _additional_policy
        )
        _pipeline = self.create_pipeline(_pipeline_dict, _cloud_assembly_artifact,
                                         _source_action, _synth_action)

        self.add_application_stage(_pipeline, "dev",
                                   project_cfg['Deployment']['dev']['VpcId'], _env_non_prod)

        self.repo = _repo

    @property
    def main_repo(self) -> codecommit.IRepository:
        return self.repo

    @staticmethod
    def create_synth_action(_source_artifact, _cloud_assembly_artifact,
                            _create_roles, _synth_accounts, additional_policy):
        return pipelines.SimpleSynthAction(
            source_artifact=_source_artifact,
            cloud_assembly_artifact=_cloud_assembly_artifact,
            install_command='npm install -g aws-cdk' + _create_roles,
            build_command="pip install -r requirements.txt",
            synth_command='cdk synth' + _synth_accounts +
                          ' && cp cdk.json cdk.out',
            role_policy_statements=additional_policy,
            environment=BuildEnvironment(
                privileged=True,
                compute_type=ComputeType.LARGE,
                build_image=LinuxBuildImage.STANDARD_5_0
            )
        )

    @staticmethod
    def create_source_action(_repo, _source_artifact):
        return cpactions.CodeCommitSourceAction(
            branch='master',
            repository=_repo,
            output=_source_artifact,
            action_name="Checkout",
            code_build_clone_output=True,
        )

    def create_codecommit_repo(self, _repo_dict):
        return codecommit.Repository(
            self,
            _repo_dict["repo_name"],
            repository_name=_repo_dict["repo_name"],
            description=_repo_dict["repo_desc"]
        )

    @staticmethod
    def setup_additional_policy(_create_roles, _synth_accounts, project_cfg):
        with open('cdk.json') as cdk_json:
            cdk = json.load(cdk_json)

        bootstrap = cdk['context']['@aws-cdk/core:bootstrapQualifier']

        _profiles = open('.aws/config', 'w')
        for name, account in project_cfg['Deployment'].items():
            _bootstrap_role = f"cdk-{bootstrap}-cfn-exec-role-{account['AccountNumber']}-{account['Region']}"
            _create_roles += f" && aws configure set role_arn arn:aws:iam::{account['AccountNumber']}:role/{_bootstrap_role} --profile {name}"
            _create_roles += f" && aws configure set region {account['Region']} --profile {name}"
            _create_roles += f" && aws configure set credential_source Ec2InstanceMetadata --profile {name}"

            _synth_accounts += f" && cdk synth --profile {name}"

        _profiles.close()

        _pipeline_synth_cfg = project_cfg['Pipeline']['Synth']

        additional_policy = []
        if 'AdditionalPolicy' in _pipeline_synth_cfg.keys():
            for statement in _pipeline_synth_cfg['AdditionalPolicy']:
                if statement['effect'] == 'ALLOW':
                    effect = iam.Effect.ALLOW
                else:
                    effect = iam.Effect.DENY

                additional_policy.append(
                    iam.PolicyStatement(actions=statement['actions'],
                                        resources=statement['resources'],
                                        effect=effect))

        return additional_policy

    def create_pipeline(self, _pipeline_dict, _cloud_assembly_artifact, _source_action, _synth_action):
        return pipelines.CdkPipeline(
            self,
            _pipeline_dict["pipeline_name"],
            pipeline_name=_pipeline_dict["pipeline_name"],
            cloud_assembly_artifact=_cloud_assembly_artifact,
            self_mutating=True,
            source_action=_source_action,
            synth_action=_synth_action
        )

    def add_application_stage(self, _pipeline, stage, vpc_id, env):
        _pipeline.add_application_stage(
            ApplicationStage(
                self,
                "staticsiteDeploymentDev",
                stage,
                vpc_id,
                env=env),
            manual_approvals=True
        )
