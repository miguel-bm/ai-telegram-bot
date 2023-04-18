set dotenv-load
ACCOUNT_ID := `aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text`
APP_NAME := `echo $APP_NAME`
ENV_NAME := `echo $ENV_NAME`

REGION := `echo $AWS_REGION`
PROFILE := `echo $AWS_PROFILE`

test:
    poetry run pytest

build:
    docker buildx build --platform linux/amd64 . -t {{APP_NAME}}

# Run the bot in a Docker container using Docker Compose
run:
    docker-compose up -d

# Stop the running Docker container and remove its resources using Docker Compose
stop:
    docker-compose down

# Rebuild and rerun the Docker container using Docker Compose
rebuild_rerun:
    just down
    just build
    just run

# Enter the command line inside the running Docker container
shell:
    docker exec -it ai-telegam-bot-container /bin/bash

terraform-init:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh init


terraform-validate:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh validate

terraform-plan:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh plan


terraform-apply:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh apply


terraform-destroy:
    #!/bin/sh
    cd terraform
    ./run_terraform.sh destroy

tag:
    docker tag {{APP_NAME}}:latest {{ACCOUNT_ID}}.dkr.ecr.{{REGION}}.amazonaws.com/{{APP_NAME}}:latest

push:
    #!/bin/zsh
    aws ecr get-login-password --region $AWS_REGION --profile {{PROFILE}} | docker login --username AWS --password-stdin {{ACCOUNT_ID}}.dkr.ecr.{{REGION}}.amazonaws.com
    docker tag {{APP_NAME}}:latest {{ACCOUNT_ID}}.dkr.ecr.{{REGION}}.amazonaws.com/{{APP_NAME}}:latest
    docker push ${ECR_REPOSITORY_URL}/telegram-bot-repo:latest
    docker push {{ACCOUNT_ID}}.dkr.ecr.{{REGION}}.amazonaws.com/{{APP_NAME}}:latest


update-app:
    #!/bin/zsh
    VERSION_LABEL=$(date +%Y%m%d%H%M%S)
    echo '{"AWSEBDockerrunVersion": "1", "Image": {"Name": "{{ACCOUNT_ID}}.dkr.ecr.{{REGION}}.amazonaws.com/{{APP_NAME}}:latest", "Update": "true"}, "Ports": [{"ContainerPort": "80"}]}' > Dockerrun.aws.json && zip dockerrun.zip Dockerrun.aws.json && aws s3 cp dockerrun.zip s3://{{APP_NAME}}/dockerrun.zip --region {{REGION}} --profile {{PROFILE}} && aws elasticbeanstalk create-application-version --region {{REGION}} --profile {{PROFILE}} --application-name {{APP_NAME}} --version-label $VERSION_LABEL --source-bundle S3Bucket={{APP_NAME}},S3Key=dockerrun.zip
    aws elasticbeanstalk update-environment --region {{REGION}} --profile {{PROFILE}} --environment-name {{ENV_NAME}} --version-label $VERSION_LABEL
    echo "Update complete!"

# Deploy the latest version of the Telegram bot
deploy:
	just build
	just push
	just update-app
