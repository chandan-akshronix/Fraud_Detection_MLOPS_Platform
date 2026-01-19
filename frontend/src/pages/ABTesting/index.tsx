/**
 * A/B Testing Page
 * Manage champion-challenger model tests.
 */
import { useState } from 'react';
import {
    Card, Table, Tag, Button, Typography, Row, Col, Space,
    Modal, Form, Input, InputNumber, Select, Progress, Statistic
} from 'antd';
import {
    ExperimentOutlined, PlayCircleOutlined, StopOutlined,
    TrophyOutlined, CheckCircleOutlined, CloseCircleOutlined,
    PlusOutlined, LineChartOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;

interface ABTest {
    id: string;
    name: string;
    champion_model_id: string;
    challenger_model_id: string;
    status: string;
    result: string;
    champion_samples: number;
    challenger_samples: number;
    created_at: string;
}

const abTestingService = {
    listTests: async () => {
        const response = await axios.get('/api/v1/ab-tests');
        return response.data;
    },
    createTest: async (data: any) => {
        const response = await axios.post('/api/v1/ab-tests', data);
        return response.data;
    },
    startTest: async (testId: string) => {
        const response = await axios.post(`/api/v1/ab-tests/${testId}/start`);
        return response.data;
    },
    evaluateTest: async (testId: string) => {
        const response = await axios.post(`/api/v1/ab-tests/${testId}/evaluate`);
        return response.data;
    },
    concludeTest: async (testId: string, result: string, promote: boolean) => {
        const response = await axios.post(
            `/api/v1/ab-tests/${testId}/conclude?result=${result}&promote_challenger=${promote}`
        );
        return response.data;
    },
    abortTest: async (testId: string) => {
        const response = await axios.post(`/api/v1/ab-tests/${testId}/abort`);
        return response.data;
    },
};

export function ABTesting() {
    const [createModal, setCreateModal] = useState(false);
    const [evaluateModal, setEvaluateModal] = useState<string | null>(null);
    const [evaluationResult, setEvaluationResult] = useState<any>(null);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();

    // Fetch tests
    const { data: testsData, isLoading } = useQuery({
        queryKey: ['ab-tests'],
        queryFn: abTestingService.listTests,
    });

    // Create mutation
    const createMutation = useMutation({
        mutationFn: abTestingService.createTest,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ab-tests'] });
            setCreateModal(false);
            form.resetFields();
        },
    });

    // Start mutation
    const startMutation = useMutation({
        mutationFn: abTestingService.startTest,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ab-tests'] });
        },
    });

    // Evaluate mutation
    const evaluateMutation = useMutation({
        mutationFn: abTestingService.evaluateTest,
        onSuccess: (data) => {
            setEvaluationResult(data.data);
        },
    });

    // Conclude mutation
    const concludeMutation = useMutation({
        mutationFn: ({ testId, result, promote }: { testId: string; result: string; promote: boolean }) =>
            abTestingService.concludeTest(testId, result, promote),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ab-tests'] });
            setEvaluateModal(null);
            setEvaluationResult(null);
        },
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'RUNNING': return 'blue';
            case 'COMPLETED': return 'green';
            case 'ABORTED': return 'red';
            default: return 'default';
        }
    };

    const getResultIcon = (result: string) => {
        switch (result) {
            case 'CHALLENGER_WINS': return <TrophyOutlined style={{ color: '#52c41a' }} />;
            case 'CHAMPION_WINS': return <CheckCircleOutlined style={{ color: '#1890ff' }} />;
            case 'NO_SIGNIFICANT_DIFFERENCE': return <CloseCircleOutlined style={{ color: '#8c8c8c' }} />;
            default: return null;
        }
    };

    const columns = [
        { title: 'Name', dataIndex: 'name', key: 'name' },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>,
        },
        {
            title: 'Result',
            dataIndex: 'result',
            key: 'result',
            render: (result: string) => (
                <Space>
                    {getResultIcon(result)}
                    <Text>{result.replace(/_/g, ' ')}</Text>
                </Space>
            ),
        },
        {
            title: 'Champion Samples',
            dataIndex: 'champion_samples',
            key: 'champion_samples',
            render: (v: number) => v.toLocaleString(),
        },
        {
            title: 'Challenger Samples',
            dataIndex: 'challenger_samples',
            key: 'challenger_samples',
            render: (v: number) => v.toLocaleString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: ABTest) => (
                <Space>
                    {record.status === 'DRAFT' && (
                        <Button
                            size="small"
                            icon={<PlayCircleOutlined />}
                            onClick={() => startMutation.mutate(record.id)}
                        >
                            Start
                        </Button>
                    )}
                    {record.status === 'RUNNING' && (
                        <>
                            <Button
                                size="small"
                                icon={<LineChartOutlined />}
                                onClick={() => {
                                    setEvaluateModal(record.id);
                                    evaluateMutation.mutate(record.id);
                                }}
                            >
                                Evaluate
                            </Button>
                            <Button
                                size="small"
                                danger
                                icon={<StopOutlined />}
                            >
                                Abort
                            </Button>
                        </>
                    )}
                </Space>
            ),
        },
    ];

    const tests = testsData?.data || [];
    const runningTests = tests.filter((t: ABTest) => t.status === 'RUNNING').length;

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>A/B Testing</Title>
                    <Text type="secondary">Champion-challenger model comparison</Text>
                </div>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setCreateModal(true)}
                >
                    New Test
                </Button>
            </div>

            {/* Summary Cards */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Total Tests"
                            value={tests.length}
                            prefix={<ExperimentOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Running"
                            value={runningTests}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Challenger Wins"
                            value={tests.filter((t: ABTest) => t.result === 'CHALLENGER_WINS').length}
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Champion Wins"
                            value={tests.filter((t: ABTest) => t.result === 'CHAMPION_WINS').length}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Tests Table */}
            <Card>
                <Table
                    loading={isLoading}
                    dataSource={tests}
                    columns={columns}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* Create Test Modal */}
            <Modal
                title="Create A/B Test"
                open={createModal}
                onCancel={() => setCreateModal(false)}
                onOk={() => form.submit()}
                confirmLoading={createMutation.isPending}
                width={600}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={(values) => createMutation.mutate(values)}
                >
                    <Form.Item
                        name="name"
                        label="Test Name"
                        rules={[{ required: true }]}
                    >
                        <Input placeholder="e.g., XGBoost v2 vs Production" />
                    </Form.Item>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                name="champion_model_id"
                                label="Champion Model ID"
                                rules={[{ required: true }]}
                            >
                                <Input placeholder="Current production model" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                name="challenger_model_id"
                                label="Challenger Model ID"
                                rules={[{ required: true }]}
                            >
                                <Input placeholder="New model to test" />
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                name="challenger_traffic_percent"
                                label="Challenger Traffic %"
                                initialValue={10}
                            >
                                <InputNumber min={1} max={50} style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                name="min_samples"
                                label="Min Samples"
                                initialValue={1000}
                            >
                                <InputNumber min={100} style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>
                    </Row>

                    <Form.Item
                        name="primary_metric"
                        label="Primary Metric"
                        initialValue="f1"
                    >
                        <Select>
                            <Option value="f1">F1 Score</Option>
                            <Option value="precision">Precision</Option>
                            <Option value="recall">Recall</Option>
                            <Option value="auc">AUC</Option>
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Evaluation Modal */}
            <Modal
                title="A/B Test Evaluation"
                open={!!evaluateModal}
                onCancel={() => {
                    setEvaluateModal(null);
                    setEvaluationResult(null);
                }}
                footer={evaluationResult?.ready_for_decision ? [
                    <Button key="keep" onClick={() => evaluateModal && concludeMutation.mutate({
                        testId: evaluateModal, result: 'CHAMPION_WINS', promote: false
                    })}>
                        Keep Champion
                    </Button>,
                    <Button key="promote" type="primary" onClick={() => evaluateModal && concludeMutation.mutate({
                        testId: evaluateModal, result: 'CHALLENGER_WINS', promote: true
                    })}>
                        Promote Challenger
                    </Button>,
                ] : null}
                width={600}
            >
                {evaluateMutation.isPending ? (
                    <div style={{ textAlign: 'center', padding: 24 }}>
                        <Progress type="circle" percent={75} />
                        <Text>Evaluating...</Text>
                    </div>
                ) : evaluationResult ? (
                    <div>
                        {evaluationResult.ready_for_decision ? (
                            <>
                                <Row gutter={16} style={{ marginBottom: 16 }}>
                                    <Col span={12}>
                                        <Card size="small" title="Champion">
                                            {Object.entries(evaluationResult.champion_metrics || {}).map(([k, v]) => (
                                                <p key={k}><Text strong>{k}:</Text> {String(v)}</p>
                                            ))}
                                        </Card>
                                    </Col>
                                    <Col span={12}>
                                        <Card size="small" title="Challenger">
                                            {Object.entries(evaluationResult.challenger_metrics || {}).map(([k, v]) => (
                                                <p key={k}><Text strong>{k}:</Text> {String(v)}</p>
                                            ))}
                                        </Card>
                                    </Col>
                                </Row>
                                <Card size="small" title="Analysis">
                                    <p><Text strong>Recommendation:</Text> {evaluationResult.analysis?.recommendation}</p>
                                    <p><Text strong>Difference:</Text> {evaluationResult.analysis?.difference_percent?.toFixed(2)}%</p>
                                    <p><Text strong>Significant:</Text> {evaluationResult.analysis?.is_significant ? 'Yes' : 'No'}</p>
                                </Card>
                            </>
                        ) : (
                            <div>
                                <Text>Need more samples: {evaluationResult.samples_collected} / {evaluationResult.samples_needed}</Text>
                                <Progress
                                    percent={(evaluationResult.samples_collected / evaluationResult.samples_needed) * 100}
                                />
                            </div>
                        )}
                    </div>
                ) : null}
            </Modal>
        </div>
    );
}
