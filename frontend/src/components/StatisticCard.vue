<template>
  <div class="statistic-card">
    <div class="card-header">
      <div class="icon-wrapper" :style="{ backgroundColor: iconBg }">
        <el-icon :style="{ color: iconColor }">
          <component :is="icon" />
        </el-icon>
      </div>
      <span class="label">{{ label }}</span>
    </div>
    <div class="card-content">
      <div class="value">{{ value }}</div>
      <div class="trend" :class="{ 'up': trend > 0, 'down': trend < 0 }">
        <el-icon><component :is="trend > 0 ? 'ArrowUp' : trend < 0 ? 'ArrowDown' : 'Minus'" /></el-icon>
        <span>{{ Math.abs(trend) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'

defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  trend: {
    type: Number,
    default: 0
  },
  icon: {
    type: String,
    required: true
  },
  iconBg: {
    type: String,
    default: '#e6f4ff'
  },
  iconColor: {
    type: String,
    default: '#1890ff'
  }
})
</script>

<style scoped>
.statistic-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.label {
  color: #909399;
  font-size: 14px;
}

.card-content {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2f3d;
  line-height: 1;
}

.trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #f0f0f0;
  color: #909399;
}

.trend.up {
  background: #f6ffed;
  color: #52c41a;
}

.trend.down {
  background: #fff2e8;
  color: #fa8c16;
}

.el-icon {
  font-size: 16px;
}
</style>
