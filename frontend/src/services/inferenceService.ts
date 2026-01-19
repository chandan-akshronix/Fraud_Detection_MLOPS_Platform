/**
 * Inference API Service
 * Handles all API calls for prediction operations.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export interface PredictionRequest {
    transaction_id?: string;
    features: Record<string, any>;
}

export interface PredictionResponse {
    transaction_id?: string;
    prediction: number;
    fraud_score: number;
    confidence: number;
    risk_level: string;
    response_time_ms: number;
    explanation?: {
        feature_contributions: Record<string, number>;
        top_positive_factors: string[];
        top_negative_factors: string[];
        explanation_text: string;
    };
}

export interface ModelInfo {
    model_id: string;
    model_name: string;
    algorithm: string;
    version: string;
    loaded_at: string;
    feature_count: number;
    onnx_enabled: boolean;
    avg_latency_ms: number;
    throughput_per_second: number;
}

export const inferenceService = {
    /**
     * Make a single prediction.
     */
    async predict(request: PredictionRequest): Promise<{ data: PredictionResponse }> {
        const response = await axios.post(`${API_BASE}/inference/predict`, request);
        return response.data;
    },

    /**
     * Make a prediction with explanation.
     */
    async predictWithExplanation(request: PredictionRequest): Promise<{ data: PredictionResponse }> {
        const response = await axios.post(`${API_BASE}/inference/predict/explain`, request);
        return response.data;
    },

    /**
     * Make batch predictions.
     */
    async predictBatch(transactions: PredictionRequest[]): Promise<{
        data: PredictionResponse[];
        meta: {
            total_transactions: number;
            total_time_ms: number;
            avg_time_per_transaction_ms: number;
        };
    }> {
        const response = await axios.post(`${API_BASE}/inference/predict/batch`, {
            transactions,
        });
        return response.data;
    },

    /**
     * Get information about the loaded model.
     */
    async getModelInfo(): Promise<{ data: ModelInfo }> {
        const response = await axios.get(`${API_BASE}/inference/model/info`);
        return response.data;
    },
};
