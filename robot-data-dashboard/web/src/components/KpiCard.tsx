import { Card, Statistic } from "antd";

interface Props {
  title: string;
  value: number | string;
  suffix?: string;
  sub?: string;
  color?: string;
}

export default function KpiCard({ title, value, suffix, sub, color }: Props) {
  return (
    <Card size="small" hoverable>
      <Statistic title={title} value={value} suffix={suffix} valueStyle={color ? { color } : undefined} />
      {sub && <div style={{ marginTop: 8, color: "#8c8c8c", fontSize: 12 }}>{sub}</div>}
    </Card>
  );
}
