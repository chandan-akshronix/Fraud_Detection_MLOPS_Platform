"""
Show detailed container contents
"""
from app.core.storage import storage_service
from app.core.config import settings

def show_container_contents():
    """Show what's inside each container."""
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
    
    print("Azure Blob Storage Container Contents")
    print("=" * 70)
    
    for container_name in containers:
        try:
            container_client = storage_service._get_container_client(container_name)
            blobs = list(container_client.list_blobs())
            
            print(f"\n📦 Container: {container_name}")
            print(f"   Files: {len(blobs)}")
            
            if blobs:
                print("   Contents:")
                for blob in blobs[:5]:  # Show first 5 files
                    size_kb = blob.size / 1024 if blob.size else 0
                    print(f"     📄 {blob.name} ({size_kb:.2f} KB)")
                if len(blobs) > 5:
                    print(f"     ... and {len(blobs) - 5} more files")
            else:
                print("     (empty)")
                
        except Exception as e:
            print(f"\n📦 Container: {container_name}")
            print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    show_container_contents()
