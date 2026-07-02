import { useEffect, useState } from "react";
import { Card, Table, Select, Space, Spin, Tag } from "antd";
import { fetchEpisodes } from "../api/client";

export default function EpisodesPage() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<unknown[]>([]);
  const [total, setTotal] = useState(0);
  const [source, setSource] = useState<string | undefined>();
  const [stage, setStage] = useState<string | undefined>();

  const load = (offset = 0) => {
    setLoading(true);
    const params: Record<string, string | number> = { limit: 50, offset };
    if (source) params.source = source;
    if (stage) params.stage = stage;
    fetchEpisodes(params).then((r) => {
      setItems(r.items);
      setTotal(r.total);
      setLoading(false);
    });
  };

  useEffect(() => {
    load();
  }, [source, stage]);

  return (
    <Card
      title="Episode 明细"
      extra={
        <Space>
          <Select allowClear placeholder="来源" style={{ width: 120 }} onChange={setSource} options={[
            { value: "ros", label: "ros" },
            { value: "sim", label: "sim" },
            { value: "mp4", label: "mp4" },
          ]} />
          <Select allowClear placeholder="阶段" style={{ width: 140 }} onChange={setStage} options={[
            { value: "pending_import", label: "待构建" },
            { value: "imported", label: "已导入" },
            { value: "raw_archived", label: "已归档" },
          ]} />
        </Space>
      }
    >
      <Table
        loading={loading}
        rowKey="id"
        dataSource={items as Record<string, unknown>[]}
        pagination={{ total, pageSize: 50, onChange: (p) => load((p - 1) * 50) }}
        columns={[
          { title: "日期", dataIndex: "collect_date", width: 110 },
          { title: "路径", dataIndex: "path", ellipsis: true },
          { title: "来源", dataIndex: "source", width: 80 },
          { title: "任务", dataIndex: "task", ellipsis: true },
          {
            title: "成功",
            dataIndex: "success",
            width: 70,
            render: (v: boolean) => (v ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag>),
          },
          { title: "帧数", dataIndex: "frames", width: 70 },
          { title: "阶段", dataIndex: "stage", width: 110 },
          { title: "导入至", dataIndex: "imported_to", ellipsis: true },
        ]}
      />
    </Card>
  );
}
