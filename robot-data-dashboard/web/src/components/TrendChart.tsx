import ReactECharts from "echarts-for-react";

interface Point {
  date: string;
  total: number;
  success: number;
  failed: number;
  imported: number;
}

interface Props {
  points: Point[];
  height?: number;
}

export default function TrendChart({ points, height = 300 }: Props) {
  const dates = points.map((p) => p.date);
  const option = {
    tooltip: { trigger: "axis" },
    legend: { data: ["总数", "成功", "失败", "已导入"] },
    xAxis: { type: "category", data: dates },
    yAxis: { type: "value" },
    series: [
      { name: "总数", type: "line", data: points.map((p) => p.total) },
      { name: "成功", type: "line", data: points.map((p) => p.success) },
      { name: "失败", type: "line", data: points.map((p) => p.failed) },
      { name: "已导入", type: "line", data: points.map((p) => p.imported) },
    ],
  };
  return <ReactECharts option={option} style={{ height }} />;
}
