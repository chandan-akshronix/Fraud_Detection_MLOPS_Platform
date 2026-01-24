/**
 * Training Page
 * Configure and run model training jobs with a step wizard.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Card, Steps, Button, Select, Form, InputNumber, Slider,
    Table, Tag, Progress, Typography, Row, Col, Space, Divider,
    Radio, message, Alert, Popconfirm
} from 'antd';
import {
    ExperimentOutlined, PlayCircleOutlined, CheckCircleOutlined,
    DatabaseOutlined, SettingOutlined, RocketOutlined, PlusOutlined,
    DeleteOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { trainingService, Algorithm } from '@/services/trainingService';
import { featureService } from '@/services/featureService';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export function Training() {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(0);
    const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
    const [selectedFeatureSet, setSelectedFeatureSet] = useState<string | null>(null);
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('xgboost');
    const [hyperparameters, setHyperparameters] = useState<Record<string, any>>({});
    const [imbalancedStrategy, setImbalancedStrategy] = useState('class_weight');
    const [form] = Form.useForm();
    const queryClient = useQueryClient();

    // Fetch feature sets
    const { data: featureSets, isLoading: featureSetsLoading } = useQuery({
        queryKey: ['featureSets'],
        queryFn: () => featureService.listFeatureSets(),
    });

    // Fetch algorithms
    const { data: algorithms, isLoading: algorithmsLoading } = useQuery({
        queryKey: ['algorithms'],
        queryFn: () => trainingService.listAlgorithms(),
    });

    // Fetch training jobs
    const { data: trainingJobs, isLoading: jobsLoading } = useQuery({
        queryKey: ['trainingJobs'],
        queryFn: () => trainingService.listJobs(),
    });

    // Delete feature set mutation
    const deleteFeatureSetMutation = useMutation({
        mutationFn: (id: string) => featureService.deleteFeatureSet(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['featureSets'] });
            message.success('Feature set deleted successfully');
            if (selectedFeatureSet) {
                setSelectedFeatureSet(null);
            }
        },
        onError: () => {
            message.error('Failed to delete feature set');
        },
    });

    // Create training job mutation
    const createJobMutation = useMutation({
        mutationFn: trainingService.createJob,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trainingJobs'] });
            message.success('Training job started!');
            setCurrentStep(3);
        },
        onError: (error: Error) => {
            message.error(error.message || 'Failed to start training');
        },
    });

    // Update hyperparameters when algorithm changes
    useEffect(() => {
        if (algorithms?.data) {
            const algo = algorithms.data.find((a: Algorithm) => a.id === selectedAlgorithm);
            if (algo) {
                const defaults: Record<string, any> = {};
                algo.hyperparameters.forEach((hp: any) => {
                    defaults[hp.name] = hp.default;
                });
                setHyperparameters(defaults);
            }
        }
    }, [selectedAlgorithm, algorithms]);

    const steps = [
        { title: 'Select Data', icon: <DatabaseOutlined /> },
        { title: 'Configure', icon: <SettingOutlined /> },
        { title: 'Train', icon: <RocketOutlined /> },
        { title: 'Results', icon: <CheckCircleOutlined /> },
    ];

    const handleStartTraining = () => {
        if (!selectedFeatureSet) {
            message.error('Please select a feature set');
            return;
        }

        createJobMutation.mutate({
            name: `${selectedAlgorithm.toUpperCase()} Model - ${new Date().toLocaleDateString()}`,
            feature_set_id: selectedFeatureSet,
            algorithm: selectedAlgorithm,
            hyperparameters,
            imbalanced_strategy: imbalancedStrategy,
        });
    };

    const renderStepContent = () => {
        switch (currentStep) {
            case 0:
                return (
                    <Card title="Select Feature Set" style={{ marginTop: 24 }}>
                        <Alert
                            message="Choose a computed feature set to train on"
                            description="Feature sets contain engineered features ready for model training."
                            type="info"
                            showIcon
                            style={{ marginBottom: 24 }}
                        />
                        <Table
                            loading={featureSetsLoading}
                            dataSource={featureSets?.data || []}
                            rowKey="id"
                            rowSelection={{
                                type: 'radio',
                                selectedRowKeys: selectedFeatureSet ? [selectedFeatureSet] : [],
                                onChange: (keys) => setSelectedFeatureSet(keys[0] as string),
                            }}
                            columns={[
                                { title: 'Name', dataIndex: 'name', key: 'name' },
                                {
                                    title: 'Features',
                                    dataIndex: 'selected_feature_count',
                                    key: 'features',
                                    render: (count: number) => count || '-',
                                },
                                {
                                    title: 'Status',
                                    dataIndex: 'status',
                                    key: 'status',
                                    render: (status: string) => (
                                        <Tag color={status === 'COMPLETED' ? 'green' : 'blue'}>{status}</Tag>
                                    ),
                                },
                                { title: 'Created', dataIndex: 'created_at', key: 'created_at' },
                                {
                                    title: 'Actions',
                                    key: 'actions',
                                    render: (_: unknown, record: { id: string; name: string }) => (
                                        <Popconfirm
                                            title="Delete feature set"
                                            description="Are you sure you want to delete this feature set?"
                                            onConfirm={(e) => {
                                                e?.stopPropagation();
                                                deleteFeatureSetMutation.mutate(record.id);
                                            }}
                                            onCancel={(e) => e?.stopPropagation()}
                                            okText="Yes"
                                            cancelText="No"
                                        >
                                            <Button
                                                size="small"
                                                danger
                                                icon={<DeleteOutlined />}
                                                onClick={(e) => e.stopPropagation()}
                                                loading={deleteFeatureSetMutation.isPending}
                                            />
                                        </Popconfirm>
                                    ),
                                },
                            ]}
                            pagination={false}
                            locale={{
                                emptyText: (
                                    <div style={{ textAlign: 'center', padding: '40px' }}>
                                        <DatabaseOutlined style={{ fontSize: 40, color: '#d9d9d9', marginBottom: 16 }} />
                                        <Paragraph>
                                            <Text type="secondary" strong>No feature sets found.</Text>
                                            <br />
                                            <Text type="secondary">You need to compute features for a dataset before you can start training.</Text>
                                        </Paragraph>
                                        <Button
                                            type="primary"
                                            icon={<PlusOutlined />}
                                            onClick={() => navigate('/data')}
                                        >
                                            Go to Data Registry
                                        </Button>
                                    </div>
                                )
                            }}
                        />
                    </Card>
                );

            case 1:
                const selectedAlgo = algorithms?.data?.find((a: Algorithm) => a.id === selectedAlgorithm);
                return (
                    <Row gutter={24} style={{ marginTop: 24 }}>
                        <Col span={12}>
                            <Card title="Select Algorithm">
                                <Radio.Group
                                    value={selectedAlgorithm}
                                    onChange={(e) => setSelectedAlgorithm(e.target.value)}
                                    style={{ width: '100%' }}
                                >
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        {algorithms?.data?.map((algo: Algorithm) => (
                                            <Radio.Button
                                                key={algo.id}
                                                value={algo.id}
                                                style={{ width: '100%', height: 'auto', padding: 16 }}
                                            >
                                                <div>
                                                    <Text strong>{algo.name}</Text>
                                                    <br />
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        {algo.description}
                                                    </Text>
                                                </div>
                                            </Radio.Button>
                                        ))}
                                    </Space>
                                </Radio.Group>

                                <Divider />

                                <Title level={5}>Imbalanced Data Strategy</Title>
                                <Radio.Group
                                    value={imbalancedStrategy}
                                    onChange={(e) => setImbalancedStrategy(e.target.value)}
                                >
                                    <Space direction="vertical">
                                        <Radio value="class_weight">Class Weights (Recommended)</Radio>
                                        <Radio value="smote">SMOTE Oversampling</Radio>
                                        <Radio value="undersample">Random Undersampling</Radio>
                                    </Space>
                                </Radio.Group>
                            </Card>
                        </Col>

                        <Col span={12}>
                            <Card title="Hyperparameters">
                                {selectedAlgo?.hyperparameters?.map((hp: any) => (
                                    <Form.Item key={hp.name} label={hp.name}>
                                        {hp.type === 'int' ? (
                                            <Slider
                                                min={hp.min}
                                                max={hp.max}
                                                value={hyperparameters[hp.name] || hp.default}
                                                onChange={(val) => setHyperparameters({ ...hyperparameters, [hp.name]: val })}
                                                marks={{
                                                    [hp.min]: hp.min,
                                                    [hp.default]: `${hp.default} (default)`,
                                                    [hp.max]: hp.max,
                                                }}
                                            />
                                        ) : (
                                            <Slider
                                                min={hp.min}
                                                max={hp.max}
                                                step={0.01}
                                                value={hyperparameters[hp.name] || hp.default}
                                                onChange={(val) => setHyperparameters({ ...hyperparameters, [hp.name]: val })}
                                            />
                                        )}
                                        <Text type="secondary">
                                            Current: {hyperparameters[hp.name] || hp.default}
                                        </Text>
                                    </Form.Item>
                                ))}
                            </Card>
                        </Col>
                    </Row>
                );

            case 2:
                return (
                    <Card title="Review & Start Training" style={{ marginTop: 24 }}>
                        <Row gutter={24}>
                            <Col span={12}>
                                <Title level={5}>Configuration Summary</Title>
                                <Paragraph>
                                    <Text strong>Algorithm:</Text> {selectedAlgorithm.toUpperCase()}
                                </Paragraph>
                                <Paragraph>
                                    <Text strong>Feature Set:</Text> {selectedFeatureSet}
                                </Paragraph>
                                <Paragraph>
                                    <Text strong>Imbalanced Strategy:</Text> {imbalancedStrategy}
                                </Paragraph>
                                <Divider />
                                <Title level={5}>Hyperparameters</Title>
                                {Object.entries(hyperparameters).map(([key, value]) => (
                                    <Paragraph key={key}>
                                        <Text strong>{key}:</Text> {value}
                                    </Paragraph>
                                ))}
                            </Col>
                            <Col span={12}>
                                <Alert
                                    message="Ready to Train"
                                    description="Click 'Start Training' to begin. Training will run in the background."
                                    type="success"
                                    showIcon
                                />
                                <Button
                                    type="primary"
                                    size="large"
                                    icon={<PlayCircleOutlined />}
                                    onClick={handleStartTraining}
                                    loading={createJobMutation.isPending}
                                    style={{ marginTop: 24, width: '100%' }}
                                >
                                    Start Training
                                </Button>
                            </Col>
                        </Row>
                    </Card>
                );

            case 3:
                return (
                    <Card title="Training Jobs" style={{ marginTop: 24 }}>
                        <Table
                            loading={jobsLoading}
                            dataSource={trainingJobs?.data || []}
                            rowKey="id"
                            columns={[
                                { title: 'Name', dataIndex: 'name', key: 'name' },
                                { title: 'Algorithm', dataIndex: 'algorithm', key: 'algorithm' },
                                {
                                    title: 'Status',
                                    dataIndex: 'status',
                                    key: 'status',
                                    render: (status: string) => {
                                        const colors: Record<string, string> = {
                                            COMPLETED: 'green',
                                            RUNNING: 'blue',
                                            QUEUED: 'orange',
                                            FAILED: 'red',
                                        };
                                        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
                                    },
                                },
                                {
                                    title: 'Progress',
                                    dataIndex: 'progress',
                                    key: 'progress',
                                    render: (progress: number) => (
                                        <Progress percent={Math.round(progress * 100)} size="small" />
                                    ),
                                },
                                {
                                    title: 'Metrics',
                                    dataIndex: 'metrics',
                                    key: 'metrics',
                                    render: (metrics: any) => metrics ? (
                                        <Space>
                                            <Tag>F1: {(metrics.f1 * 100).toFixed(1)}%</Tag>
                                            <Tag>AUC: {(metrics.auc * 100).toFixed(1)}%</Tag>
                                        </Space>
                                    ) : '-',
                                },
                            ]}
                        />
                    </Card>
                );

            default:
                return null;
        }
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Training</Title>
                    <Text type="secondary">Configure and train fraud detection models</Text>
                </div>
            </div>

            <Card>
                <Steps
                    current={currentStep}
                    items={steps.map((step) => ({
                        title: step.title,
                        icon: step.icon,
                    }))}
                />
            </Card>

            {renderStepContent()}

            <div style={{ marginTop: 24, display: 'flex', justifyContent: 'space-between' }}>
                {currentStep > 0 && currentStep < 3 && (
                    <Button onClick={() => setCurrentStep(currentStep - 1)}>
                        Previous
                    </Button>
                )}
                {currentStep < 2 && (
                    <Button
                        type="primary"
                        onClick={() => setCurrentStep(currentStep + 1)}
                        disabled={currentStep === 0 && !selectedFeatureSet}
                        style={{ marginLeft: 'auto' }}
                    >
                        Next
                    </Button>
                )}
                {currentStep === 3 && (
                    <Button onClick={() => setCurrentStep(0)} style={{ marginLeft: 'auto' }}>
                        Train New Model
                    </Button>
                )}
            </div>
        </div>
    );
}
