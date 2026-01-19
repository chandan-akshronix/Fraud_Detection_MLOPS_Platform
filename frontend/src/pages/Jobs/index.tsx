/**
 * Jobs Page
 * Manage scheduled monitoring jobs.
 */
import { useState } from 'react';
import {
    Card, Table, Tag, Button, Typography, Row, Col, Space,
    Modal, Form, Select, Input, Switch, message, Statistic, Dropdown
} from 'antd';
import {
    ScheduleOutlined, PlayCircleOutlined, PauseOutlined, ReloadOutlined,
    PlusOutlined, DeleteOutlined, MoreOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobService, ScheduledJob } from '@/services/jobService';

const { Title, Text } = Typography;
const { Option } = Select;

export function Jobs() {
    const [createModal, setCreateModal] = useState(false);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();

    // Fetch jobs
    const { data: jobsData, isLoading } = useQuery({
        queryKey: ['jobs'],
        queryFn: () => jobService.listJobs(),
    });

    // Fetch job types
    const { data: typesData } = useQuery({
        queryKey: ['jobTypes'],
        queryFn: () => jobService.getJobTypes(),
    });

    // Create job mutation
    const createMutation = useMutation({
        mutationFn: jobService.createJob,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            setCreateModal(false);
            form.resetFields();
            message.success('Job created');
        },
    });

    // Run job mutation
    const runMutation = useMutation({
        mutationFn: jobService.runJob,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            message.success('Job triggered');
        },
    });

    // Enable/disable mutation
    const toggleMutation = useMutation({
        mutationFn: ({ jobId, enabled }: { jobId: string; enabled: boolean }) =>
            enabled ? jobService.enableJob(jobId) : jobService.disableJob(jobId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: jobService.deleteJob,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            message.success('Job deleted');
        },
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'COMPLETED': return 'green';
            case 'RUNNING': return 'blue';
            case 'FAILED': return 'red';
            case 'PENDING': return 'default';
            default: return 'default';
        }
    };

    const getJobTypeLabel = (type: string) => {
        const labels: Record<string, string> = {
            DRIFT_CHECK: 'Drift Check',
            BIAS_CHECK: 'Bias Check',
            PERFORMANCE_CHECK: 'Performance Check',
            MODEL_RETRAIN: 'Model Retrain',
            DATA_CLEANUP: 'Data Cleanup',
        };
        return labels[type] || type;
    };

    const columns = [
        {
            title: 'Job Type',
            dataIndex: 'job_type',
            key: 'job_type',
            render: (type: string) => (
                <Tag color="blue">{getJobTypeLabel(type)}</Tag>
            ),
        },
        {
            title: 'Schedule',
            dataIndex: 'schedule',
            key: 'schedule',
            render: (schedule: string) => (
                <Text code>{schedule}</Text>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Tag color={getStatusColor(status)}>{status}</Tag>
            ),
        },
        {
            title: 'Enabled',
            dataIndex: 'enabled',
            key: 'enabled',
            render: (enabled: boolean, record: ScheduledJob) => (
                <Switch
                    checked={enabled}
                    onChange={(checked) => toggleMutation.mutate({ jobId: record.id, enabled: checked })}
                    loading={toggleMutation.isPending}
                />
            ),
        },
        {
            title: 'Last Run',
            dataIndex: 'last_run',
            key: 'last_run',
            render: (date: string) => date ? new Date(date).toLocaleString() : '-',
        },
        {
            title: 'Next Run',
            dataIndex: 'next_run',
            key: 'next_run',
            render: (date: string) => new Date(date).toLocaleString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: ScheduledJob) => (
                <Space>
                    <Button
                        size="small"
                        icon={<PlayCircleOutlined />}
                        onClick={() => runMutation.mutate(record.id)}
                        loading={runMutation.isPending}
                    >
                        Run Now
                    </Button>
                    <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => {
                            Modal.confirm({
                                title: 'Delete Job',
                                content: 'Are you sure you want to delete this job?',
                                onOk: () => deleteMutation.mutate(record.id),
                            });
                        }}
                    />
                </Space>
            ),
        },
    ];

    const jobs = jobsData?.data || [];
    const activeCount = jobs.filter((j: ScheduledJob) => j.enabled).length;

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Scheduled Jobs</Title>
                    <Text type="secondary">Manage automated monitoring tasks</Text>
                </div>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setCreateModal(true)}
                >
                    Create Job
                </Button>
            </div>

            {/* Summary Cards */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Total Jobs"
                            value={jobs.length}
                            prefix={<ScheduleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Active"
                            value={activeCount}
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Disabled"
                            value={jobs.length - activeCount}
                            valueStyle={{ color: '#8c8c8c' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Job Types"
                            value={typesData?.data?.length || 5}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Jobs Table */}
            <Card>
                <Table
                    loading={isLoading}
                    dataSource={jobs}
                    columns={columns}
                    rowKey="id"
                    pagination={{
                        pageSize: 10,
                        showTotal: (total) => `Total ${total} jobs`,
                    }}
                />
            </Card>

            {/* Create Job Modal */}
            <Modal
                title="Create Scheduled Job"
                open={createModal}
                onCancel={() => {
                    setCreateModal(false);
                    form.resetFields();
                }}
                onOk={() => form.submit()}
                confirmLoading={createMutation.isPending}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={(values) => createMutation.mutate(values)}
                >
                    <Form.Item
                        name="job_type"
                        label="Job Type"
                        rules={[{ required: true, message: 'Please select a job type' }]}
                    >
                        <Select placeholder="Select job type">
                            {typesData?.data?.map((t: any) => (
                                <Option key={t.type} value={t.type}>
                                    {getJobTypeLabel(t.type)} - {t.description}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="schedule"
                        label="Schedule (Cron)"
                        tooltip="Cron expression: minute hour day month weekday"
                    >
                        <Input placeholder="0 * * * * (every hour)" />
                    </Form.Item>

                    <Form.Item
                        name="model_id"
                        label="Model ID (Optional)"
                    >
                        <Input placeholder="Leave blank for all models" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}
