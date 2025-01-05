<template>
  <div class="timeline-card">
    <div class="card-header">
      <h3>{{ title }}</h3>
    </div>
    <el-timeline>
      <el-timeline-item
        v-for="(activity, index) in activities"
        :key="index"
        :type="activity.type"
        :color="activity.color"
        :timestamp="activity.timestamp"
        :hollow="true"
      >
        {{ activity.content }}
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  activities: {
    type: Array,
    required: true
  }
})
</script>

<style scoped>
.timeline-card {
  text-align: left;
}

.card-header {
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2f3d;
}

:deep(.el-timeline) {
  padding-left: 16px;
}

:deep(.el-timeline-item__content) {
  color: #1f2f3d;
  font-size: 14px;
}

:deep(.el-timeline-item__timestamp) {
  font-size: 12px;
  color: #909399;
}

:deep(.el-timeline-item__node) {
  background-color: #fff;
  border-color: currentColor;
}

:deep(.el-timeline-item__tail) {
  border-left-color: #e4e7ed;
}
</style>
