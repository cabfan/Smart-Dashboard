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
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2f3d;
}

.chart-container {
  flex: 1;
  position: relative;
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}

:deep(.el-select) {
  margin-left: 16px;
}

:deep(.el-input__wrapper) {
  box-shadow: none !important;
  border: 1px solid #dcdfe6;
}

:deep(.el-input__wrapper:focus-within) {
  border-color: #409EFF;
}
</style>
