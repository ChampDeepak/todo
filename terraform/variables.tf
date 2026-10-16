variable "aws_region" {
  description = "AWS region to deploy into. ap-south-1 (Mumbai) is closest to IST."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix applied to every resource name, so resources are traceable to this project."
  type        = string
  default     = "taskr"
}

variable "environment" {
  description = "Environment label used in tags and names."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "Address space for the VPC. /16 gives 65k addresses, far more than needed, but leaves room to add subnets without renumbering."
  type        = string
  default     = "10.0.0.0/16"
}

variable "kubernetes_version" {
  description = "EKS control plane version."
  type        = string
  default     = "1.31"
}

variable "node_instance_type" {
  description = "Worker node size. t3.small, not t3.medium: this AWS account is Free Tier-restricted and refuses to launch any instance type outside the free-tier list, which t3.medium is not on. t3.small gives 2 vCPU / 2 GiB and an ENI limit allowing 11 pods per node -- enough for the system pods plus this application."
  type        = string
  default     = "t3.small"
}

variable "node_desired_size" {
  description = "Number of worker nodes. 2 x t3.small = 2 vCPUs, well inside a new AWS account's default 5-vCPU on-demand quota. Two nodes, not one, so the node group demonstrates scheduling across availability zones."
  type        = number
  default     = 2
}
