import { useEffect, useState } from "react";
import { Card, Spin } from "antd";
import ReactECharts from "echarts-for-react";
import { fetchStorage } from "../api/client";

export default function StoragePage() {
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<{ snapshot_at: string; raw_gb: number; lerobot_gb: number; staging_gb: number }[]>([]);

  useEffect(() => {
    fetchStorage().then((r) => {
      setHistory(r.history || []);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spin />;

  const option = {
    tooltip: { trigger: "axis" },
    legend: { data: ["raw", "lerobot", "staging"] },
    xAxis: { type: "category", data: history.map((h) => h.snapshot_at.slice(0, 16)) },
    yAxis: { type: "value", name: "GB" },
    series: [
      { name: "raw", type: "bar", stack: "s", data: history.map((h) => h.raw_gb) },
      { name: "lerobot", type: "bar", stack: "s", data: history.map((h) => h.lerobot_gb) },
      { name: "staging", type: "bar", stack: "s", data: history.map((h) => h.staging_gb) },
    ],
  };

  return (
    <Card title="存储占用趋势">
      <ReactECharts option={option} style={{ height: 400 }} />
    </Card>
  );
}
