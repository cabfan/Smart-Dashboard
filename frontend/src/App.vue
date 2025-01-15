<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="260px" class="sidebar">
      <div class="logo">
        <el-icon class="logo-icon" :size="32"><Monitor /></el-icon>
        <span class="logo-text">Smart Dashboard</span>
      </div>
      <el-menu
        :default-active="$route.path"
        class="sidebar-menu"
        background-color="var(--menu-bg)"
        text-color="#fff"
        active-text-color="var(--primary-color)"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>ChatDB</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 头部 -->
      <el-header class="header">
        <div class="breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ $route.name }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-actions">
          <div class="notification-icon">
            <el-icon :size="20" color="#666"><Bell /></el-icon>
            <span class="notification-badge">3</span>
          </div>
          <el-dropdown>
            <el-avatar class="avatar" :size="32" src="/assets/user-avatar.svg" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人信息</el-dropdown-item>
                <el-dropdown-item>设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 路由视图 -->
      <el-main>
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { Bell, Monitor, Setting, ChatDotRound } from '@element-plus/icons-vue'
import { RouterView } from 'vue-router'

</script>

<style scoped>
/* 添加全局样式 */
:global(body) {
  margin: 0;
  padding: 0;
  overflow: hidden;  /* 隐藏body的滚动条 */
  height: 100vh;
}

.app-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;  /* 隐藏容器滚动条 */
}

.sidebar {
  background-color: #001529;
  color: #fff;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: #002140;
}

.logo-icon {
  color: #1890ff;
  margin-right: 8px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.main-container {
  margin-left: 260px;
  height: 100vh;
  overflow: hidden;  /* 隐藏主容器滚动条 */
  background: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notification-icon {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.notification-icon:hover {
  background-color: #f5f7fa;
}

.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background-color: #f56c6c;
  color: white;
  font-size: 12px;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 8px;
  padding: 0 4px;
}

.avatar {
  cursor: pointer;
  transition: transform 0.2s;
}

.avatar:hover {
  transform: scale(1.1);
}

:deep(.el-button.is-loading) {
  width: 80px;
  height: 36px;
  padding: 8px 12px;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff !important;
}

:deep(.el-menu-item:hover) {
  background-color: #1890ff !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #1890ff !important;
  color: #fff !important;
}

:deep(.el-textarea__inner) {
  padding-right: 100px;
  resize: none;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  min-height: 100px;
}
</style>