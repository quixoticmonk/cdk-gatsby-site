#!/usr/bin/env python3

from aws_cdk import core as cdk
from lib.pipeline_stack import PipelineStack

import json
import yaml

with open('config/project.yaml') as project_cfg_yaml:
    _project_cfg = yaml.load(project_cfg_yaml, Loader=yaml.FullLoader)

_env_non_prod = cdk.Environment(account="xxxx", region="us-east-1")

app = cdk.App()

with open('./tags.json', 'r') as file:
    tags = json.loads(file.read())

for key, value in tags.items():
    cdk.Tags.of(app).add(key, value)

PipelineStack(app,
              'staticapppipelinestack',
              project_cfg=_project_cfg,
              env=_env_non_prod)

app.synth()
