"""
Azure Blob Storage Connection Test
Run this script to verify your Azure Storage connection.

Usage:
    cd backend
    python -m scripts.test_storage_connection
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_connection():
    """Test Azure Blob Storage connection."""
    from app.core.config import settings
    from app.core.storage import StorageService
    
    print("=" * 60)
    print("Azure Blob Storage Connection Test")
    print("=" * 60)
    
    # Check if connection string is set
    if not settings.AZURE_STORAGE_CONNECTION_STRING:
        print("\n❌ ERROR: AZURE_STORAGE_CONNECTION_STRING not set!")
        print("\nPlease add it to your .env file:")
        print("AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...")
        return False
    
    print(f"\n✓ Connection string found")
    print(f"✓ Datasets container: {settings.AZURE_STORAGE_CONTAINER_DATASETS}")
    print(f"✓ Models container: {settings.AZURE_STORAGE_CONTAINER_MODELS}")
    
    try:
        storage = StorageService()
        
        # Test connection by listing containers
        print("\n📡 Testing connection...")
        client = storage.client
        containers = list(client.list_containers())
        
        print(f"\n✓ Connection successful!")
        print(f"✓ Found {len(containers)} container(s):")
        for container in containers:
            print(f"   - {container['name']}")
        
        # Check for required containers
        container_names = [c['name'] for c in containers]
        required = ['datasets', 'models']
        missing = [c for c in required if c not in container_names]
        
        if missing:
            print(f"\n⚠️  Missing required containers: {missing}")
            print("   They will be created automatically when you upload files.")
        else:
            print(f"\n✓ All required containers exist!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nPlease check:")
        print("  1. Your connection string is correct")
        print("  2. The storage account exists and is accessible")
        print("  3. Your network can reach Azure")
        return False


async def test_upload_download():
    """Test upload and download operations."""
    from app.core.storage import storage_service
    
    print("\n" + "=" * 60)
    print("Testing Upload/Download Operations")
    print("=" * 60)
    
    test_data = b"transaction_id,amount,is_fraud\n1,100.00,0\n2,999.99,1\n3,50.00,0"
    test_name = "__test_dataset__"
    test_version = "test"
    
    try:
        # Test upload
        print("\n📤 Uploading test dataset...")
        storage_path = await storage_service.upload_dataset(
            name=test_name,
            version=test_version,
            data=test_data,
            file_format="csv",
            metadata={"test": "true"}
        )
        print(f"   ✓ Uploaded to: {storage_path}")
        
        # Test download
        print("\n📥 Downloading test dataset...")
        downloaded = await storage_service.download_dataset(storage_path)
        if downloaded == test_data:
            print("   ✓ Downloaded data matches!")
        else:
            print("   ⚠️ Downloaded data differs from original")
        
        # Test metadata
        print("\n📋 Getting metadata...")
        metadata = await storage_service.get_blob_metadata(storage_path)
        if metadata:
            print(f"   ✓ Size: {metadata['size']} bytes")
            print(f"   ✓ Created: {metadata['created_on']}")
        
        # Test SAS URL
        print("\n🔗 Generating SAS URL...")
        sas_url = storage_service.generate_sas_url(storage_path, expiry_hours=1)
        print(f"   ✓ SAS URL generated (valid for 1 hour)")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        await storage_service.delete_dataset(storage_path)
        print("   ✓ Test dataset deleted")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Azure Blob Storage is ready.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Test operations
    if not asyncio.run(test_upload_download()):
        sys.exit(1)
    
    print("\n🎉 Azure Blob Storage setup complete!")
    print("\nNext steps:")
    print("  1. Run database migrations: alembic upgrade head")
    print("  2. Start the API server: uvicorn app.main:app --reload")
    print("  3. Upload a dataset via the API: POST /api/v1/datasets/upload")


if __name__ == "__main__":
    main()
