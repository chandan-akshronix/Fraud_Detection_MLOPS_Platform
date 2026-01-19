/**
 * Training API Service
 * Handles all API calls for training operations.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export interface Algorithm {
    id: string;
    name: string;
    description: string;
    hyperparameters: Array<{
        name: string;
        type: string;
        default: number;
        min: number;
        max: number;
    }>;
}

export interface TrainingJob {
    id: string;
    name: string;
    feature_set_id: string;
    algorithm: string;
    hyperparameters: Record<string, any>;
    status: string;
    progress: number;
    metrics?: {
        precision: number;
        recall: number;
        f1: number;
        auc: number;
    };
    created_at: string;
    completed_at?: string;
}

export interface CreateJobRequest {
    name: string;
    feature_set_id: string;
    algorithm: string;
    hyperparameters: Record<string, any>;
    imbalanced_strategy: string;
}

export const trainingService = {
    /**
     * List all training jobs.
     */
    async listJobs(status?: string): Promise<{ data: TrainingJob[] }> {
        const params = status ? { status } : {};
        const response = await axios.get(`${API_BASE}/training/jobs`, { params });
        return response.data;
    },

    /**
     * Create a new training job.
     */
    async createJob(request: CreateJobRequest): Promise<{ data: TrainingJob }> {
        const response = await axios.post(`${API_BASE}/training/jobs`, request);
        return response.data;
    },

    /**
     * Get training job status.
     */
    async getJob(jobId: string): Promise<TrainingJob> {
        const response = await axios.get(`${API_BASE}/training/jobs/${jobId}`);
        return response.data.data;
    },

    /**
     * List available algorithms.
     */
    async listAlgorithms(): Promise<{ data: Algorithm[] }> {
        const response = await axios.get(`${API_BASE}/training/algorithms`);
        return response.data;
    },

    /**
     * Get default hyperparameters for an algorithm.
     */
    async getAlgorithmDefaults(algorithmId: string): Promise<Record<string, any>> {
        const response = await axios.get(`${API_BASE}/training/algorithms/${algorithmId}/defaults`);
        return response.data.data;
    },
};
