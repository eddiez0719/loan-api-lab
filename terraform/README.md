# terraform/ - production environment for the lab

Builds "production" in AWS: ECR, ECS Fargate cluster and service, an Application Load Balancer (the `<PROD_ALB_DNS>`), and a GitHub OIDC deploy role (no long-lived AWS keys).

> **Cost:** the ALB and a running Fargate task bill by the hour. Apply only during the lesson and **always run `terraform destroy` afterwards.**

Run from this folder, on your fork's `main` branch:

```
terraform init
terraform apply -var github_repo=<your-user>/loan-api-lab
# if the account already has the GitHub OIDC provider:
terraform apply -var github_repo=<your-user>/loan-api-lab -var create_github_oidc_provider=false
terraform output prod_alb_dns
terraform output github_environment_variables
```

Clean up: `terraform destroy` with the same `-var` flags.

The ECS service ignores `task_definition` drift on purpose: after the bootstrap placeholder, the pipeline owns deployments. Do not edit ECS or task definitions in the console during the lab. State is local; never commit `*.tfstate`.
