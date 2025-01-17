<template>
  <div class="chart-container">
    <div ref="chartRef" :style="{ width: '100%', height: '400px' }" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const chartRef = ref(null)
let chart = null

// 列名映射表
const columnNameMap = {
  // NBA 数据表
  'PLAYER_NAME': '球员',
  'TEAM_NAME': '球队',
  'GAME_DATE': '比赛日期',
  'EVENT_TYPE': '投篮结果',
  'SHOT_MADE': '是否命中',
  'ACTION_TYPE': '投篮类型',
  'SHOT_TYPE': '投篮距离',
  'BASIC_ZONE': '投篮区域',
  'ZONE_NAME': '场上位置',
  'SHOT_DISTANCE': '投篮距离',
  'QUARTER': '比赛节数',
  'MINS_LEFT': '剩余分钟',
  'SECS_LEFT': '剩余秒数',
  // 统计字段
  'attempts': '出手次数',
  'made': '命中次数',
  'fg_percentage': '命中率',
  'count': '数量',
  'shots': '投篮数'
}

// 格式化列名
const formatColumnName = (col) => {
  return columnNameMap[col] || col
}

// 根据数据类型生成图表配置
const generateChartOption = (data) => {
  const { results, columns, type, message } = data
  
  // 生成图表标题
  const generateTitle = (categoryColumn, numericColumns) => {
    const category = formatColumnName(categoryColumn)
    const metrics = numericColumns.map(col => formatColumnName(col)).join('、')
    return `${category}的${metrics}统计`
  }
  
  // 如果是单值，使用仪表盘
  if (type === 'single') {
    return {
      title: {
        text: message,
        left: 'center'
      },
      series: [{
        type: 'gauge',
        data: [{ value: results }],
        detail: { formatter: '{value}' }
      }]
    }
  }
  
  // 判断是否需要双Y轴
  const needDualYAxis = (columns, results) => {
    const valueRanges = {}
    columns.forEach(col => {
      if (typeof results[0][col] === 'number') {
        const values = results.map(row => row[col])
        valueRanges[col] = {
          min: Math.min(...values),
          max: Math.max(...values)
        }
      }
    })
    
    // 检查是否有百分比类型的列
    const percentageColumns = columns.filter(col => 
      col.toLowerCase().includes('percentage') ||
      col.toLowerCase().includes('rate') ||
      (valueRanges[col] && valueRanges[col].max <= 100 && valueRanges[col].min >= 0)
    )
    
    // 检查是否有大数值列
    const largeValueColumns = columns.filter(col =>
      valueRanges[col] && valueRanges[col].max > 100
    )
    
    return percentageColumns.length > 0 && largeValueColumns.length > 0
  }
  
  // 如果是表格数据，尝试生成合适的图表
  if (type === 'table') {
    // 检查是否包含数值列
    const numericColumns = columns.filter(col => 
      typeof results[0][col] === 'number'
    )
    
    // 如果有分类和数值，生成柱状图/折线图
    if (numericColumns.length > 0) {
      const categoryColumn = columns.find(col => !numericColumns.includes(col))
      const useDualYAxis = needDualYAxis(columns, results)
      
      // 分离百分比和非百分比列
      const percentageColumns = numericColumns.filter(col => 
        col.toLowerCase().includes('percentage') ||
        col.toLowerCase().includes('rate')
      )
      const normalColumns = numericColumns.filter(col => !percentageColumns.includes(col))
      
      return {
        title: {
          text: generateTitle(categoryColumn, numericColumns),
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            const categoryValue = params[0].name
            return params.map(param => {
              const columnName = formatColumnName(param.seriesName)
              const value = param.seriesName.toLowerCase().includes('percentage') ? 
                `${param.value}%` : param.value
              return `${categoryValue} - ${columnName}: ${value}`
            }).join('<br/>')
          }
        },
        legend: {
          data: numericColumns.map(col => formatColumnName(col)),
          bottom: 0
        },
        xAxis: {
          type: 'category',
          data: results.map(row => row[categoryColumn]),
          axisLabel: {
            rotate: 45
          },
          name: formatColumnName(categoryColumn),
          nameLocation: 'middle',
          nameGap: 40
        },
        yAxis: useDualYAxis ? [
          {
            type: 'value',
            name: '数量',
            nameLocation: 'middle',
            nameGap: 50,
            axisLabel: {
              formatter: '{value}'
            }
          },
          {
            type: 'value',
            name: '百分比',
            nameLocation: 'middle',
            nameGap: 50,
            axisLabel: {
              formatter: '{value}%'
            },
            max: 100,
            splitLine: {
              show: false
            }
          }
        ] : {
          type: 'value',
          name: numericColumns.length === 1 ? formatColumnName(numericColumns[0]) : '数值',
          nameLocation: 'middle',
          nameGap: 50
        },
        series: [
          ...normalColumns.map(col => ({
            name: formatColumnName(col),
            type: 'bar',
            data: results.map(row => row[col]),
            yAxisIndex: 0
          })),
          ...percentageColumns.map(col => ({
            name: formatColumnName(col),
            type: 'line',
            data: results.map(row => row[col]),
            yAxisIndex: useDualYAxis ? 1 : 0,
            label: {
              show: true,
              formatter: '{c}%',
              position: 'top'
            },
            lineStyle: {
              width: 3
            },
            symbol: 'circle',
            symbolSize: 8
          }))
        ]
      }
    }
  }
  
  return null
}

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    const option = generateChartOption(props.data)
    if (option) {
      chart.setOption(option)
    }
  }
}

// 监听数据变化
watch(() => props.data, () => {
  const option = generateChartOption(props.data)
  if (option && chart) {
    chart.setOption(option)
  }
}, { deep: true })

onMounted(() => {
  initChart()
})

// 响应窗口大小变化
window.addEventListener('resize', () => {
  chart?.resize()
})
</script>

<style scoped>
.chart-container {
  margin: 16px 0;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style> 