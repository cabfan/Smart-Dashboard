<template>
  <div class="training-container">
    <!-- 移除 el-card，保留内容 -->
    <div class="header">
      <span>训练数据管理</span>
      <el-button type="primary" @click="showAddDialog">
        添加训练数据
      </el-button>
    </div>

    <el-table 
      :data="trainingData" 
      style="width: 100%"
      v-loading="loading">
      <el-table-column label="训练类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTypeTag(row.type)">
            {{ getTypeLabel(row.type) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <!-- 添加标题列 -->
      <el-table-column prop="title" label="标题" min-width="150">
        <template #default="{ row }">
          <span v-if="row.title">{{ row.title }}</span>
          <el-tag v-else size="small" type="info">无</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="question" label="问题描述" min-width="200">
        <template #default="{ row }">
          <span v-if="row.question">{{ row.question }}</span>
          <el-tag v-else size="small" type="info">无</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="content" label="训练内容" min-width="400">
        <template #default="{ row }">
          <div class="code-content">
            <pre><code>{{ row.content }}</code></pre>
          </div>
        </template>
      </el-table-column>
      
      <!-- 添加备注列 -->
      <el-table-column prop="note" label="备注" min-width="150">
        <template #default="{ row }">
          <span v-if="row.note">{{ row.note }}</span>
          <el-tag v-else size="small" type="info">无</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button 
            type="danger" 
            link
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加数据对话框保持不变 -->
    <el-dialog
      v-model="dialogVisible"
      title="添加训练数据"
      width="60%"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="数据类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择数据类型" style="width: 100%">
            <el-option label="SQL查询" value="sql" />
            <el-option label="DDL语句" value="ddl" />
            <el-option label="文档说明" value="documentation" />
          </el-select>
        </el-form-item>
        
        <!-- 添加标题字段 -->
        <el-form-item label="标题" prop="title">
          <el-input 
            v-model="form.title" 
            placeholder="请输入标题（可选）"
          />
        </el-form-item>
        
        <el-form-item 
          v-if="form.type === 'sql'" 
          label="问题描述" 
          prop="question"
        >
          <el-input 
            v-model="form.question" 
            placeholder="请输入对应的问题描述"
          />
        </el-form-item>
        
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="10"
            placeholder="请输入训练内容"
          />
        </el-form-item>
        
        <!-- 添加备注字段 -->
        <el-form-item label="备注" prop="note">
          <el-input
            v-model="form.note"
            type="textarea"
            :rows="3"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAdd" :loading="submitting">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 状态变量
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const trainingData = ref([])
const formRef = ref()

// 添加类型标签和标签文本函数
const getTypeTag = (type) => {
  switch (type) {
    case 'sql':
      return 'success'
    case 'ddl':
      return 'warning'
    case 'documentation':
      return 'info'
    default:
      return 'default'
  }
}

const getTypeLabel = (type) => {
  switch (type) {
    case 'sql':
      return 'SQL查询'
    case 'ddl':
      return 'DDL语句'
    case 'documentation':
      return '文档说明'
    default:
      return '未知类型'
  }
}

// 表单数据
const form = ref({
  type: '',
  title: '',  // 添加标题字段
  question: '',
  content: '',
  note: ''    // 添加备注字段
})

// 表单验证规则
const rules = {
  type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
  question: [{ required: true, message: '请输入问题描述', trigger: 'blur' }],
  content: [{ required: true, message: '请输入训练内容', trigger: 'blur' }],
  // 标题和备注是可选的，不需要验证规则
}

// 显示添加对话框
const showAddDialog = () => {
  form.value = {
    type: '',
    title: '',  // 重置标题
    question: '',
    content: '',
    note: ''    // 重置备注
  }
  dialogVisible.value = true
}

// 获取训练数据列表
const fetchTrainingData = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/training/list')
    const data = await response.json()
    if (data.success) {
      trainingData.value = data.data
    } else {
      ElMessage.error(data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取训练数据失败:', error)
    ElMessage.error('获取训练数据失败')
  } finally {
    loading.value = false
  }
}

// 添加训练数据
const handleAdd = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const params = new URLSearchParams()
        params.append('data_type', form.value.type)
        params.append('content', form.value.content)
        params.append('title', form.value.title || '')  // 添加标题
        params.append('note', form.value.note || '')    // 添加备注
        if (form.value.type === 'sql') {
          params.append('question', form.value.question)
        }
        
        const response = await fetch('/api/training/add', {
          method: 'POST',
          body: params
        })
        const data = await response.json()
        
        if (data.success) {
          ElMessage.success('添加成功')
          dialogVisible.value = false
          fetchTrainingData()
        } else {
          ElMessage.error(data.message || '添加失败')
        }
      } catch (error) {
        console.error('添加训练数据失败:', error)
        ElMessage.error('添加失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 删除训练数据
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条训练数据吗？', '提示', {
      type: 'warning'
    })
    
    const response = await fetch(`/api/training/${row.id}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('删除成功')
      fetchTrainingData()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除训练数据失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 页面加载时获取数据
onMounted(() => {
  fetchTrainingData()
})
</script>

<style scoped>
.training-container {
  padding: 20px;
  height: 100%;
}

/* 移除 .training-card 样式，添加 header 样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: bold;
}

.column-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-tags {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.type-tags .el-tag {
  margin: 0;
}

.code-content {
  max-height: 100px;
  overflow-y: auto;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.code-content pre {
  margin: 0;
  padding: 12px;
}

.code-content code {
  font-family: Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
}

:deep(.el-table__header) {
  background-color: var(--el-fill-color-light);
}

:deep(.el-table__fixed-right) {
  height: 100% !important;
}

:deep(.el-tag--large) {
  padding: 0 12px;
  height: 32px;
  line-height: 30px;
}
:deep(.el-dialog__body) {
  padding-top: 20px;
}
</style>