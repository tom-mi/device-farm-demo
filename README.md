# device-farm-demo

Minimal demo of a CodePipeline executing Android instrumentation tests in AWS DeviceFarm

This demo includes

* Custom resources to create AWS DeviceFarm projects & device pools
* A minimal Android project with one Hello-World instrumentation test
* A CodePipeline to build the Android app and run instrumentation tests on DeviceFarm

The whole demo is deployed as 3 CloudFormation stacks.

## Prerequisites

You need

* access to an AWS account
* The AWS command-line tools

All commands shown below need to run within the context of an AWS profile, e.g. by specifying `AWS_PROFILE`.
See https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html for how to setup the AWS cli.

## Deploy the demo to your AWS account

All CloudFormation stacks are prefixed with the given prefix. This allows to deploy the demo multiple times, e.g. in a shared playground account.

```
./deploy_pipeline.sh your_prefix
```

This deploys 3 stacks:
* `your_prefix-device-farm-demo-infrastructure` Some basic infrastructure needed for later steps
* `your_prefix-device-farm-demo-resources` Custom resource lambdas
* `your_prefix-device-farm-demo-pipeline` CodePipeline ready to build & test the Android project

## Trigger the pipeline

For the sake of simplicity, the demo pipeline is triggered by uploading a `sources.zip` to S3.
The target bucket is part of the pipeline stack.

```
./push_sources.sh your_prefix
```

The pipeline should now be triggered and first build the app, then run the instrumentation tests on AWS DeviceFarm.
