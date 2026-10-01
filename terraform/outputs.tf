output "prod_alb_dns" {
  description = "Use as <PROD_ALB_DNS> and as BASE_URL (http://<this>)"
  value       = aws_lb.this.dns_name
}

output "github_environment_variables" {
  description = "Create these as variables on the GitHub Environment 'production'"
  value = {
    AWS_REGION     = var.region
    AWS_ROLE_ARN   = aws_iam_role.github_deploy.arn
    ECR_REPOSITORY = aws_ecr_repository.app.name
    ECS_CLUSTER    = aws_ecs_cluster.this.name
    ECS_SERVICE    = aws_ecs_service.app.name
    BASE_URL       = "http://${aws_lb.this.dns_name}"
  }
}

output "task_execution_role_arn" {
  description = "Put this in .aws/task-definition.json as executionRoleArn"
  value       = aws_iam_role.task_execution.arn
}
