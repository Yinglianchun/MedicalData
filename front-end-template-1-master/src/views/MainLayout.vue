<template>
    <div class="layout">
      <aside class="layout-sidebar">
        <div class="logo">医疗数据平台</div>
        <nav class="menu">
          <div
            v-for="item in menuItems"
            :key="item.path"
            :class="['menu-item', activePath === item.path ? 'active' : '']"
            @click="go(item.path)"
          >
            {{ item.label }}
          </div>
        </nav>
      </aside>
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </template>
  
  <script>
  export default {
    name: 'MainLayout',
    data () {
      return {
        activePath: this.$route.path,
        menuItems: [
          { path: '/dashboard', label: '数据概览' },      // 原来的大屏（首页图表）
          { path: '/user/pred', label: '在线预测' },
          { path: '/user/table', label: '病例数据表' },
          { path: '/admin/manage', label: '后台管理' }
        ]
      }
    },
    watch: {
      '$route.path' (val) {
        this.activePath = val
      }
    },
    methods: {
      go (path) {
        this.$router.push(path)
      }
    }
  }
  </script>
  
  <style scoped>
  .layout {
    display: flex;
    height: calc(100vh - 80px); /* 扣掉 Header 高度 */
  }
  .layout-sidebar {
    width: 200px;
    background: #f0effa;
    border-radius: 18px;
    margin-right: 16px;
    padding: 16px 12px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
  }
  .logo {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 20px;
    color: #26243a;
  }
  .menu {
    flex: 1;
  }
  .menu-item {
    padding: 8px 12px;
    border-radius: 12px;
    cursor: pointer;
    margin-bottom: 6px;
    font-size: 14px;
    color: #55556a;
  }
  .menu-item:hover {
    background: #e1dfff;
  }
  .menu-item.active {
    background: #7b6cff;
    color: #fff;
  }
  .layout-content {
    flex: 1;
    background: #ffffff;
    border-radius: 18px;
    padding: 20px 24px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
    overflow: auto;
  }
  </style>
  