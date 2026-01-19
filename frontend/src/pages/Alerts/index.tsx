/**
 * Alerts Page
 * View and manage active alerts.
 */
import { useState } from 'react';
import {
    Card, Table, Tag, Button, Typography, Row, Col, Space,
    Statistic, Modal, Input, message, Badge
} from 'antd';
import {
    AlertOutlined, CheckCircleOutlined, ClockCircleOutlined,
    ExclamationCircleOutlined, WarningOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertService, Alert } from '@/services/alertService';

const { Title, Text, TextArea } = Typography;

export function Alerts() {
    const [acknowledgeModal, setAcknowledgeModal] = useState(false);
    const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
    const [resolutionNote, setResolutionNote] = useState('');
    const queryClient = useQueryClient();

    // Fetch alerts
    const { data: alertsData, isLoading } = useQuery({
        queryKey: ['alerts'],
        queryFn: () => alertService.listAlerts(),
    });

    // Acknowledge mutation
    const acknowledgeMutation = useMutation({
        mutationFn: ({ alertId, note }: { alertId: string; note?: string }) =>
            alertService.acknowledgeAlert(alertId, note),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            setAcknowledgeModal(false);
            setSelectedAlert(null);
            setResolutionNote('');
            message.success('Alert acknowledged');
        },
    });

    // Resolve mutation
    const resolveMutation = useMutation({
        mutationFn: ({ alertId, note }: { alertId: string; note?: string }) =>
            alertService.resolveAlert(alertId, note),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            message.success('Alert resolved');
        },
    });

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case 'CRITICAL': return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
            case 'WARNING': return <WarningOutlined style={{ color: '#faad14' }} />;
            case 'INFO': return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
            default: return null;
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'CRITICAL': return 'red';
            case 'WARNING': return 'orange';
            case 'INFO': return 'blue';
            default: return 'default';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ACTIVE': return 'red';
            case 'ACKNOWLEDGED': return 'orange';
            case 'RESOLVED': return 'green';
            default: return 'default';
        }
    };

    const columns = [
        {
            title: 'Severity',
            dataIndex: 'severity',
            key: 'severity',
            width: 100,
            render: (severity: string) => (
                <Space>
                    {getSeverityIcon(severity)}
                    <Tag color={getSeverityColor(severity)}>{severity}</Tag>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'alert_type',
            key: 'alert_type',
            width: 120,
            render: (type: string) => <Tag>{type}</Tag>,
        },
        {
            title: 'Title',
            dataIndex: 'title',
            key: 'title',
            render: (title: string) => <Text strong>{title}</Text>,
        },
        {
            title: 'Message',
            dataIndex: 'message',
            key: 'message',
            ellipsis: true,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 130,
            render: (status: string) => (
                <Tag color={getStatusColor(status)}>{status}</Tag>
            ),
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180,
            render: (date: string) => new Date(date).toLocaleString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 180,
            render: (_: any, record: Alert) => (
                <Space>
                    {record.status === 'ACTIVE' && (
                        <Button
                            size="small"
                            onClick={() => {
                                setSelectedAlert(record);
                                setAcknowledgeModal(true);
                            }}
                        >
                            Acknowledge
                        </Button>
                    )}
                    {record.status === 'ACKNOWLEDGED' && (
                        <Button
                            size="small"
                            type="primary"
                            onClick={() => resolveMutation.mutate({ alertId: record.id })}
                        >
                            Resolve
                        </Button>
                    )}
                    {record.status === 'RESOLVED' && (
                        <Tag icon={<CheckCircleOutlined />} color="success">
                            Resolved
                        </Tag>
                    )}
                </Space>
            ),
        },
    ];

    const summary = alertsData?.summary || { active: 0, acknowledged: 0, resolved: 0, critical: 0 };

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Alerts</Title>
                    <Text type="secondary">View and manage system alerts</Text>
                </div>
            </div>

            {/* Summary Cards */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Active Alerts"
                            value={summary.active}
                            prefix={<Badge status="error" />}
                            valueStyle={{ color: summary.active > 0 ? '#cf1322' : '#3f8600' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Critical"
                            value={summary.critical}
                            prefix={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                            valueStyle={{ color: summary.critical > 0 ? '#cf1322' : '#3f8600' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Acknowledged"
                            value={summary.acknowledged}
                            prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Resolved"
                            value={summary.resolved}
                            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                            valueStyle={{ color: '#3f8600' }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Alerts Table */}
            <Card title="All Alerts">
                <Table
                    loading={isLoading}
                    dataSource={alertsData?.data || []}
                    columns={columns}
                    rowKey="id"
                    pagination={{
                        pageSize: 10,
                        showTotal: (total) => `Total ${total} alerts`,
                    }}
                    rowClassName={(record) =>
                        record.status === 'ACTIVE' && record.severity === 'CRITICAL'
                            ? 'alert-critical'
                            : ''
                    }
                />
            </Card>

            {/* Acknowledge Modal */}
            <Modal
                title="Acknowledge Alert"
                open={acknowledgeModal}
                onCancel={() => {
                    setAcknowledgeModal(false);
                    setSelectedAlert(null);
                    setResolutionNote('');
                }}
                onOk={() => {
                    if (selectedAlert) {
                        acknowledgeMutation.mutate({
                            alertId: selectedAlert.id,
                            note: resolutionNote
                        });
                    }
                }}
                confirmLoading={acknowledgeMutation.isPending}
            >
                {selectedAlert && (
                    <>
                        <p><strong>Alert:</strong> {selectedAlert.title}</p>
                        <p><strong>Message:</strong> {selectedAlert.message}</p>
                        <Input.TextArea
                            placeholder="Add a note (optional)"
                            rows={4}
                            value={resolutionNote}
                            onChange={(e) => setResolutionNote(e.target.value)}
                        />
                    </>
                )}
            </Modal>
        </div>
    );
}
