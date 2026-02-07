import { Chart } from '@antv/g2';

// 更新元数据展示
const metaInfo = document.getElementById('meta-info');
if (metaInfo) {
  metaInfo.innerText = `舆情分析: 情感倾向分布 (甜甜圈图)`;
  metaInfo.style.color = '#A6A6A6';
}

// 1. 自定义数据 (总计 1000 以符合 60%, 20%, 20% 的比例)
const data = [
  { name: '正面', value: 600 },
  { name: '负面', value: 200 },
  { name: '中性', value: 200 },
];

const chart = new Chart({
  container: 'container',
  autoFit: true,
  theme: 'dark', // 保持深色主题适配页面背景
});

// 设置极坐标系并配置内半径实现环形效果
chart.coordinate({ type: 'theta', innerRadius: 0.6 });

chart
  .interval()
  .data(data)
  .transform({ type: 'stackY' })
  .encode('y', 'value')
  .encode('color', 'name')
  .style('stroke', '#1F1F1F')
  .style('inset', 1)
  .style('radius', 10)
  .scale('color', {
    // 为正面、负面、中性设置语义化颜色
    domain: ['正面', '负面', '中性'],
    range: ['#2582a1', '#c52125', '#f88c24'],
  })
  .label({ 
    text: (d) => `${d.name}：${d.value}条`, 
    fontSize: 17, // 21 * 0.8 ≈ 17
    fontWeight: 'bold',
    fill: '#fff',
    position: 'outside', // 类别名称和条数显示在外部
  })
  .label({
    text: (d) => `${((d.value / 1000) * 100).toFixed(0)}%`,
    fontSize: 18, // 12 * 1.5
    fill: '#fff',
    position: 'inside', // 关键：百分比显示在甜甜圈内部
    fontWeight: 'bold',
  })
  .animate('enter', { type: 'waveIn' })
  .legend({
    position: 'bottom',
    layout: { justifyContent: 'center' }
  });

chart.render();
