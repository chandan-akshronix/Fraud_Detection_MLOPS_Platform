/**
 * Monitoring API Service
 * Handles all API calls for monitoring operations.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

export interface DriftMetrics {
    overall_status: string;
    last_computed: string;
    features: Record<string, {
        psi: number;
        ks_statistic: number;
        ks_p_value: number;
        status: string;
        trend: string;
    }>;
    thresholds: {
        psi_warning: number;
        psi_critical: number;
        ks_alpha: number;
    };
}

export interface BiasMetrics {
    overall_status: string;
    last_computed: string;
    protected_attributes: Record<string, {
        demographic_parity_diff: number;
        equalized_odds_diff: number;
        disparate_impact: number;
        status: string;
        group_rates: Record<string, number>;
    }>;
    thresholds: {
        demographic_parity: number;
        disparate_impact: number;
    };
}

export interface PerformanceMetrics {
    current: {
        precision: number;
        recall: number;
        f1: number;
        auc: number;
        fpr: number;
    };
    baseline: {
        precision: number;
        recall: number;
        f1: number;
        auc: number;
        fpr: number;
    };
    trend: Array<{
        date: string;
        precision: number;
        recall: number;
        f1: number;
    }>;
    period: string;
}

export const monitoringService = {
    /**
     * Get drift metrics for a model.
     */
    async getDriftMetrics(modelId: string): Promise<{ data: DriftMetrics }> {
        const response = await axios.get(`${API_BASE}/monitoring/drift/${modelId}`);
        return response.data;
    },

    /**
     * Get bias metrics for a model.
     */
    async getBiasMetrics(modelId: string): Promise<{ data: BiasMetrics }> {
        const response = await axios.get(`${API_BASE}/monitoring/bias/${modelId}`);
        return response.data;
    },

    /**
     * Get performance metrics for a model.
     */
    async getPerformanceMetrics(modelId: string, period = '7d'): Promise<{ data: PerformanceMetrics }> {
        const response = await axios.get(`${API_BASE}/monitoring/performance/${modelId}?period=${period}`);
        return response.data;
    },

    /**
     * Trigger manual drift computation.
     */
    async triggerDriftComputation(modelId: string): Promise<void> {
        await axios.post(`${API_BASE}/monitoring/drift/${modelId}/compute`);
    },

    /**
     * Trigger manual bias computation.
     */
    async triggerBiasComputation(modelId: string): Promise<void> {
        await axios.post(`${API_BASE}/monitoring/bias/${modelId}/compute`);
    },
};
