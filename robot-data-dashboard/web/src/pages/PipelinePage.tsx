import { useEffect, useState } from "react";
import { Card, Table, Spin } from "antd";
import { fetchFunnel, fetchJobs } from "../api/client";
import FunnelChart from "../components/FunnelChart";

export default function PipelinePage() {
  const [loading, setLoading] = useState(true);
  const [stages, setStages] = useState<{ label: string; count: number }[]>([]);
  const [jobs, setJobs] = useState<unknown[]>([]);

  useEffect(() => {
    Promise.all([fetchFunnel(), fetchJobs(50)]).then(([f, j]) => {
      setStages(f.stages.map((s) => ({ label: s.label, count: s.count })));
      setJobs(j.items);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spin />;

  return (
    <div>
      <Card title="处理漏斗">
        <FunnelChart stages={stages} />
      </Card>
      <Card title="任务流历史" style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={jobs as Record<string, unknown>[]}
          columns={[
            { title: "ID", dataIndex: "id" },
            { title: "类型", dataIndex: "job_type" },
            { title: "状态", dataIndex: "status" },
            { title: "触发", dataIndex: "triggered_by" },
            { title: "导入", dataIndex: "episodes_ok" },
            { title: "失败", dataIndex: "episodes_fail" },
            { title: "开始", dataIndex: "started_at" },
          ]}
        />
      </Card>
    </div>
  );
}
