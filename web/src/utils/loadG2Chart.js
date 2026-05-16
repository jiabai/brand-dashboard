let chartLoader;

export const loadG2Chart = async () => {
  if (!chartLoader) {
    chartLoader = import('@antv/g2').then((mod) => mod.Chart);
  }

  return chartLoader;
};
