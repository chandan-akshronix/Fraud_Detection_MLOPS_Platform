/**
 * Monitoring Page
 * Track data drift, model performance, and bias metrics.
 */
import { useState } from 'react';
import {
    Card, Row, Col, Typography, Tag, Table, Tabs, Progress,
    Statistic, Space, Button, Tooltip, Alert
} from 'antd';
import {
    LineChartOutlined, WarningOutlined, CheckCircleOutlined,
    ReloadOutlined, ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip as RechartsTooltip, ResponsiveContainer, Legend,
    BarChart, Bar, Cell
} from 'recharts';
import { monitoringService } from '@/services/monitoringService';

const { Title, Text } = Typography;

// Mock model ID for demo
const DEMO_MODEL_ID = 'demo-model-001';

export function Monitoring() {
    const [activeTab, setActiveTab] = useState('drift');
    const queryClient = useQueryClient();

    // Fetch drift metrics
    const { data: driftData, isLoading: driftLoading } = useQuery({
        queryKey: ['drift', DEMO_MODEL_ID],
        queryFn: () => monitoringService.getDriftMetrics(DEMO_MODEL_ID),
    });

    // Fetch bias metrics
    const { data: biasData, isLoading: biasLoading } = useQuery({
        queryKey: ['bias', DEMO_MODEL_ID],
        queryFn: () => monitoringService.getBiasMetrics(DEMO_MODEL_ID),
    });

    // Fetch performance metrics
    const { data: performanceData, isLoading: performanceLoading } = useQuery({
        queryKey: ['performance', DEMO_MODEL_ID],
        queryFn: () => monitoringService.getPerformanceMetrics(DEMO_MODEL_ID),
    });

    // Refresh mutations
    const refreshDriftMutation = useMutation({
        mutationFn: () => monitoringService.triggerDriftComputation(DEMO_MODEL_ID),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['drift'] });
        },
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'OK': return 'green';
            case 'WARNING': return 'orange';
            case 'CRITICAL': return 'red';
            default: return 'default';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'OK': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
            case 'WARNING': return <WarningOutlined style={{ color: '#faad14' }} />;
            case 'CRITICAL': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
            default: return null;
        }
    };

    // Prepare drift table data
    const getDriftTableData = () => {
        if (!driftData?.data?.features) return [];
        return Object.entries(driftData.data.features).map(([name, metrics]: [string, any]) => ({
            key: name,
            feature: name,
            ...metrics,
        }));
    };

    // Prepare bias table data
    const getBiasTableData = () => {
        if (!biasData?.data?.protected_attributes) return [];
        return Object.entries(biasData.data.protected_attributes).map(([name, metrics]: [string, any]) => ({
            key: name,
            attribute: name,
            ...metrics,
        }));
    };

    const driftColumns = [
        {
            title: 'Feature',
            dataIndex: 'feature',
            key: 'feature',
            render: (name: string) => <Text strong>{name}</Text>,
        },
        {
            title: 'PSI',
            dataIndex: 'psi',
            key: 'psi',
            render: (psi: number) => (
                <Tooltip title={`PSI: ${psi.toFixed(4)}`}>
                    <Progress
                        percent={Math.min(psi / 0.25 * 100, 100)}
                        size="small"
                        strokeColor={psi > 0.25 ? '#ff4d4f' : psi > 0.1 ? '#faad14' : '#52c41a'}
                        format={() => psi.toFixed(3)}
                    />
                </Tooltip>
            ),
        },
        {
            title: 'KS Statistic',
            dataIndex: 'ks_statistic',
            key: 'ks_statistic',
            render: (ks: number) => ks.toFixed(4),
        },
        {
            title: 'P-Value',
            dataIndex: 'ks_p_value',
            key: 'ks_p_value',
            render: (p: number) => (
                <Tag color={p < 0.05 ? 'red' : 'green'}>{p.toFixed(4)}</Tag>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Space>
                    {getStatusIcon(status)}
                    <Tag color={getStatusColor(status)}>{status}</Tag>
                </Space>
            ),
        },
    ];

    const biasColumns = [
        {
            title: 'Protected Attribute',
            dataIndex: 'attribute',
            key: 'attribute',
            render: (name: string) => <Text strong>{name}</Text>,
        },
        {
            title: 'Demographic Parity Diff',
            dataIndex: 'demographic_parity_diff',
            key: 'demographic_parity_diff',
            render: (diff: number) => (
                <Tag color={diff > 0.1 ? 'orange' : 'green'}>{diff.toFixed(3)}</Tag>
            ),
        },
        {
            title: 'Disparate Impact',
            dataIndex: 'disparate_impact',
            key: 'disparate_impact',
            render: (di: number) => (
                <Tag color={di < 0.8 ? 'red' : 'green'}>{(di * 100).toFixed(1)}%</Tag>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Space>
                    {getStatusIcon(status)}
                    <Tag color={getStatusColor(status)}>{status}</Tag>
                </Space>
            ),
        },
    ];

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Monitoring</Title>
                    <Text type="secondary">Track drift, performance, and bias metrics</Text>
                </div>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={() => refreshDriftMutation.mutate()}
                    loading={refreshDriftMutation.isPending}
                >
                    Refresh Metrics
                </Button>
            </div>

            {/* Status Summary Cards */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Drift Status"
                            value={driftData?.data?.overall_status || 'N/A'}
                            prefix={getStatusIcon(driftData?.data?.overall_status || '')}
                            valueStyle={{
                                color: driftData?.data?.overall_status === 'OK' ? '#3f8600' :
                                    driftData?.data?.overall_status === 'WARNING' ? '#cf9700' : '#cf1322'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Bias Status"
                            value={biasData?.data?.overall_status || 'N/A'}
                            prefix={getStatusIcon(biasData?.data?.overall_status || '')}
                            valueStyle={{
                                color: biasData?.data?.overall_status === 'OK' ? '#3f8600' : '#cf9700'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Current F1 Score"
                            value={(performanceData?.data?.current?.f1 || 0) * 100}
                            suffix="%"
                            precision={1}
                            valueStyle={{ color: '#3f8600' }}
                        />
                    </Card>
                </Col>
            </Row>

            <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={[
                    {
                        key: 'drift',
                        label: (
                            <span>
                                <LineChartOutlined /> Data Drift
                            </span>
                        ),
                        children: (
                            <Card>
                                {driftData?.data?.overall_status === 'CRITICAL' && (
                                    <Alert
                                        message="Critical Drift Detected"
                                        description="Significant drift has been detected in one or more features. Consider retraining the model."
                                        type="error"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />
                                )}
                                <Table
                                    loading={driftLoading}
                                    dataSource={getDriftTableData()}
                                    columns={driftColumns}
                                    pagination={false}
                                />
                            </Card>
                        ),
                    },
                    {
                        key: 'performance',
                        label: (
                            <span>
                                <LineChartOutlined /> Performance
                            </span>
                        ),
                        children: (
                            <Card title="Performance Metrics Over Time">
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart data={performanceData?.data?.trend || []}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis domain={[0.8, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                                        <RechartsTooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
                                        <Legend />
                                        <Line type="monotone" dataKey="precision" stroke="#2563EB" strokeWidth={2} />
                                        <Line type="monotone" dataKey="recall" stroke="#059669" strokeWidth={2} />
                                        <Line type="monotone" dataKey="f1" stroke="#7C3AED" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </Card>
                        ),
                    },
                    {
                        key: 'bias',
                        label: (
                            <span>
                                <WarningOutlined /> Bias Detection
                            </span>
                        ),
                        children: (
                            <Card>
                                {biasData?.data?.overall_status === 'WARNING' && (
                                    <Alert
                                        message="Bias Warning"
                                        description="Fairness thresholds have been exceeded for one or more protected attributes."
                                        type="warning"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />
                                )}
                                <Table
                                    loading={biasLoading}
                                    dataSource={getBiasTableData()}
                                    columns={biasColumns}
                                    pagination={false}
                                />
                            </Card>
                        ),
                    },
                ]}
            />
        </div>
    );
}
