/**
 * Jobs API Service
 * Handles all API calls for scheduled job operations.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export interface ScheduledJob {
    id: string;
    job_type: string;
    schedule: string;
    model_id?: string;
    enabled: boolean;
    last_run?: string;
    next_run: string;
    status: string;
    config?: Record<string, any>;
}

export interface JobRun {
    id: string;
    job_id: string;
    job_type: string;
    started_at: string;
    completed_at?: string;
    status: string;
    result?: Record<string, any>;
    error?: string;
}

export interface CreateJobRequest {
    job_type: string;
    model_id?: string;
    schedule?: string;
    config?: Record<string, any>;
}

export const jobService = {
    /**
     * List all scheduled jobs.
     */
    async listJobs(jobType?: string, modelId?: string): Promise<{ data: ScheduledJob[]; meta: { total: number } }> {
        const params: Record<string, string> = {};
        if (jobType) params.job_type = jobType;
        if (modelId) params.model_id = modelId;

        const response = await axios.get(`${API_BASE}/jobs`, { params });
        return response.data;
    },

    /**
     * Create a new job.
     */
    async createJob(request: CreateJobRequest): Promise<{ data: ScheduledJob }> {
        const response = await axios.post(`${API_BASE}/jobs`, request);
        return response.data;
    },

    /**
     * Get job details.
     */
    async getJob(jobId: string): Promise<{ data: ScheduledJob }> {
        const response = await axios.get(`${API_BASE}/jobs/${jobId}`);
        return response.data;
    },

    /**
     * Run a job manually.
     */
    async runJob(jobId: string): Promise<{ data: JobRun }> {
        const response = await axios.post(`${API_BASE}/jobs/${jobId}/run`);
        return response.data;
    },

    /**
     * Enable a job.
     */
    async enableJob(jobId: string): Promise<{ message: string }> {
        const response = await axios.post(`${API_BASE}/jobs/${jobId}/enable`);
        return response.data;
    },

    /**
     * Disable a job.
     */
    async disableJob(jobId: string): Promise<{ message: string }> {
        const response = await axios.post(`${API_BASE}/jobs/${jobId}/disable`);
        return response.data;
    },

    /**
     * Delete a job.
     */
    async deleteJob(jobId: string): Promise<{ message: string }> {
        const response = await axios.delete(`${API_BASE}/jobs/${jobId}`);
        return response.data;
    },

    /**
     * Get job run history.
     */
    async getJobRuns(jobId: string, limit = 10): Promise<{ data: JobRun[] }> {
        const response = await axios.get(`${API_BASE}/jobs/${jobId}/runs?limit=${limit}`);
        return response.data;
    },

    /**
     * Get available job types.
     */
    async getJobTypes(): Promise<{ data: { type: string; description: string }[] }> {
        const response = await axios.get(`${API_BASE}/jobs/types/available`);
        return response.data;
    },
};
