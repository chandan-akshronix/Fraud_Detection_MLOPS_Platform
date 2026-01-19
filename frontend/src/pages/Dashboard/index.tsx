/**
 * Dashboard Page
 * Overview of platform status and key metrics.
 */
import { Row, Col, Card, Statistic, Table, Tag, Typography } from 'antd';
import {
    DatabaseOutlined,
    ExperimentOutlined,
    AppstoreOutlined,
    AlertOutlined,
    ArrowUpOutlined,
    ArrowDownOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const { Title, Text } = Typography;

// Mock data - will be replaced with API calls
const mockMetrics = [
    { name: 'Jan 1', predictions: 4000, drift: 0.05 },
    { name: 'Jan 2', predictions: 3000, drift: 0.08 },
    { name: 'Jan 3', predictions: 5000, drift: 0.12 },
    { name: 'Jan 4', predictions: 4500, drift: 0.09 },
    { name: 'Jan 5', predictions: 6000, drift: 0.15 },
    { name: 'Jan 6', predictions: 5500, drift: 0.11 },
    { name: 'Jan 7', predictions: 7000, drift: 0.18 },
];

const recentAlerts = [
    { id: '1', type: 'DRIFT', message: 'Data drift detected in amount feature', severity: 'warning', time: '2 hours ago' },
    { id: '2', type: 'PERFORMANCE', message: 'Precision dropped below baseline', severity: 'critical', time: '5 hours ago' },
    { id: '3', type: 'BIAS', message: 'Age group disparity increased', severity: 'info', time: '1 day ago' },
];

const alertColumns = [
    { title: 'Type', dataIndex: 'type', key: 'type' },
    { title: 'Message', dataIndex: 'message', key: 'message' },
    {
        title: 'Severity',
        dataIndex: 'severity',
        key: 'severity',
        render: (severity: string) => {
            const colors: Record<string, string> = {
                critical: 'red',
                warning: 'orange',
                info: 'blue',
            };
            return <Tag color={colors[severity]}>{severity.toUpperCase()}</Tag>;
        },
    },
    { title: 'Time', dataIndex: 'time', key: 'time' },
];

export function Dashboard() {
    return (
        <div className="fade-in">
            <div className="page-header">
                <Title level={2} style={{ margin: 0 }}>Dashboard</Title>
                <Text type="secondary">Overview of your ML platform</Text>
            </div>

            {/* Stats Cards */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Datasets"
                            value={12}
                            prefix={<DatabaseOutlined />}
                            valueStyle={{ color: '#2563EB' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Training Jobs"
                            value={8}
                            prefix={<ExperimentOutlined />}
                            suffix={<Text type="secondary" style={{ fontSize: 14 }}> / 3 active</Text>}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Production Models"
                            value={2}
                            prefix={<AppstoreOutlined />}
                            valueStyle={{ color: '#059669' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Active Alerts"
                            value={3}
                            prefix={<AlertOutlined />}
                            valueStyle={{ color: '#DC2626' }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Charts */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} lg={16}>
                    <Card title="Predictions Over Time" extra={<a href="#">View Details</a>}>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={mockMetrics}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" />
                                <YAxis />
                                <Tooltip />
                                <Line type="monotone" dataKey="predictions" stroke="#2563EB" strokeWidth={2} />
                            </LineChart>
                        </ResponsiveContainer>
                    </Card>
                </Col>
                <Col xs={24} lg={8}>
                    <Card title="Model Performance">
                        <Row gutter={[16, 16]}>
                            <Col span={12}>
                                <Statistic
                                    title="Precision"
                                    value={92.5}
                                    suffix="%"
                                    prefix={<ArrowUpOutlined />}
                                    valueStyle={{ color: '#059669', fontSize: 24 }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="Recall"
                                    value={88.3}
                                    suffix="%"
                                    prefix={<ArrowUpOutlined />}
                                    valueStyle={{ color: '#059669', fontSize: 24 }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="F1 Score"
                                    value={90.2}
                                    suffix="%"
                                    valueStyle={{ fontSize: 24 }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="AUC-ROC"
                                    value={95.1}
                                    suffix="%"
                                    prefix={<ArrowDownOutlined />}
                                    valueStyle={{ color: '#DC2626', fontSize: 24 }}
                                />
                            </Col>
                        </Row>
                    </Card>
                </Col>
            </Row>

            {/* Recent Alerts */}
            <Card title="Recent Alerts" extra={<a href="/alerts">View All</a>}>
                <Table
                    dataSource={recentAlerts}
                    columns={alertColumns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                />
            </Card>
        </div>
    );
}
