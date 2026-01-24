"""
Extract storage account details for Azure Storage Explorer connection
"""
from app.core.config import settings

def show_connection_info():
    """Show connection information for Azure Storage Explorer."""
    print("=" * 70)
    print("Azure Storage Account Connection Information")
    print("=" * 70)
    
    conn_string = settings.AZURE_STORAGE_CONNECTION_STRING
    
    # Parse connection string
    parts = {}
    for part in conn_string.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            parts[key] = value
    
    account_name = parts.get('AccountName', 'NOT FOUND')
    
    print(f"\n📦 Storage Account Name: {account_name}")
    print(f"🔗 Connection String: {conn_string[:50]}...")
    
    print("\n" + "=" * 70)
    print("How to connect in Azure Storage Explorer:")
    print("=" * 70)
    print("\n1. Open Azure Storage Explorer")
    print("2. Click the 'Connect' icon (plug icon) on the left")
    print("3. Select 'Storage account or service'")
    print("4. Select 'Connection string'")
    print("5. Paste this connection string:")
    print(f"\n   {conn_string}")
    print("\n6. Click 'Next' → 'Connect'")
    print(f"7. Look for storage account: '{account_name}'")
    print("8. Expand 'Blob Containers'")
    print("9. You should see all 8 containers")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    show_connection_info()
