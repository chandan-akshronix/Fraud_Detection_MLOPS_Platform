/**
 * Model Registry Page
 * View, compare, and promote trained models.
 */
import { useState } from 'react';
import {
    Card, Table, Button, Tag, Modal, Typography, Row, Col, Space,
    Statistic, Descriptions, Progress, Tooltip, message, Empty
} from 'antd';
import {
    AppstoreOutlined, RocketOutlined, EyeOutlined,
    SwapOutlined, CheckCircleOutlined, StarFilled
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelService, MLModel } from '@/services/modelService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

const { Title, Text } = Typography;

export function ModelRegistry() {
    const [selectedModel, setSelectedModel] = useState<MLModel | null>(null);
    const [detailModalOpen, setDetailModalOpen] = useState(false);
    const queryClient = useQueryClient();

    // Fetch models
    const { data: models, isLoading } = useQuery({
        queryKey: ['models'],
        queryFn: () => modelService.listModels(),
    });

    // Fetch production model
    const { data: productionModel } = useQuery({
        queryKey: ['productionModel'],
        queryFn: () => modelService.getProductionModel(),
    });

    // Promote mutation
    const promoteMutation = useMutation({
        mutationFn: ({ modelId, status }: { modelId: string; status: string }) =>
            modelService.promoteModel(modelId, status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['models'] });
            queryClient.invalidateQueries({ queryKey: ['productionModel'] });
            message.success('Model promoted successfully');
        },
    });

    const handleViewDetails = (model: MLModel) => {
        setSelectedModel(model);
        setDetailModalOpen(true);
    };

    const handlePromote = (modelId: string, targetStatus: string) => {
        promoteMutation.mutate({ modelId, status: targetStatus });
    };

    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (name: string, record: MLModel) => (
                <Space>
                    {record.status === 'PRODUCTION' && <StarFilled style={{ color: '#faad14' }} />}
                    <Text strong>{name}</Text>
                </Space>
            ),
        },
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            render: (version: string) => <Tag>{version}</Tag>,
        },
        {
            title: 'Algorithm',
            dataIndex: 'algorithm',
            key: 'algorithm',
            render: (algo: string) => algo?.toUpperCase(),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                const colors: Record<string, string> = {
                    TRAINED: 'default',
                    STAGING: 'blue',
                    PRODUCTION: 'green',
                    ARCHIVED: 'gray',
                };
                return <Tag color={colors[status] || 'default'}>{status}</Tag>;
            },
        },
        {
            title: 'Metrics',
            key: 'metrics',
            render: (_: any, record: MLModel) => {
                if (!record.metrics) return '-';
                return (
                    <Space>
                        <Tooltip title="Precision">
                            <Tag>P: {(record.metrics.precision * 100).toFixed(1)}%</Tag>
                        </Tooltip>
                        <Tooltip title="Recall">
                            <Tag>R: {(record.metrics.recall * 100).toFixed(1)}%</Tag>
                        </Tooltip>
                        <Tooltip title="F1 Score">
                            <Tag color="blue">F1: {(record.metrics.f1 * 100).toFixed(1)}%</Tag>
                        </Tooltip>
                    </Space>
                );
            },
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => new Date(date).toLocaleDateString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: MLModel) => (
                <Space>
                    <Button
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewDetails(record)}
                    >
                        Details
                    </Button>
                    {record.status === 'TRAINED' && (
                        <Button
                            size="small"
                            type="primary"
                            icon={<RocketOutlined />}
                            onClick={() => handlePromote(record.id, 'STAGING')}
                        >
                            Stage
                        </Button>
                    )}
                    {record.status === 'STAGING' && (
                        <Button
                            size="small"
                            type="primary"
                            icon={<CheckCircleOutlined />}
                            onClick={() => handlePromote(record.id, 'PRODUCTION')}
                        >
                            Deploy
                        </Button>
                    )}
                </Space>
            ),
        },
    ];

    // Prepare feature importance chart data
    const getFeatureImportanceData = (model: MLModel | null) => {
        if (!model?.feature_importance) return [];
        return Object.entries(model.feature_importance)
            .sort(([, a], [, b]) => (b as number) - (a as number))
            .slice(0, 10)
            .map(([name, value]) => ({
                name: name.length > 15 ? name.slice(0, 15) + '...' : name,
                importance: (value as number * 100).toFixed(2),
            }));
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Model Registry</Title>
                    <Text type="secondary">View, compare, and deploy trained models</Text>
                </div>
            </div>

            {/* Production Model Card */}
            {productionModel?.data && (
                <Card style={{ marginBottom: 24, borderColor: '#52c41a' }}>
                    <Row gutter={24} align="middle">
                        <Col>
                            <StarFilled style={{ fontSize: 48, color: '#faad14' }} />
                        </Col>
                        <Col flex={1}>
                            <Title level={4} style={{ margin: 0 }}>
                                Production Model: {productionModel.data.name}
                            </Title>
                            <Text type="secondary">
                                {productionModel.data.algorithm?.toUpperCase()} • v{productionModel.data.version}
                            </Text>
                        </Col>
                        <Col>
                            <Space size="large">
                                <Statistic
                                    title="Precision"
                                    value={(productionModel.data.metrics?.precision || 0) * 100}
                                    suffix="%"
                                    precision={1}
                                />
                                <Statistic
                                    title="Recall"
                                    value={(productionModel.data.metrics?.recall || 0) * 100}
                                    suffix="%"
                                    precision={1}
                                />
                                <Statistic
                                    title="F1 Score"
                                    value={(productionModel.data.metrics?.f1 || 0) * 100}
                                    suffix="%"
                                    precision={1}
                                    valueStyle={{ color: '#3f8600' }}
                                />
                            </Space>
                        </Col>
                    </Row>
                </Card>
            )}

            {/* Models Table */}
            <Card title="All Models">
                <Table
                    loading={isLoading}
                    dataSource={models?.data || []}
                    columns={columns}
                    rowKey="id"
                    pagination={{
                        pageSize: 10,
                        showTotal: (total) => `Total ${total} models`,
                    }}
                />
            </Card>

            {/* Model Detail Modal */}
            <Modal
                title={selectedModel?.name || 'Model Details'}
                open={detailModalOpen}
                onCancel={() => setDetailModalOpen(false)}
                width={800}
                footer={null}
            >
                {selectedModel && (
                    <>
                        <Descriptions bordered size="small" column={2}>
                            <Descriptions.Item label="Version">{selectedModel.version}</Descriptions.Item>
                            <Descriptions.Item label="Algorithm">{selectedModel.algorithm?.toUpperCase()}</Descriptions.Item>
                            <Descriptions.Item label="Status">
                                <Tag>{selectedModel.status}</Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Created">
                                {new Date(selectedModel.created_at).toLocaleString()}
                            </Descriptions.Item>
                        </Descriptions>

                        <Title level={5} style={{ marginTop: 24 }}>Performance Metrics</Title>
                        <Row gutter={16}>
                            {selectedModel.metrics && Object.entries(selectedModel.metrics).map(([key, value]) => (
                                <Col span={6} key={key}>
                                    <Card size="small">
                                        <Statistic
                                            title={key.charAt(0).toUpperCase() + key.slice(1)}
                                            value={(value as number) * 100}
                                            suffix="%"
                                            precision={2}
                                        />
                                    </Card>
                                </Col>
                            ))}
                        </Row>

                        <Title level={5} style={{ marginTop: 24 }}>Feature Importance (Top 10)</Title>
                        {selectedModel.feature_importance ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={getFeatureImportanceData(selectedModel)} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" />
                                    <YAxis dataKey="name" type="category" width={120} />
                                    <RechartsTooltip />
                                    <Bar dataKey="importance" fill="#2563EB" />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <Empty description="No feature importance data available" />
                        )}
                    </>
                )}
            </Modal>
        </div>
    );
}
