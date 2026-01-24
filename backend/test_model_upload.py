"""
Upload a test model to demonstrate the models container folder structure
"""
import asyncio
from app.core.storage import storage_service
from datetime import datetime

async def upload_test_model():
    """Upload a test model to show folder structure."""
    print("Uploading test model to demonstrate folder structure...")
    print("=" * 70)
    
    # Create dummy model data
    model_data = b"This is a test model file"
    
    # Model metadata
    model_metadata = {
        "model_id": "test-model-001",
        "version": "v1.0.0",
        "algorithm": "XGBoost",
        "created_at": datetime.utcnow().isoformat(),
        "metrics": {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.89
        }
    }
    
    try:
        # Upload model using the existing upload_model method
        print("\n📤 Uploading model...")
        storage_path = await storage_service.upload_model(
            model_name="test-model-001",
            version="v1.0.0",
            model_data=model_data,
            format="onnx",
            metadata={
                "algorithm": "XGBoost",
                "accuracy": "0.95"
            }
        )
        print(f"✓ Model uploaded to: {storage_path}")
        
        # Upload model metadata JSON
        print("\n📤 Uploading model metadata...")
        metadata_path = await storage_service._upload_json_metadata(
            container_name="models",
            blob_path="test-model-001/v1.0.0/model_metadata.json",
            metadata_dict=model_metadata
        )
        print(f"✓ Metadata uploaded to: {metadata_path}")
        
        print("\n" + "=" * 70)
        print("✅ Test model uploaded successfully!")
        print("\nNow check Azure Storage Explorer:")
        print("  1. Refresh the 'models' container")
        print("  2. You should see folder structure:")
        print("     models/")
        print("       └── test-model-001/")
        print("           └── v1.0.0/")
        print("               ├── model.onnx")
        print("               └── model_metadata.json")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(upload_test_model())
