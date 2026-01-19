/**
 * Inference Page
 * Real-time fraud prediction interface.
 */
import { useState } from 'react';
import {
    Card, Row, Col, Typography, Form, Input, InputNumber, Button,
    Statistic, Tag, Progress, Divider, Space, Alert, Collapse
} from 'antd';
import {
    ThunderboltOutlined, SafetyOutlined, WarningOutlined,
    ExclamationCircleOutlined
} from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { inferenceService, PredictionResponse } from '@/services/inferenceService';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

export function Inference() {
    const [result, setResult] = useState<PredictionResponse | null>(null);
    const [form] = Form.useForm();

    // Prediction mutation
    const predictMutation = useMutation({
        mutationFn: inferenceService.predict,
        onSuccess: (data) => {
            setResult(data.data);
        },
    });

    const handlePredict = (values: any) => {
        predictMutation.mutate({
            transaction_id: values.transaction_id,
            features: {
                amount: values.amount,
                merchant_category: values.merchant_category,
                is_online: values.is_online ? 1 : 0,
                hour_of_day: new Date().getHours(),
                day_of_week: new Date().getDay(),
            },
        });
    };

    const getRiskColor = (riskLevel: string) => {
        switch (riskLevel) {
            case 'CRITICAL': return '#ff4d4f';
            case 'HIGH': return '#fa8c16';
            case 'MEDIUM': return '#faad14';
            case 'LOW': return '#52c41a';
            default: return '#8c8c8c';
        }
    };

    const getRiskIcon = (riskLevel: string) => {
        switch (riskLevel) {
            case 'CRITICAL': return <ExclamationCircleOutlined />;
            case 'HIGH': return <WarningOutlined />;
            case 'MEDIUM': return <WarningOutlined />;
            case 'LOW': return <SafetyOutlined />;
            default: return null;
        }
    };

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Real-time Inference</Title>
                    <Text type="secondary">Test fraud detection predictions</Text>
                </div>
            </div>

            <Row gutter={24}>
                {/* Input Form */}
                <Col span={10}>
                    <Card title="Transaction Details" extra={<ThunderboltOutlined />}>
                        <Form
                            form={form}
                            layout="vertical"
                            onFinish={handlePredict}
                            initialValues={{
                                amount: 150.00,
                                merchant_category: 'retail',
                                is_online: false,
                            }}
                        >
                            <Form.Item
                                name="transaction_id"
                                label="Transaction ID"
                            >
                                <Input placeholder="TXN-12345" />
                            </Form.Item>

                            <Form.Item
                                name="amount"
                                label="Amount ($)"
                                rules={[{ required: true, message: 'Amount is required' }]}
                            >
                                <InputNumber
                                    style={{ width: '100%' }}
                                    min={0}
                                    precision={2}
                                    formatter={(value) => `$ ${value}`}
                                />
                            </Form.Item>

                            <Form.Item
                                name="merchant_category"
                                label="Merchant Category"
                            >
                                <Input placeholder="retail, travel, electronics..." />
                            </Form.Item>

                            <Form.Item
                                name="card_present"
                                label="Card Present"
                                valuePropName="checked"
                            >
                                <Input type="checkbox" />
                            </Form.Item>

                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={predictMutation.isPending}
                                icon={<ThunderboltOutlined />}
                                size="large"
                                style={{ width: '100%' }}
                            >
                                Predict
                            </Button>
                        </Form>
                    </Card>
                </Col>

                {/* Results */}
                <Col span={14}>
                    {result ? (
                        <Card>
                            {/* Risk Level Banner */}
                            <Alert
                                message={`Risk Level: ${result.risk_level}`}
                                type={
                                    result.risk_level === 'LOW' ? 'success' :
                                        result.risk_level === 'MEDIUM' ? 'warning' :
                                            'error'
                                }
                                showIcon
                                icon={getRiskIcon(result.risk_level)}
                                style={{ marginBottom: 24 }}
                            />

                            {/* Main Stats */}
                            <Row gutter={16} style={{ marginBottom: 24 }}>
                                <Col span={8}>
                                    <Card size="small">
                                        <Statistic
                                            title="Prediction"
                                            value={result.prediction === 1 ? 'FRAUD' : 'LEGITIMATE'}
                                            valueStyle={{
                                                color: result.prediction === 1 ? '#ff4d4f' : '#52c41a',
                                                fontSize: 20,
                                            }}
                                        />
                                    </Card>
                                </Col>
                                <Col span={8}>
                                    <Card size="small">
                                        <Statistic
                                            title="Fraud Score"
                                            value={result.fraud_score * 100}
                                            suffix="%"
                                            precision={1}
                                            valueStyle={{ color: getRiskColor(result.risk_level) }}
                                        />
                                    </Card>
                                </Col>
                                <Col span={8}>
                                    <Card size="small">
                                        <Statistic
                                            title="Response Time"
                                            value={result.response_time_ms}
                                            suffix="ms"
                                            precision={2}
                                            valueStyle={{ color: result.response_time_ms < 10 ? '#52c41a' : '#faad14' }}
                                        />
                                    </Card>
                                </Col>
                            </Row>

                            {/* Confidence Bar */}
                            <div style={{ marginBottom: 24 }}>
                                <Text strong>Confidence</Text>
                                <Progress
                                    percent={result.confidence * 100}
                                    strokeColor={getRiskColor(result.risk_level)}
                                    format={(p) => `${p?.toFixed(1)}%`}
                                />
                            </div>

                            {/* Explanation (if available) */}
                            {result.explanation && (
                                <Collapse style={{ marginTop: 16 }}>
                                    <Panel header="Explanation" key="1">
                                        <Paragraph>
                                            <pre style={{ margin: 0 }}>
                                                {result.explanation.explanation_text}
                                            </pre>
                                        </Paragraph>

                                        {result.explanation.top_positive_factors && (
                                            <>
                                                <Divider orientation="left">Risk Factors</Divider>
                                                <ul>
                                                    {result.explanation.top_positive_factors.map((f: string, i: number) => (
                                                        <li key={i}><Text type="danger">{f}</Text></li>
                                                    ))}
                                                </ul>
                                            </>
                                        )}

                                        {result.explanation.top_negative_factors && (
                                            <>
                                                <Divider orientation="left">Mitigating Factors</Divider>
                                                <ul>
                                                    {result.explanation.top_negative_factors.map((f: string, i: number) => (
                                                        <li key={i}><Text type="success">{f}</Text></li>
                                                    ))}
                                                </ul>
                                            </>
                                        )}
                                    </Panel>
                                </Collapse>
                            )}
                        </Card>
                    ) : (
                        <Card style={{ textAlign: 'center', padding: 48 }}>
                            <ThunderboltOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                            <Title level={4} type="secondary" style={{ marginTop: 16 }}>
                                Enter transaction details and click Predict
                            </Title>
                        </Card>
                    )}
                </Col>
            </Row>
        </div>
    );
}
