import ReactECharts from "echarts-for-react";

interface Stage {
  label: string;
  count: number;
}

interface Props {
  stages: Stage[];
  height?: number;
}

export default function FunnelChart({ stages, height = 320 }: Props) {
  const option = {
    tooltip: { trigger: "item", formatter: "{b}: {c}" },
    series: [
      {
        type: "funnel",
        left: "10%",
        width: "80%",
        sort: "descending",
        label: { show: true, position: "inside" },
        data: stages.map((s) => ({ name: s.label, value: s.count })),
      },
    ],
  };
  return <ReactECharts option={option} style={{ height }} />;
}
