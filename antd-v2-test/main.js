import { Chart } from '@antv/g2';

// 1. 数据定义
const response = {
    "status": "success",
    "data": [
        {
            "date": "20260127",
            "brand": "哈基桃电竞",
            "platform": "deepseek",
            "keyword": "三角洲陪玩",
            "mention_rate": 0.1613
        }
    ],
    "metadata": {
        "brand": "哈基桃电竞",
        "platform": "deepseek",
        "keyword": "三角洲陪玩",
        "start_date": "20260125",
        "end_date": "20260128",
        "calculation_method": "mention_rate_by_day",
        "points": 1
    }
};

// 填充元数据信息
const metaInfo = document.getElementById('meta-info');
if (metaInfo) {
  const { brand, platform, keyword } = response.metadata;
  metaInfo.innerText = `品牌: ${brand} | 平台: ${platform} | 关键词: ${keyword}`;
}

// 2. 数据转换与日期补全
const { start_date, end_date } = response.metadata;

const parseDate = (s) => new Date(s.slice(0, 4), parseInt(s.slice(4, 6)) - 1, s.slice(6, 8));
const formatDate = (d) => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return { raw: `${year}${month}${day}`, display: `${year}-${month}-${day}` };
};

const fullData = [];
let curr = parseDate(start_date);
const end = parseDate(end_date);

while (curr <= end) {
  const dates = formatDate(curr);
  const existing = response.data.find(item => item.date === dates.raw);
  
  fullData.push({
    date: dates.raw,
    dateStr: dates.display,
    mention_rate: existing ? existing.mention_rate : 0,
    brand: response.metadata.brand,
    platform: response.metadata.platform,
    keyword: response.metadata.keyword
  });
  
  curr.setDate(curr.getDate() + 1);
}

const data = fullData;

// 3. 创建图表
const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.theme({ type: 'academy' });

chart.data(data);

// 4. 绘制柱状图层
chart
  .interval()
  .encode('x', 'dateStr')
  .encode('y', 'mention_rate')
  .axis('y', {
    title: '提及率 (Mention Rate)',
    titleFill: '#5B8FF9',
    labelFormatter: (d) => `${(d * 100).toFixed(1)}%`
  })
  .tooltip({
    title: 'dateStr',
    items: [
      { field: 'mention_rate', name: '提及率', valueFormatter: d => `${(d * 100).toFixed(2)}%` }
    ]
  });

// 5. 绘制折线图层 (平滑趋势)
chart
  .line()
  .encode('x', 'dateStr')
  .encode('y', 'mention_rate')
  .encode('shape', 'smooth')
  .style('stroke', '#fdae6b')
  .style('lineWidth', 3)
  .tooltip(false);

// 6. 绘制数据点图层
chart
  .point()
  .encode('x', 'dateStr')
  .encode('y', 'mention_rate')
  .encode('shape', 'point')
  .style('fill', '#fdae6b')
  .style('r', 5)
  .tooltip(false);

// 7. 渲染
chart.render();
