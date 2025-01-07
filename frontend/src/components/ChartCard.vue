<template>
  <el-card class="chart-card">
    <div class="card-content">
      <v-chart class="chart" :option="option" :autoresize="true" />
    </div>
    <div class="card-footer">
      {{ description }}
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'

// 注册必要的组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

const timeRange = ref('7')

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.chart-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-content {
  width: 600px;
  height: 300px;
}

.card-footer {
  padding: 12px;
  font-size: 12px;
  color: #909399;
  text-align: left;
  max-width: 600px;
}
</style>
