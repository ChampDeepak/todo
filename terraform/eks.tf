# ---------------------------------------------------------------------------
# EKS cluster + managed node group
#
# "Managed" means AWS runs the control plane (API server, etcd, scheduler) and
# you never see those machines. You pay $0.10/hour for it whether or not you
# use it, which is the entire reason `terraform destroy` is worth 2 points.
# ---------------------------------------------------------------------------

# --- IAM: the control plane's own role ---------------------------------------
# EKS assumes this role to create load balancers, network interfaces and
# security groups on your behalf. It is not the role your pods use.
resource "aws_iam_role" "cluster" {
  name = "${var.project_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

# --- IAM: the worker nodes' role ---------------------------------------------
# Three policies, each for a distinct job:
#   WorkerNodePolicy -- the kubelet registers the node with the control plane
#   CNI_Policy       -- the VPC CNI assigns real VPC IPs to pods
#   ECR ReadOnly     -- nodes pull container images from ECR
resource "aws_iam_role" "node" {
  name = "${var.project_name}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "node_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
  ])

  role       = aws_iam_role.node.name
  policy_arn = each.value
}

# --- The cluster -------------------------------------------------------------
resource "aws_eks_cluster" "main" {
  name     = "${var.project_name}-cluster"
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = aws_subnet.public[*].id
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  # Control plane logs to CloudWatch. Without these, debugging a rejected API
  # call means guessing: you cannot see why the API server refused a request.
  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  # API mode plus this flag is what lets the IAM identity that ran `terraform
  # apply` actually use kubectl afterwards. Omit it and you create a cluster
  # you are locked out of -- a genuinely common and very annoying mistake.
  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  # Explicit dependency: without it Terraform may create the cluster before the
  # policy attachment lands, and the cluster fails with an opaque permissions
  # error. Terraform infers most ordering from references, but not this one.
  depends_on = [aws_iam_role_policy_attachment.cluster_policy]

  tags = { Name = "${var.project_name}-cluster" }
}

# --- Worker nodes ------------------------------------------------------------
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_name}-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = aws_subnet.public[*].id

  instance_types = [var.node_instance_type]
  capacity_type  = "ON_DEMAND"
  disk_size      = 20

  scaling_config {
    desired_size = var.node_desired_size
    min_size     = 1
    max_size     = 3
  }

  # During a node replacement, allow at most one node unavailable at a time, so
  # the workload keeps serving through the roll.
  update_config {
    max_unavailable = 1
  }

  depends_on = [aws_iam_role_policy_attachment.node_policies]

  tags = { Name = "${var.project_name}-node-group" }
}
