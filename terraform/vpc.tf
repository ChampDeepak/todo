# ---------------------------------------------------------------------------
# Network
#
# Public subnets only, deliberately. The textbook layout puts worker nodes in
# private subnets behind a NAT Gateway, but a NAT Gateway costs ~$32/month plus
# data charges and adds several minutes to both apply and destroy. For a graded
# exercise that gets destroyed tonight, public subnets with security groups
# doing the actual access control is the honest trade.
#
# What you would change for production: private subnets for the nodes, NAT for
# their egress, and only the load balancers in public subnets.
# ---------------------------------------------------------------------------

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  # Both are required by EKS: pods resolve the cluster's internal DNS names and
  # AWS-internal endpoints by hostname.
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

# Two subnets in two different availability zones. This is not redundancy
# theatre: EKS *refuses to create a cluster* with subnets in fewer than two AZs,
# because the managed control plane runs across them.
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
    # This tag is load-bearing. The AWS load balancer controller scans subnets
    # for it to decide where to place an internet-facing load balancer. Without
    # it, a Service of type LoadBalancer in M8 stays <pending> forever with no
    # useful error.
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  # Everything not local to the VPC goes out through the internet gateway.
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
