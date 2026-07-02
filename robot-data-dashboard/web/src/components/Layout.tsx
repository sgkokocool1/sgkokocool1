import { Layout, Menu, Button, Space, Typography } from "antd";
import {
  DashboardOutlined,
  PieChartOutlined,
  ApartmentOutlined,
  UnorderedListOutlined,
  DatabaseOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import { Link, Outlet, useLocation } from "react-router-dom";
import { triggerSync } from "../api/client";
import { message } from "antd";

const { Header, Sider, Content } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: <Link to="/">总览</Link> },
  { key: "/distribution", icon: <PieChartOutlined />, label: <Link to="/distribution">数据分布</Link> },
  { key: "/pipeline", icon: <ApartmentOutlined />, label: <Link to="/pipeline">处理流水线</Link> },
  { key: "/episodes", icon: <UnorderedListOutlined />, label: <Link to="/episodes">Episode 明细</Link> },
  { key: "/storage", icon: <DatabaseOutlined />, label: <Link to="/storage">存储</Link> },
];

export default function AppLayout() {
  const loc = useLocation();

  const onSync = async () => {
    try {
      const res = await triggerSync();
      message.success(`同步完成，episodes=${res.episodes_synced}`);
    } catch {
      message.error("同步失败，请检查 API 与数据库");
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsedWidth={64}>
        <div style={{ color: "#fff", padding: 16, fontWeight: 600 }}>Robot Stats</div>
        <Menu theme="dark" mode="inline" selectedKeys={[loc.pathname]} items={items} />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", padding: "0 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            机器人数据统计大看板
          </Typography.Title>
          <Space>
            <Button icon={<SyncOutlined />} onClick={onSync}>
              手动同步
            </Button>
          </Space>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
