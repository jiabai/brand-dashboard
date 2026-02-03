export const buildTrendChartConfig = (trendData, token) => {
  if (!Array.isArray(trendData) || trendData.length === 0) return null;

  const lineColor = token?.colorPrimary;
  const textColor = token?.colorTextSecondary;
  const successColor = token?.colorSuccess;
  const errorColor = token?.colorError;

  return {
    data: trendData,
    xField: 'dateLabel',
    legend: false,
    children: [
      {
        type: 'line',
        yField: 'mentionRatePct',
        style: {
          stroke: lineColor,
          lineWidth: 2,
        },
        axis: {
          y: {
            position: 'left',
            label: {
              formatter: (v) => `${v}%`,
              style: { fill: textColor },
            },
          },
        },
        point: {
          size: 4,
          shape: 'circle',
          style: { fill: lineColor, stroke: lineColor },
        },
        tooltip: {
          name: '提及率',
          channel: 'y',
          valueFormatter: (v) => `${Number(v).toFixed(2)}%`,
        },
      },
      {
        type: 'interval',
        yField: 'deltaPct',
        axis: {
          y: {
            position: 'right',
            label: {
              formatter: (v) => `${v}%`,
              style: { fill: textColor },
            },
          },
        },
        style: {
          fill: (datum) => (datum.deltaPct >= 0 ? successColor : errorColor),
          fillOpacity: 0.75,
          radius: [4, 4, 0, 0],
        },
        tooltip: {
          name: '日变化',
          channel: 'y',
          valueFormatter: (v) => `${v >= 0 ? '+' : ''}${Number(v).toFixed(2)}%`,
        },
      },
    ],
    axis: {
      x: {
        label: {
          style: { fill: textColor },
        },
        tick: false,
      },
    },
    tooltip: {
      shared: true,
    },
  };
};
