#!/bin/zsh

# Load environment variables from .env file
source ./.env

# Set AWS profile and region
export AWS_PROFILE="$AWS_PROFILE"
export AWS_REGION="$AWS_REGION"
export APP_NAME="$APP_NAME"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

# Create an ECR repository
aws ecr create-repository --repository-name $APP_NAME

# Log in to the ECR repository
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push the Docker image
docker tag $APP_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME:latest

# Create an ECS cluster
aws ecs create-cluster --cluster-name $APP_NAME

# Create a Task Definition
cat > task-definition.json <<EOL
{
  "family": "$APP_NAME",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "$APP_NAME",
      "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "hostPort": 8080
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$APP_NAME",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": [
    "FARGATE"
  ],
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512"
}
EOL
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create a Service
aws ecs create-service --cluster $APP_NAME --service-name $APP_NAME --task-definition $APP_NAME --desired-count 1 --launch-type "FARGATE" --platform-version "LATEST" --scheduling-strategy "REPLICA" --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100"

# Cleanup
rm task-definition.json