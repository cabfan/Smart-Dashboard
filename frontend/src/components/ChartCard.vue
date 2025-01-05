<template>
  <div class="chart-card">
    <div class="card-header">
      <h3>{{ title }}</h3>
      <el-select
        v-if="showTimeRange"
        v-model="timeRange"
        size="small"
        style="width: 120px"
      >
        <el-option label="最近7天" value="7" />
        <el-option label="最近30天" value="30" />
        <el-option label="最近90天" value="90" />
      </el-select>
    </div>
    <div class="chart-container">
      <v-chart class="chart" :option="option" :autoresize="true" />
    </div>
  </div>
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
  title: {
    type: String,
    required: true
  },
  option: {
    type: Object,
    required: true
  },
  showTimeRange: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.chart-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chart-container {
  flex: 1;
  max-height: 400px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
