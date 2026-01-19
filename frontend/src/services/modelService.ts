/**
 * Model API Service
 * Handles all API calls for model registry operations.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export interface MLModel {
    id: string;
    name: string;
    version: string;
    description?: string;
    algorithm: string;
    hyperparameters: Record<string, any>;
    status: string;
    metrics: {
        precision: number;
        recall: number;
        f1: number;
        auc: number;
        accuracy: number;
    };
    feature_names?: string[];
    feature_importance?: Record<string, number>;
    storage_path: string;
    onnx_path?: string;
    checksum?: string;
    created_at: string;
    promoted_at?: string;
}

export interface Baseline {
    metric: string;
    threshold: number;
    operator: string;
}

export const modelService = {
    /**
     * List all models.
     */
    async listModels(status?: string): Promise<{ data: MLModel[] }> {
        const params = status ? { status } : {};
        const response = await axios.get(`${API_BASE}/models`, { params });
        return response.data;
    },

    /**
     * Get a single model.
     */
    async getModel(modelId: string): Promise<MLModel> {
        const response = await axios.get(`${API_BASE}/models/${modelId}`);
        return response.data.data;
    },

    /**
     * Get the production model.
     */
    async getProductionModel(): Promise<{ data: MLModel | null }> {
        const response = await axios.get(`${API_BASE}/models/production`);
        return response.data;
    },

    /**
     * Promote a model to a new status.
     */
    async promoteModel(modelId: string, targetStatus: string): Promise<MLModel> {
        const response = await axios.post(`${API_BASE}/models/${modelId}/promote`, {
            target_status: targetStatus,
        });
        return response.data.data;
    },

    /**
     * Set baseline thresholds for a model.
     */
    async setBaselines(modelId: string, baselines: Baseline[]): Promise<Baseline[]> {
        const response = await axios.post(`${API_BASE}/models/${modelId}/baselines`, baselines);
        return response.data.data;
    },

    /**
     * Compare two models.
     */
    async compareModels(modelId1: string, modelId2: string): Promise<any> {
        const response = await axios.get(`${API_BASE}/models/${modelId1}/compare/${modelId2}`);
        return response.data;
    },
};
