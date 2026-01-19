# Shadow Hubble - Terraform Azure Infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "shadowhubble-tfstate"
    storage_account_name = "shadowhubbletfstate"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

provider "azuread" {}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "shadowhubble"
}

# Local values
locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${local.resource_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

# Networking Module
module "networking" {
  source = "./modules/networking"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags
}

# Database Module
module "database" {
  source = "./modules/database"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  subnet_id           = module.networking.database_subnet_id
  tags                = local.common_tags
}

# Redis Cache Module
module "redis" {
  source = "./modules/redis"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  subnet_id           = module.networking.redis_subnet_id
  tags                = local.common_tags
}

# Storage Module
module "storage" {
  source = "./modules/storage"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags
}

# Key Vault Module
module "keyvault" {
  source = "./modules/keyvault"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags
}

# Container Apps Module
module "container_apps" {
  source = "./modules/container_apps"

  resource_group_name   = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  resource_prefix       = local.resource_prefix
  subnet_id             = module.networking.app_subnet_id
  database_connection   = module.database.connection_string
  redis_connection      = module.redis.connection_string
  storage_connection    = module.storage.connection_string
  keyvault_uri          = module.keyvault.vault_uri
  tags                  = local.common_tags
}

# Application Insights Module
module "monitoring" {
  source = "./modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  resource_prefix     = local.resource_prefix
  tags                = local.common_tags
}

# Outputs
output "api_url" {
  value       = module.container_apps.api_url
  description = "API endpoint URL"
}

output "ui_url" {
  value       = module.container_apps.ui_url
  description = "Frontend UI URL"
}

output "database_server" {
  value       = module.database.server_fqdn
  description = "PostgreSQL server FQDN"
  sensitive   = true
}

output "keyvault_uri" {
  value       = module.keyvault.vault_uri
  description = "Key Vault URI"
}
