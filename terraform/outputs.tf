# Outputs are the interface between this module and whatever comes next --
# a human, a CI job, or another Terraform configuration.

output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Kubernetes API server endpoint."
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "Kubernetes version running on the control plane."
  value       = aws_eks_cluster.main.version
}

output "vpc_id" {
  description = "VPC the cluster runs in."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "The two public subnets, one per availability zone."
  value       = aws_subnet.public[*].id
}

output "configure_kubectl" {
  description = "Run this to point kubectl at the new cluster."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}
