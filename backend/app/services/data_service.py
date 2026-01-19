"""
Data Service
Business logic for dataset operations.
"""
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID
import io

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

from app.models.dataset import Dataset


class DataService:
    """Service for dataset operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_datasets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[Dataset], int]:
        """List datasets with pagination."""
        # Base query
        query = select(Dataset).order_by(Dataset.created_at.desc())
        count_query = select(func.count(Dataset.id))
        
        # Filter by status
        if status:
            query = query.where(Dataset.status == status)
            count_query = count_query.where(Dataset.status == status)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute
        result = await self.db.execute(query)
        datasets = result.scalars().all()
        
        return list(datasets), total
    
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get a single dataset by ID."""
        try:
            uuid_id = UUID(dataset_id)
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == uuid_id)
        )
        return result.scalar_one_or_none()
    
    async def create_dataset(
        self,
        name: str,
        file: UploadFile,
        description: Optional[str] = None,
    ) -> Dataset:
        """Create a new dataset from uploaded file."""
        # Read file content
        content = await file.read()
        
        # Determine format and parse
        file_format = "csv"
        if file.filename.endswith(".parquet"):
            file_format = "parquet"
            df = pd.read_parquet(io.BytesIO(content))
        elif file.filename.endswith(".json"):
            file_format = "json"
            df = pd.read_json(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
        
        # Extract schema
        schema = {
            "columns": [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "nullable": bool(df[col].isna().any()),
                }
                for col in df.columns
            ]
        }
        
        # Compute basic statistics
        statistics = {}
        for col in df.columns:
            col_stats = {"type": str(df[col].dtype)}
            if df[col].dtype in ["int64", "float64"]:
                col_stats.update({
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                })
            elif df[col].dtype == "object":
                col_stats["unique_count"] = int(df[col].nunique())
            statistics[col] = col_stats
        
        # TODO: Upload to Azure Blob Storage
        storage_path = f"datasets/{name}/v1.0/data.{file_format}"
        
        # Create database record
        dataset = Dataset(
            name=name,
            description=description,
            storage_path=storage_path,
            file_format=file_format,
            file_size_bytes=len(content),
            row_count=len(df),
            column_count=len(df.columns),
            schema=schema,
            statistics=statistics,
            status="ACTIVE",
        )
        
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)
        
        return dataset
    
    async def preview_dataset(
        self,
        dataset_id: str,
        rows: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Get preview of dataset rows."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return None
        
        # TODO: Load from Azure Blob Storage and return preview
        # For now, return schema info
        return {
            "columns": [c["name"] for c in dataset.schema.get("columns", [])] if dataset.schema else [],
            "rows": [],  # Will be populated from blob storage
            "total_rows": dataset.row_count,
            "preview_rows": rows,
        }
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Soft delete a dataset."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return False
        
        dataset.status = "ARCHIVED"
        await self.db.commit()
        return True
