"""
List all containers in Azure Blob Storage
"""
from app.core.storage import storage_service

def list_all_containers():
    """List all containers in the storage account."""
    print("Listing all containers in Azure Blob Storage...")
    print("=" * 60)
    
    try:
        # Get the blob service client
        client = storage_service.client
        
        # List all containers
        containers = list(client.list_containers())
        
        if containers:
            print(f"✓ Found {len(containers)} container(s):\n")
            for container in containers:
                print(f"  📦 {container['name']}")
                print(f"     Created: {container.get('last_modified', 'N/A')}")
                print()
        else:
            print("⚠️  No containers found!")
            print("\nThis might mean:")
            print("  1. Containers haven't been created yet")
            print("  2. Connection string is incorrect")
            print("  3. You're connected to a different storage account")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPlease check:")
        print("  1. AZURE_STORAGE_CONNECTION_STRING in .env is correct")
        print("  2. Network connectivity to Azure")

if __name__ == "__main__":
    list_all_containers()
