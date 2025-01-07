<template>
  <el-card class="statistic-card">
    <div class="card-content">
      <span class="card-value" :style="{ color: valueColor }">
        {{ formattedValue }}
      </span>
    </div>
    <div v-if="description" class="card-footer">
      {{ description }}
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '统计指标'
  },
  value: {
    type: [Number, String],
    required: true
  },
  icon: {
    type: String,
    default: 'el-icon-data-line'
  },
  color: {
    type: String,
    default: '#409EFF'
  },
  description: {
    type: String,
    default: ''
  },
  format: {
    type: String,
    default: 'number' // 可选：number, percent, currency
  }
})

// 计算属性
const formattedValue = computed(() => {
  
  switch (props.format) {
    case 'percent':
      return `${props.value}%`
    case 'currency':
      return `¥${props.value.toLocaleString()}`
    default:
      return props.value.toLocaleString()
  }
})

const valueColor = computed(() => props.color)

</script>

<style scoped>
.statistic-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-content {
  text-align: center;
  width: 600px;
  height: 300px;
}

.card-footer {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>
