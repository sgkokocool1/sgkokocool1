import { useEffect, useState } from "react";
import { Col, Row, Card, Table, Spin, Progress } from "antd";
import KpiCard from "../components/KpiCard";
import PieChart from "../components/PieChart";
import FunnelChart from "../components/FunnelChart";
import TrendChart from "../components/TrendChart";
import { fetchOverview, fetchFunnel, fetchDailyTrend, fetchJobs, Overview } from "../api/client";

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [funnel, setFunnel] = useState<{ label: string; count: number }[]>([]);
  const [trend, setTrend] = useState<{ date: string; total: number; success: number; failed: number; imported: number }[]>([]);
  const [jobs, setJobs] = useState<unknown[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const [ov, fu, tr, jb] = await Promise.all([fetchOverview(), fetchFunnel(), fetchDailyTrend(), fetchJobs(10)]);
      setOverview(ov);
      setFunnel(fu.stages.map((s) => ({ label: s.label, count: s.count })));
      setTrend(tr.points);
      setJobs(jb.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, []);

  if (loading && !overview) return <Spin size="large" />;

  const ep = overview?.episodes;
  const pieData = Object.entries(overview?.by_source || {}).map(([name, v]) => ({ name, value: v.total }));
  const storage = overview?.storage;
  const storageTotal = (storage?.raw_gb || 0) + (storage?.lerobot_gb || 0) + (storage?.staging_gb || 0);

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={4}><KpiCard title="原始总数" value={ep?.total ?? 0} /></Col>
        <Col xs={24} sm={12} lg={4}><KpiCard title="成功" value={ep?.success ?? 0} sub={`${((ep?.success_rate ?? 0) * 100).toFixed(1)}%`} color="#52c41a" /></Col>
        <Col xs={24} sm={12} lg={4}><KpiCard title="失败" value={ep?.failed ?? 0} color="#ff4d4f" /></Col>
        <Col xs={24} sm={12} lg={4}><KpiCard title="已入数据集" value={ep?.imported ?? 0} color="#1677ff" /></Col>
        <Col xs={24} sm={12} lg={4}><KpiCard title="待处理" value={ep?.pending ?? 0} color="#faad14" /></Col>
        <Col xs={24} sm={12} lg={4}><KpiCard title="总帧数" value={ep?.frames_total ?? 0} /></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="数据来源分布">
            <PieChart data={pieData} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="处理漏斗">
            <FunnelChart stages={funnel} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="日采集趋势">
            <TrendChart points={trend} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="存储占用 (GB)">
            {storage && (
              <>
                <div style={{ marginBottom: 8 }}>raw {storage.raw_gb} GB</div>
                <Progress percent={storageTotal ? Math.round((storage.raw_gb / storageTotal) * 100) : 0} />
                <div style={{ margin: "8px 0" }}>lerobot {storage.lerobot_gb} GB</div>
                <Progress percent={storageTotal ? Math.round((storage.lerobot_gb / storageTotal) * 100) : 0} status="active" />
                <div style={{ margin: "8px 0" }}>staging {storage.staging_gb} GB</div>
                <Progress percent={storageTotal ? Math.round((storage.staging_gb / storageTotal) * 100) : 0} status="exception" />
              </>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="最近任务流" style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          size="small"
          dataSource={jobs as Record<string, unknown>[]}
          pagination={false}
          columns={[
            { title: "ID", dataIndex: "id", width: 60 },
            { title: "类型", dataIndex: "job_type" },
            { title: "状态", dataIndex: "status" },
            { title: "开始", dataIndex: "started_at" },
            { title: "成功", dataIndex: "episodes_ok" },
            { title: "失败", dataIndex: "episodes_fail" },
            { title: "耗时(s)", dataIndex: "duration_sec" },
          ]}
        />
      </Card>
    </div>
  );
}
