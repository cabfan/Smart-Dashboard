<template>
  <div class="statistic-card">
    <div class="card-header">
      <el-icon :style="{ color }"><component :is="icon" /></el-icon>
      <span class="title">{{ title }}</span>
    </div>
    <div class="card-content">
      <span class="value">{{ value }}<span v-if="unit">{{ unit }}</span></span>
      <div class="trend" :class="trend">
        <el-icon><ArrowUp /></el-icon>
        <span>{{ trendValue }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  value: [String, Number],
  unit: String,
  icon: String,
  color: String,
  trend: String,
  trendValue: String
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

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2f3d;
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
