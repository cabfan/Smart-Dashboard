<template>
  <el-container>
    <el-main>
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>AI 设置</span>
          </div>
        </template>

        <el-form :model="settings" label-width="120px">
          <el-form-item label="Base URL">
            <el-input
              v-model="settings.baseURL"
              placeholder="请输入API基础地址"
            />
          </el-form-item>

          <el-form-item label="API Key">
            <el-input
              v-model="settings.apiKey"
              type="password"
              show-password
              placeholder="请输入API密钥"
            />
          </el-form-item>

          <el-form-item label="模型名称">
            <el-select
              v-model="settings.model"
              placeholder="请选择模型"
              filterable
            >
              <el-option
                v-for="model in modelOptions"
                :key="model.value"
                :label="model.label"
                :value="model.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="isTesting"
              @click="testConnection"
            >
              测试连接
            </el-button>
            <el-button type="success" @click="saveSettings">
              保存设置
            </el-button>
          </el-form-item>
        </el-form>

        <el-alert
          v-if="testResult"
          :title="testResult"
          :type="testSuccess ? 'success' : 'error'"
          show-icon
          class="test-result"
        />
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 设置状态
const settings = ref({
  baseURL: 'https://api.deepseek.com',
  apiKey: '',
  model: 'deepseek-chat'
})

const isTesting = ref(false)
const testResult = ref('')
const testSuccess = ref(false)

// 模型选项
const modelOptions = [
  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
  { value: 'gpt-4o-mini-2024-07-18', label: 'GPT-4o-mini' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
]

// 加载保存的设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem('aiSettings')
  if (savedSettings) {
    settings.value = JSON.parse(savedSettings)
  }
}

// 保存设置
const saveSettings = () => {
  localStorage.setItem('aiSettings', JSON.stringify(settings.value))
  ElMessage.success('设置已保存')
}

// 测试连接
const testConnection = async () => {
  isTesting.value = true
  testResult.value = ''
  
  try {
    const response = await fetch(`${settings.value.baseURL}/v1/models`, {
      headers: {
        'Authorization': `Bearer ${settings.value.apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      testResult.value = '连接成功！'
      testSuccess.value = true
    } else {
      throw new Error('连接失败')
    }
  } catch (error) {
    testResult.value = `连接失败：${error.message}`
    testSuccess.value = false
  } finally {
    isTesting.value = false
  }
}

// 初始化加载设置
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-card {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
}

.test-result {
  margin-top: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}
</style>
