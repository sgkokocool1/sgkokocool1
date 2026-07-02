import { useEffect, useState } from "react";
import { Card, Table, Spin } from "antd";
import { fetchSourceDist } from "../api/client";
import PieChart from "../components/PieChart";

export default function DistributionPage() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<{ key: string; total: number; success: number; failed: number; imported: number; frames: number }[]>([]);

  useEffect(() => {
    fetchSourceDist().then((r) => {
      setItems(r.items as typeof items);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spin />;

  return (
    <div>
      <Card title="按来源分布">
        <PieChart data={items.map((i) => ({ name: i.key, value: i.total }))} />
      </Card>
      <Card title="来源明细表" style={{ marginTop: 16 }}>
        <Table
          rowKey="key"
          dataSource={items}
          columns={[
            { title: "来源", dataIndex: "key" },
            { title: "总数", dataIndex: "total" },
            { title: "成功", dataIndex: "success" },
            { title: "失败", dataIndex: "failed" },
            { title: "已导入", dataIndex: "imported" },
            { title: "帧数", dataIndex: "frames" },
          ]}
        />
      </Card>
    </div>
  );
}
