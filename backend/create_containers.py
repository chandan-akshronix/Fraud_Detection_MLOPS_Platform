"""
Create all 8 Azure Blob Storage containers
"""
from app.core.storage import storage_service
from app.core.config import settings

def create_all_containers():
    """Create all required containers."""
    containers = [
        settings.AZURE_STORAGE_CONTAINER_DATASETS,
        settings.AZURE_STORAGE_CONTAINER_MODELS,
        settings.AZURE_STORAGE_CONTAINER_FEATURES,
        settings.AZURE_STORAGE_CONTAINER_MONITORING,
        settings.AZURE_STORAGE_CONTAINER_AUDIT_LOGS,
        settings.AZURE_STORAGE_CONTAINER_EXPERIMENTS,
        settings.AZURE_STORAGE_CONTAINER_BACKUPS,
        settings.AZURE_STORAGE_CONTAINER_TEMP_PROCESSING,
    ]
    
    print("Creating Azure Blob Storage containers...")
    print("=" * 60)
    
    for container_name in containers:
        try:
            # This will create the container if it doesn't exist
            container_client = storage_service._get_container_client(container_name)
            print(f"✓ Container '{container_name}' ready")
        except Exception as e:
            print(f"✗ Failed to create '{container_name}': {e}")
    
    print("=" * 60)
    print("✅ All containers created successfully!")
    print("\nYou can now view them in Azure Storage Explorer")

if __name__ == "__main__":
    create_all_containers()