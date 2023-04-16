provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}


resource "aws_elastic_beanstalk_application" "bot_app" {
  name        = var.app_name
  description = "Personal AI Telegram bot application"
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
}
