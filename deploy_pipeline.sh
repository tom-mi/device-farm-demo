#!/bin/bash

set -eu

BUILD_DIR=lambda_build

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <prefix>"
    exit 1
fi

PREFIX=$1

if [[ -d ${BUILD_DIR} ]]; then
    rm -r "${BUILD_DIR}"
fi

mkdir -p "${BUILD_DIR}/test"

(
    unset "${!AWS_@}"

    for pkg in "device-farm-project-resource"; do
        echo "Testing ${pkg}"
        test_target="${BUILD_DIR}/test/${pkg}"
        cp -r ${pkg} ${test_target}
        pushd ${test_target}

                pipenv clean
                pipenv install --dev
                pipenv run pip install --quiet --editable .
                pipenv run pytest --quiet
        popd
        echo "Packaging $pkg"
        pushd ${pkg}
            target="../${BUILD_DIR}/build/${pkg}"
            mkdir -p ${target}
            pipenv lock --requirements > ${target}/requirements.txt
            pipenv run pip install --quiet --target ${target} --requirement ${target}/requirements.txt
            pipenv run pip install --quiet --target ${target} .
        popd
    done
)

infrastructure_stack_name="${PREFIX}-device-farm-demo-infrastructure"
echo "Deploying infrastructure to ${infrastructure_stack_name}"

aws cloudformation deploy \
    --template-file pipeline/infrastructure.yaml \
    --stack-name ${infrastructure_stack_name} \
    --no-fail-on-empty-changeset \
    --parameter-overrides "Prefix=${PREFIX}"

lambda_artifacts_bucket=$(aws cloudformation describe-stacks \
    --output text \
    --stack-name ${infrastructure_stack_name} \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaArtifactsBucket`].OutputValue')

echo "Packaging device-farm custom resource lambdas"
aws cloudformation package \
    --template-file pipeline/resources.yaml \
    --output-template-file lambda_build/resources.yaml \
    --s3-bucket ${lambda_artifacts_bucket}

resources_stack_name="${PREFIX}-device-farm-demo-resources"
echo "Deploying resources to ${resources_stack_name}"
aws cloudformation deploy \
    --template-file lambda_build/resources.yaml \
    --stack-name ${resources_stack_name} \
    --no-fail-on-empty-changeset \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides "Prefix=${PREFIX}"
