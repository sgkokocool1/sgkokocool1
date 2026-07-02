import ReactECharts from "echarts-for-react";

interface Item {
  name: string;
  value: number;
}

interface Props {
  title?: string;
  data: Item[];
  height?: number;
}

export default function PieChart({ title, data, height = 280 }: Props) {
  const option = {
    title: title ? { text: title, left: "center", textStyle: { fontSize: 14 } } : undefined,
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["40%", "65%"],
        data,
        label: { formatter: "{b}: {c} ({d}%)" },
      },
    ],
  };
  return <ReactECharts option={option} style={{ height }} />;
}
