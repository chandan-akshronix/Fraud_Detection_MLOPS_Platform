/**
 * Data Registry Page
 * Upload and manage datasets.
 */
import { useState } from 'react';
import { Card, Table, Button, Modal, Form, Input, Upload, message, Tag, Typography, Space } from 'antd';
import { PlusOutlined, UploadOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { datasetService } from '@/services/datasetService';
import type { UploadFile } from 'antd/es/upload/interface';

const { Title, Text } = Typography;

export function DataRegistry() {
    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [form] = Form.useForm();
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const queryClient = useQueryClient();

    // Fetch datasets
    const { data, isLoading } = useQuery({
        queryKey: ['datasets'],
        queryFn: () => datasetService.list(),
    });

    // Upload mutation
    const uploadMutation = useMutation({
        mutationFn: async (values: { name: string; description: string }) => {
            if (fileList.length === 0 || !fileList[0].originFileObj) {
                throw new Error('Please select a file');
            }
            return datasetService.create(values.name, fileList[0].originFileObj, values.description);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['datasets'] });
            setUploadModalOpen(false);
            form.resetFields();
            setFileList([]);
            message.success('Dataset uploaded successfully');
        },
        onError: (error: Error) => {
            message.error(error.message || 'Failed to upload dataset');
        },
    });

    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (name: string) => <Text strong>{name}</Text>,
        },
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            render: (version: string) => <Tag>{version}</Tag>,
        },
        {
            title: 'Rows',
            dataIndex: 'row_count',
            key: 'row_count',
            render: (count: number) => count?.toLocaleString() || '-',
        },
        {
            title: 'Columns',
            dataIndex: 'column_count',
            key: 'column_count',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                const colors: Record<string, string> = {
                    ACTIVE: 'green',
                    PROCESSING: 'blue',
                    ARCHIVED: 'gray',
                };
                return <Tag color={colors[status] || 'default'}>{status}</Tag>;
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
            render: () => (
                <Space>
                    <Button size="small" icon={<EyeOutlined />}>Preview</Button>
                    <Button size="small" danger icon={<DeleteOutlined />}>Delete</Button>
                </Space>
            ),
        },
    ];

    return (
        <div className="fade-in">
            <div className="page-header">
                <div>
                    <Title level={2} style={{ margin: 0 }}>Data Registry</Title>
                    <Text type="secondary">Manage your datasets for model training</Text>
                </div>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setUploadModalOpen(true)}
                >
                    Upload Dataset
                </Button>
            </div>

            <Card>
                <Table
                    dataSource={data?.data || []}
                    columns={columns}
                    loading={isLoading}
                    rowKey="id"
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (total) => `Total ${total} datasets`,
                    }}
                />
            </Card>

            {/* Upload Modal */}
            <Modal
                title="Upload Dataset"
                open={uploadModalOpen}
                onCancel={() => {
                    setUploadModalOpen(false);
                    form.resetFields();
                    setFileList([]);
                }}
                onOk={() => form.submit()}
                confirmLoading={uploadMutation.isPending}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={(values) => uploadMutation.mutate(values)}
                >
                    <Form.Item
                        name="name"
                        label="Dataset Name"
                        rules={[{ required: true, message: 'Please enter a name' }]}
                    >
                        <Input placeholder="e.g., fraud_train_2026" />
                    </Form.Item>

                    <Form.Item
                        name="description"
                        label="Description"
                    >
                        <Input.TextArea placeholder="Optional description" rows={3} />
                    </Form.Item>

                    <Form.Item
                        label="File"
                        required
                        rules={[{ required: true, message: 'Please upload a file' }]}
                    >
                        <Upload
                            beforeUpload={() => false}
                            fileList={fileList}
                            onChange={({ fileList }) => setFileList(fileList)}
                            accept=".csv,.parquet,.json"
                            maxCount={1}
                        >
                            <Button icon={<UploadOutlined />}>Select File</Button>
                        </Upload>
                        <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                            Supported formats: CSV, Parquet, JSON
                        </Text>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}
