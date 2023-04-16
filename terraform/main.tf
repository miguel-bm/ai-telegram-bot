provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}


resource "aws_elastic_beanstalk_application" "bot_app" {
  name        = var.app_name
  description = "Personal AI Telegram bot application"

  tags = {
    Name = var.app_name
  }
}

resource "aws_elastic_beanstalk_environment" "bot_env" {
  name        = var.env_name
  application = aws_elastic_beanstalk_application.bot_app.name

  solution_stack_name = "64bit Amazon Linux 2 v3.5.6 running Docker"

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = "t2.micro"
  }

  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = "1"
  }

  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = "1"
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.eb_instance_profile.name
  }

  dynamic "setting" {
    for_each = var.env_vars
    content {
      namespace = "aws:elasticbeanstalk:application:environment"
      name      = setting.key
      value     = setting.value
    }
  }

  tags = {
    Name = var.app_name
  }
}

resource "aws_iam_role" "eb_instance_role" {
  name = "${var.app_name}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = var.app_name
  }
}

resource "aws_iam_role_policy_attachment" "eb_instance_web_tier_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
  role       = aws_iam_role.eb_instance_role.name
}

resource "aws_iam_role_policy_attachment" "eb_instance_docker_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkMulticontainerDocker"
  role       = aws_iam_role.eb_instance_role.name
}

resource "aws_iam_instance_profile" "eb_instance_profile" {
  name = "${var.app_name}-instance-profile"
  role = aws_iam_role.eb_instance_role.name

  tags = {
    Name = var.app_name
  }
}

resource "aws_ecr_repository" "bot_repo" {
  name = var.app_name

  force_delete = true

  tags = {
    Name = var.app_name
  }
}

resource "aws_iam_policy" "ecr_access_policy" {
  name        = "${var.app_name}-ecr-access-policy"
  description = "Policy to grant Elastic Beanstalk instances access to ECR repository"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = var.app_name
  }
}

# Attach the new ECR access policy to the existing Elastic Beanstalk instance role
resource "aws_iam_role_policy_attachment" "eb_instance_ecr_policy" {
  policy_arn = aws_iam_policy.ecr_access_policy.arn
  role       = aws_iam_role.eb_instance_role.name
}

resource "aws_s3_bucket" "bot_bucket" {
  bucket = var.app_name

  force_destroy = true

  tags = {
    Name = var.app_name
  }
}
