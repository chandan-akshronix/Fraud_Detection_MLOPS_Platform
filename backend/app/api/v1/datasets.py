"""
Datasets API Endpoints
CRUD operations for dataset management.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dataset import (
    DatasetResponse,
    DatasetListResponse,
    DatasetPreviewResponse,
)
from app.services.data_service import DataService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all datasets with pagination and optional filtering.
    
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    - **status**: Filter by status (ACTIVE, ARCHIVED, PROCESSING)
    """
    service = DataService(db)
    datasets, total = await service.list_datasets(
        page=page, 
        page_size=min(page_size, 100),
        status=status
    )
    return DatasetListResponse(
        data=datasets,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a new dataset.
    
    - **name**: Dataset name (required)
    - **description**: Optional description
    - **file**: Dataset file (CSV, Parquet, JSON)
    
    The file will be validated for schema and uploaded to Azure Blob Storage.
    """
    # Validate file type
    allowed_types = ["text/csv", "application/octet-stream", "application/json"]
    if file.content_type not in allowed_types and not file.filename.endswith(('.csv', '.parquet', '.json')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: CSV, Parquet, JSON"
        )
    
    service = DataService(db)
    dataset = await service.create_dataset(
        name=name,
        description=description,
        file=file
    )
    return DatasetResponse(data=dataset)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get dataset details by ID."""
    service = DataService(db)
    dataset = await service.get_dataset(str(dataset_id))
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    return DatasetResponse(data=dataset)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    dataset_id: UUID,
    rows: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Preview dataset rows.
    
    - **rows**: Number of rows to preview (max 100)
    """
    service = DataService(db)
    preview = await service.preview_dataset(str(dataset_id), rows=min(rows, 100))
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    return DatasetPreviewResponse(data=preview)


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get dataset schema with column types and statistics."""
    service = DataService(db)
    dataset = await service.get_dataset(str(dataset_id))
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    return {
        "data": {
            "columns": dataset.schema.get("columns", []) if dataset.schema else [],
            "row_count": dataset.row_count,
            "statistics": dataset.statistics
        }
    }


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a dataset (soft delete - marks as ARCHIVED)."""
    service = DataService(db)
    success = await service.delete_dataset(str(dataset_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    return None
