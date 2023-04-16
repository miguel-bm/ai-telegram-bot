#!/bin/sh
set -a
source ../.env
set +a

# Extract variable names from the .env file
env_var_names=$(grep -oE '^[^=#]+' ../.env)

tf_env_vars=""

# Iterate over the variable names and build the TF_VAR_env_vars map
for env_var_name in $env_var_names; do
  env_var_value="${!env_var_name}"
  tf_env_vars+=" $env_var_name=\"$env_var_value\","
done

export TF_VAR_env_vars="{$tf_env_vars}"

# Load environment variables from .env file
export $(grep -v '^#' ../.env | xargs)

# Pass environment variables to Terraform
export TF_VAR_aws_profile="$AWS_PROFILE"
export TF_VAR_aws_region="$AWS_REGION"
export TF_VAR_app_name="$APP_NAME"
export TF_VAR_env_name="$ENV_NAME"

# Run Terraform commands
terraform "$@"
