"""
Data Service
Business logic for dataset operations with Azure Blob Storage integration.
"""
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID
import io
import logging

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

from app.models.dataset import Dataset
from app.core.storage import storage_service

logger = logging.getLogger(__name__)


class DataService:
    """Service for dataset operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = storage_service
    
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
        version: str = "1.0",
    ) -> Dataset:
        """Create a new dataset from uploaded file."""
        # Read file content
        content = await file.read()
        
        # Determine format and parse
        file_format = "csv"
        if file.filename and file.filename.endswith(".parquet"):
            file_format = "parquet"
            df = pd.read_parquet(io.BytesIO(content))
        elif file.filename and file.filename.endswith(".json"):
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
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
                })
            elif df[col].dtype == "object":
                col_stats["unique_count"] = int(df[col].nunique())
            statistics[col] = col_stats
        
        # Upload to Azure Blob Storage
        try:
            storage_path = await self.storage.upload_dataset(
                name=name,
                version=version,
                data=content,
                file_format=file_format,
                metadata={
                    "row_count": str(len(df)),
                    "column_count": str(len(df.columns)),
                    "description": description or "",
                }
            )
            logger.info(f"Uploaded dataset to storage: {storage_path}")
        except Exception as e:
            logger.error(f"Failed to upload dataset to storage: {e}")
            raise ValueError(f"Failed to upload dataset: {str(e)}")
        
        # Create database record
        dataset = Dataset(
            name=name,
            description=description,
            version=version,
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
        
        # Load from Azure Blob Storage
        try:
            content = await self.storage.download_dataset(dataset.storage_path)
            
            # Parse based on format
            if dataset.file_format == "parquet":
                df = pd.read_parquet(io.BytesIO(content))
            elif dataset.file_format == "json":
                df = pd.read_json(io.BytesIO(content))
            else:
                df = pd.read_csv(io.BytesIO(content))
            
            # Get preview rows
            preview_df = df.head(rows)
            
            return {
                "columns": list(df.columns),
                "rows": preview_df.to_dict(orient="records"),
                "total_rows": dataset.row_count,
                "preview_rows": len(preview_df),
            }
        except FileNotFoundError:
            logger.warning(f"Dataset file not found in storage: {dataset.storage_path}")
            return {
                "columns": [c["name"] for c in dataset.schema.get("columns", [])] if dataset.schema else [],
                "rows": [],
                "total_rows": dataset.row_count,
                "preview_rows": 0,
                "error": "File not found in storage",
            }
        except Exception as e:
            logger.error(f"Failed to load dataset preview: {e}")
            return {
                "columns": [c["name"] for c in dataset.schema.get("columns", [])] if dataset.schema else [],
                "rows": [],
                "total_rows": dataset.row_count,
                "preview_rows": 0,
                "error": str(e),
            }
    
    async def delete_dataset(self, dataset_id: str, hard_delete: bool = False) -> bool:
        """Delete a dataset (soft delete by default)."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return False
        
        if hard_delete:
            # Delete from blob storage
            try:
                await self.storage.delete_dataset(dataset.storage_path)
                logger.info(f"Deleted dataset from storage: {dataset.storage_path}")
            except Exception as e:
                logger.warning(f"Failed to delete from storage: {e}")
            
            # Delete from database
            await self.db.delete(dataset)
        else:
            # Soft delete
            dataset.status = "ARCHIVED"
        
        await self.db.commit()
        return True
    
    async def get_dataset_download_url(
        self,
        dataset_id: str,
        expiry_hours: int = 1,
    ) -> Optional[str]:
        """Get a temporary download URL for a dataset."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return None
        
        try:
            return self.storage.generate_sas_url(
                storage_path=dataset.storage_path,
                expiry_hours=expiry_hours,
                permission="r",
            )
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            return None
