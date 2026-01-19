/**
 * Dataset API Service
 * Handles all API calls for dataset operations.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export interface Dataset {
    id: string;
    name: string;
    description?: string;
    version: string;
    storage_path: string;
    file_format: string;
    file_size_bytes?: number;
    row_count?: number;
    column_count?: number;
    schema?: { columns: Array<{ name: string; type: string; nullable: boolean }> };
    statistics?: Record<string, unknown>;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface DatasetListResponse {
    data: Dataset[];
    meta: {
        page: number;
        page_size: number;
        total: number;
        total_pages: number;
    };
}

export interface DatasetResponse {
    data: Dataset;
}

export const datasetService = {
    /**
     * List all datasets with pagination.
     */
    async list(page = 1, pageSize = 20, status?: string): Promise<DatasetListResponse> {
        const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
        if (status) params.append('status', status);

        const response = await axios.get<DatasetListResponse>(`${API_BASE}/datasets?${params}`);
        return response.data;
    },

    /**
     * Get a single dataset by ID.
     */
    async get(id: string): Promise<Dataset> {
        const response = await axios.get<DatasetResponse>(`${API_BASE}/datasets/${id}`);
        return response.data.data;
    },

    /**
     * Create a new dataset with file upload.
     */
    async create(name: string, file: File, description?: string): Promise<Dataset> {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('file', file);
        if (description) formData.append('description', description);

        const response = await axios.post<DatasetResponse>(`${API_BASE}/datasets`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data.data;
    },

    /**
     * Delete a dataset.
     */
    async delete(id: string): Promise<void> {
        await axios.delete(`${API_BASE}/datasets/${id}`);
    },

    /**
     * Preview dataset rows.
     */
    async preview(id: string, rows = 10): Promise<{ columns: string[]; rows: unknown[]; total_rows: number }> {
        const response = await axios.get(`${API_BASE}/datasets/${id}/preview?rows=${rows}`);
        return response.data.data;
    },
};
