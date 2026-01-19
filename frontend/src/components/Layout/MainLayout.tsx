/**
 * Main Layout Component
 * Sidebar navigation with header and content area.
 */
import { useState } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    DashboardOutlined,
    DatabaseOutlined,
    ExperimentOutlined,
    AppstoreOutlined,
    LineChartOutlined,
    AlertOutlined,
    SettingOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    ThunderboltOutlined,
    SwapOutlined,
    ClockCircleOutlined,
    SyncOutlined,
    BlockOutlined,
} from '@ant-design/icons';
import type { ReactNode } from 'react';

const { Sider, Content, Header } = Layout;

interface MainLayoutProps {
    children: ReactNode;
}

const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/data', icon: <DatabaseOutlined />, label: 'Data Registry' },
    { key: '/training', icon: <ExperimentOutlined />, label: 'Training' },
    { key: '/models', icon: <AppstoreOutlined />, label: 'Model Registry' },
    { key: '/models/compare', icon: <SwapOutlined />, label: 'Compare Models' },
    { key: '/inference', icon: <ThunderboltOutlined />, label: 'Inference' },
    { key: '/monitoring', icon: <LineChartOutlined />, label: 'Monitoring' },
    { key: '/jobs', icon: <ClockCircleOutlined />, label: 'Jobs' },
    { key: '/retraining', icon: <SyncOutlined />, label: 'Retraining' },
    { key: '/ab-testing', icon: <BlockOutlined />, label: 'A/B Testing' },
    { key: '/alerts', icon: <AlertOutlined />, label: 'Alerts' },
    { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
];




export function MainLayout({ children }: MainLayoutProps) {
    const [collapsed, setCollapsed] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider
                collapsible
                collapsed={collapsed}
                onCollapse={setCollapsed}
                trigger={null}
                theme="light"
                style={{
                    boxShadow: '2px 0 8px rgba(0, 0, 0, 0.05)',
                    position: 'fixed',
                    height: '100vh',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    zIndex: 100,
                }}
            >
                <div
                    style={{
                        height: 64,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: collapsed ? 'center' : 'flex-start',
                        padding: collapsed ? 0 : '0 16px',
                        borderBottom: '1px solid #f0f0f0',
                    }}
                >
                    {collapsed ? (
                        <span style={{ fontSize: 24 }}>🔮</span>
                    ) : (
                        <span style={{ fontSize: 18, fontWeight: 700, color: '#2563EB' }}>
                            Shadow Hubble
                        </span>
                    )}
                </div>
                <Menu
                    mode="inline"
                    selectedKeys={[location.pathname]}
                    items={menuItems}
                    onClick={({ key }) => navigate(key)}
                    style={{ borderRight: 0 }}
                />
            </Sider>

            <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
                <Header
                    style={{
                        background: '#fff',
                        padding: '0 24px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        boxShadow: '0 1px 4px rgba(0, 0, 0, 0.05)',
                        position: 'sticky',
                        top: 0,
                        zIndex: 99,
                    }}
                >
                    <div
                        onClick={() => setCollapsed(!collapsed)}
                        style={{ cursor: 'pointer', fontSize: 18 }}
                    >
                        {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <AlertOutlined style={{ fontSize: 18 }} />
                        <div
                            style={{
                                width: 32,
                                height: 32,
                                borderRadius: '50%',
                                background: '#2563EB',
                                color: 'white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: 600,
                            }}
                        >
                            U
                        </div>
                    </div>
                </Header>

                <Content
                    style={{
                        padding: 24,
                        background: '#f5f5f5',
                        minHeight: 'calc(100vh - 64px)',
                    }}
                >
                    {children}
                </Content>
            </Layout>
        </Layout>
    );
}
