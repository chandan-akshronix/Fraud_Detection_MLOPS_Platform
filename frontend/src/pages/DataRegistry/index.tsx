/**
 * Data Registry Page
 * Upload and manage datasets.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Table, Button, Modal, Form, Input, Upload, message, Tag, Typography, Space, Radio, Row, Col, InputNumber, Divider } from 'antd';
import { PlusOutlined, UploadOutlined, EyeOutlined, DeleteOutlined, DownloadOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { datasetService } from '@/services/datasetService';
import { featureService } from '@/services/featureService';
import type { UploadFile } from 'antd/es/upload/interface';

const { Title, Text } = Typography;

export function DataRegistry() {
    const navigate = useNavigate();
    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [datasetToDelete, setDatasetToDelete] = useState<{ id: string; name: string } | null>(null);
    const [previewModalOpen, setPreviewModalOpen] = useState(false);
    const [previewData, setPreviewData] = useState<{ columns: string[]; rows: unknown[]; total_rows: number } | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [previewDatasetName, setPreviewDatasetName] = useState('');
    const [form] = Form.useForm();
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const queryClient = useQueryClient();
    const [previewDatasetId, setPreviewDatasetId] = useState('');
    const [computeModalOpen, setComputeModalOpen] = useState(false);
    const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
    const [selectedDatasetName, setSelectedDatasetName] = useState<string>('');
    const [computeForm] = Form.useForm();

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

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: (id: string) => datasetService.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['datasets'] });
            message.success('Dataset deleted successfully');
            setDeleteModalOpen(false);
            setDatasetToDelete(null);
        },
        onError: () => {
            message.error('Failed to delete dataset');
        },
    });

    // Compute features mutation
    const computeMutation = useMutation({
        mutationFn: (values: any) => featureService.computeFeatures({
            ...values,
            dataset_id: selectedDatasetId!,
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['featureSets'] });
            message.success('Feature computation started!');
            setComputeModalOpen(false);
            computeForm.resetFields();
            navigate('/training');
        },
        onError: (error: Error) => {
            message.error(error.message || 'Failed to start computation');
        },
    });

    const handleDeleteClick = (id: string, name: string) => {
        setDatasetToDelete({ id, name });
        setDeleteModalOpen(true);
    };

    const handleConfirmDelete = () => {
        if (datasetToDelete) {
            deleteMutation.mutate(datasetToDelete.id);
        }
    };

    const handlePreview = async (id: string, name: string) => {
        setPreviewDatasetId(id);
        setPreviewDatasetName(name);
        setPreviewLoading(true);
        setPreviewModalOpen(true);
        try {
            const data = await datasetService.preview(id, 10);
            setPreviewData(data);
        } catch (error) {
            message.error('Failed to load preview');
            setPreviewModalOpen(false);
        } finally {
            setPreviewLoading(false);
        }
    };

    const handleDownload = async () => {
        try {
            message.loading({ content: 'Generating download link...', key: 'download' });
            const { download_url } = await datasetService.getDownloadUrl(previewDatasetId);

            // Open download URL in new tab
            window.open(download_url, '_blank');
            message.success({ content: 'Download started!', key: 'download' });
        } catch (error) {
            message.error({ content: 'Failed to generate download link', key: 'download' });
        }
    };

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
            title: 'File Type',
            dataIndex: 'file_format',
            key: 'file_format',
            render: (format: string) => (
                <Tag color={format === 'csv' ? 'blue' : format === 'parquet' ? 'purple' : 'orange'}>
                    {format?.toUpperCase() || '-'}
                </Tag>
            ),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: unknown, record: { id: string; name: string }) => (
                <Space>
                    <Button
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handlePreview(record.id, record.name)}
                        title="Preview"
                    />
                    <Button
                        size="small"
                        icon={<ThunderboltOutlined />}
                        style={{ color: '#FAAD14' }}
                        onClick={() => {
                            setSelectedDatasetId(record.id);
                            setSelectedDatasetName(record.name);
                            setComputeModalOpen(true);
                            computeForm.setFieldsValue({ name: `${record.name}_features` });
                        }}
                        title="Compute Features"
                    />
                    <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeleteClick(record.id, record.name)}
                        loading={deleteMutation.isPending && datasetToDelete?.id === record.id}
                        title="Delete"
                    />
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

            {/* Delete Confirmation Modal */}
            <Modal
                title="Delete Dataset"
                open={deleteModalOpen}
                onCancel={() => {
                    setDeleteModalOpen(false);
                    setDatasetToDelete(null);
                }}
                onOk={handleConfirmDelete}
                okText="Delete"
                okType="danger"
                confirmLoading={deleteMutation.isPending}
            >
                <p>Are you sure you want to delete "{datasetToDelete?.name}"?</p>
                <p style={{ color: '#ff4d4f' }}>This action cannot be undone.</p>
            </Modal>

            {/* Preview Modal */}
            <Modal
                title={`Preview: ${previewDatasetName}`}
                open={previewModalOpen}
                onCancel={() => {
                    setPreviewModalOpen(false);
                    setPreviewData(null);
                    setPreviewDatasetId('');
                }}
                footer={[
                    <Button
                        key="download"
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={handleDownload}
                        disabled={!previewData}
                    >
                        Download Dataset
                    </Button>,
                    <Button
                        key="close"
                        onClick={() => {
                            setPreviewModalOpen(false);
                            setPreviewData(null);
                            setPreviewDatasetId('');
                        }}
                    >
                        Close
                    </Button>
                ]}
                width={800}
            >
                {previewLoading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        Loading preview...
                    </div>
                ) : previewData ? (
                    <Table
                        dataSource={previewData.rows.map((row, idx) => ({ key: idx, ...row as object }))}
                        columns={previewData.columns.map(col => ({
                            title: col,
                            dataIndex: col,
                            key: col,
                            ellipsis: true,
                        }))}
                        pagination={false}
                        scroll={{ x: true }}
                        size="small"
                    />
                ) : (
                    <div>No data available</div>
                )}
                {previewData && (
                    <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
                        Showing {previewData.rows.length} of {previewData.total_rows} rows
                    </Text>
                )}
            </Modal>

            {/* Compute Features Modal */}
            <Modal
                title={`Compute Features: ${selectedDatasetName}`}
                open={computeModalOpen}
                onCancel={() => {
                    setComputeModalOpen(false);
                    computeForm.resetFields();
                }}
                onOk={() => computeForm.submit()}
                confirmLoading={computeMutation.isPending}
                width={600}
            >
                <Form
                    form={computeForm}
                    layout="vertical"
                    onFinish={(values) => computeMutation.mutate(values)}
                    initialValues={{
                        transaction_features: true,
                        behavioral_features: true,
                        temporal_features: true,
                        aggregation_features: true,
                        enable_feature_selection: true,
                        max_features: 30
                    }}
                >
                    <Form.Item
                        name="name"
                        label="Feature Set Name"
                        rules={[{ required: true, message: 'Please enter a name' }]}
                    >
                        <Input placeholder="e.g., fraud_features_v1" />
                    </Form.Item>

                    <Form.Item name="description" label="Description">
                        <Input.TextArea placeholder="Optional description" rows={2} />
                    </Form.Item>

                    <Title level={5}>Feature Configuration</Title>
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="transaction_features" label="Transaction Features" valuePropName="checked">
                                <Radio.Group optionType="button" buttonStyle="solid">
                                    <Radio value={true}>Enable</Radio>
                                    <Radio value={false}>Disable</Radio>
                                </Radio.Group>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="behavioral_features" label="Behavioral Features" valuePropName="checked">
                                <Radio.Group optionType="button" buttonStyle="solid">
                                    <Radio value={true}>Enable</Radio>
                                    <Radio value={false}>Disable</Radio>
                                </Radio.Group>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="temporal_features" label="Temporal Features" valuePropName="checked">
                                <Radio.Group optionType="button" buttonStyle="solid">
                                    <Radio value={true}>Enable</Radio>
                                    <Radio value={false}>Disable</Radio>
                                </Radio.Group>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="aggregation_features" label="Aggregation Features" valuePropName="checked">
                                <Radio.Group optionType="button" buttonStyle="solid">
                                    <Radio value={true}>Enable</Radio>
                                    <Radio value={false}>Disable</Radio>
                                </Radio.Group>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Divider />

                    <Title level={5}>Feature Selection</Title>
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="enable_feature_selection" label="Auto Selection" valuePropName="checked">
                                <Radio.Group optionType="button" buttonStyle="solid">
                                    <Radio value={true}>Enable</Radio>
                                    <Radio value={false}>Disable</Radio>
                                </Radio.Group>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="max_features" label="Max Features">
                                <InputNumber min={5} max={100} style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>
                    </Row>
                </Form>
            </Modal>
        </div>
    );
}