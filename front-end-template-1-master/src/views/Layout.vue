<template>
  <div class="layout-shell" :class="shellClasses">
    <StarryBackground
      :particles-number="backgroundParticles"
      :particle-opacity="backgroundOpacity"
      :line-opacity="backgroundLineOpacity"
      :move-speed="backgroundSpeed"
      :particle-size="backgroundSize"
      :click-effect="isSingleScreenMode"
    ></StarryBackground>

    <aside v-if="!isSingleScreenMode" class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="brand-row">
        <div class="brand-anchor" :class="{ centered: sidebarCollapsed }">
          <img :src="logoImg" class="brand-icon" alt="Medical Data logo" />
          <div v-if="!sidebarCollapsed" class="brand-copy">
            <div class="brand-title">Medical Data</div>
            <div class="brand-sub">{{ isAdminMode ? 'Admin Console' : 'Patient Workspace' }}</div>
          </div>
        </div>
        <button
          type="button"
          class="collapse-btn"
          :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
          @click="toggleSidebar"
        >
          <i :class="sidebarCollapsed ? 'el-icon-s-unfold' : 'el-icon-s-fold'"></i>
        </button>
      </div>

      <div class="sidebar-body">
        <button
          v-if="showBackToDashboard"
          type="button"
          class="back-btn-sidebar"
          @click="goDashboard"
        >
          <i class="el-icon-back"></i>
          <span v-if="!sidebarCollapsed">返回总览</span>
        </button>

        <p v-if="!sidebarCollapsed" class="nav-label">{{ navLabel }}</p>

        <nav class="sidebar-nav" :aria-label="navLabel">
          <router-link
            v-for="item in visibleNavItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: $route.path === item.path }"
            :title="item.label"
          >
            <span class="nav-icon"><i :class="item.icon"></i></span>
            <span v-if="!sidebarCollapsed" class="nav-text">{{ item.label }}</span>
          </router-link>
        </nav>
      </div>

      <div class="sidebar-footer">
        <div v-if="!sidebarCollapsed" class="user-chip">
          <div class="avatar">{{ username ? username.charAt(0).toUpperCase() : 'U' }}</div>
          <div class="user-text">
            <div class="name">{{ username || '未登录' }}</div>
            <div class="role">{{ isAdminMode ? '管理员' : '普通用户' }}</div>
          </div>
        </div>
        <button type="button" class="logout" @click="handleLogout">
          <span class="nav-icon"><i class="el-icon-switch-button"></i></span>
          <span v-if="!sidebarCollapsed" class="nav-text">退出登录</span>
        </button>
      </div>
    </aside>

    <main class="main-area">
      <header v-if="isSingleScreenMode && isAdminMode" class="topbar topbar-screen">
        <ScreenHeader>
          <template #actions>
            <span class="screen-user-chip">{{ username || 'admin' }}</span>
            <button type="button" class="screen-logout" @click="handleLogout">退出</button>
          </template>
        </ScreenHeader>
      </header>

      <header v-else class="topbar topbar-main">
        <div class="page-meta">
          <span class="page-kicker">{{ pageKicker }}</span>
          <div class="page-title-row">
            <h1 class="crumb">{{ pageTitle }}</h1>
            <span class="time">{{ currentTime }}</span>
          </div>
          <p class="page-desc">{{ pageDescription }}</p>
        </div>

        <div class="topbar-actions">
          <span v-if="isUserMode" class="role-badge-top">个人服务</span>
          <div class="topbar-brand">
            <img :src="logoImg" class="brand-icon-top" alt="Medical Data logo" />
            <div class="brand-meta-top">
              <div class="brand-title">Medical Data</div>
              <div class="brand-sub">Visualization</div>
            </div>
          </div>
        </div>
      </header>

      <section class="content-area">
        <router-view />
      </section>
    </main>
  </div>
</template>

<script>
import { getCurrentUser, logout } from '@/api/admin'
import logoImg from '@/assets/logo.png'
import ScreenHeader from '@/components/ScreenHeader.vue'
import StarryBackground from '@/components/StarryBackground.vue'
import { showFullscreenLoading } from '@/utils/fullscreenLoading'

const NAV_ITEMS = {
  admin: [
    { path: '/admin/users', label: '用户管理', icon: 'el-icon-s-operation' },
    { path: '/admin/cases', label: '病例管理', icon: 'el-icon-folder-opened' }
  ],
  user: [
    { path: '/user/predict', label: '病情预测', icon: 'el-icon-view' },
    { path: '/user/cases', label: '我的病例', icon: 'el-icon-folder-opened' }
  ]
}

export default {
  name: 'Layout',
  components: {
    ScreenHeader,
    StarryBackground
  },
  data() {
    return {
      logoImg,
      sidebarCollapsed: false,
      username: '',
      userRole: '',
      currentTime: '',
      timer: null
    }
  },
  computed: {
    isAdminMode() {
      return this.userRole === 'admin'
    },
    isUserMode() {
      return this.userRole === 'user'
    },
    isSingleScreenMode() {
      return this.$route.path === '/admin/dashboard'
    },
    adminBackendActive() {
      return this.isAdminMode && (this.$route.path === '/admin/users' || this.$route.path === '/admin/cases')
    },
    showBackToDashboard() {
      return this.adminBackendActive
    },
    visibleNavItems() {
      if (this.isAdminMode) return NAV_ITEMS.admin
      if (this.isUserMode) return NAV_ITEMS.user
      return []
    },
    navLabel() {
      if (this.isAdminMode) return '管理工作台'
      if (this.isUserMode) return '个人服务'
      return '导航'
    },
    pageTitle() {
      const titleMap = {
        '/admin/dashboard': '数据总览',
        '/admin/users': '用户管理',
        '/admin/cases': '病例管理',
        '/user/predict': '病情预测',
        '/user/cases': '我的病例'
      }
      return titleMap[this.$route.path] || '医疗数据分析系统'
    },
    pageKicker() {
      if (this.isAdminMode) return this.isSingleScreenMode ? '可视化总览' : '后台管理'
      return '用户服务'
    },
    pageDescription() {
      const descMap = {
        '/admin/dashboard': '集中展示医疗数据分布、趋势和关键指标。',
        '/admin/users': '维护系统用户角色、状态与基础信息。',
        '/admin/cases': '查看、检索并维护病例数据。',
        '/user/predict': '输入症状描述，快速获得初步预测参考。',
        '/user/cases': '查看个人就诊记录与历史信息。'
      }
      return descMap[this.$route.path] || '统一的医疗数据可视化与管理体验。'
    },
    backgroundParticles() {
      if (this.isSingleScreenMode) return 96
      return this.isUserMode ? 46 : 62
    },
    backgroundOpacity() {
      if (this.isSingleScreenMode) return 0.15
      return this.isUserMode ? 0.08 : 0.11
    },
    backgroundLineOpacity() {
      if (this.isSingleScreenMode) return 0.2
      return this.isUserMode ? 0.12 : 0.16
    },
    backgroundSpeed() {
      return this.isSingleScreenMode ? 1.8 : 1.1
    },
    backgroundSize() {
      return this.isSingleScreenMode ? 3 : 2
    },
    shellClasses() {
      return {
        'screen-mode': this.isSingleScreenMode,
        'admin-mode': this.isAdminMode,
        'user-mode': this.isUserMode
      }
    }
  },
  created() {
    this.getUserInfo()
    this.updateTime()
    this.timer = setInterval(this.updateTime, 60000)
  },
  beforeDestroy() {
    if (this.timer) clearInterval(this.timer)
  },
  methods: {
    async getUserInfo() {
      try {
        const res = await getCurrentUser()
        if (res.code === 200) {
          this.username = res.data.username
          this.userRole = res.data.role
        } else {
          this.$router.push('/login')
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.$router.push('/login')
      }
    },
    goDashboard() {
      this.$router.push('/admin/dashboard')
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    async handleLogout() {
      try {
        await this.$confirm('确定要退出登录吗？', '提示', {
          type: 'warning',
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        })
      } catch (error) {
        return
      }

      const loader = showFullscreenLoading('正在退出登录')

      try {
        await logout()
        await this.$router.push('/login')
      } catch (error) {
        console.error('退出登录异常:', error)
        await this.$router.push('/login')
      } finally {
        loader.close()
      }
    },
    updateTime() {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      this.currentTime = `${year}-${month}-${day} ${hours}:${minutes}`
    }
  }
}
</script>

<style scoped>
.layout-shell {
  position: relative;
  display: flex;
  min-height: 100vh;
  background: transparent;
  color: var(--text);
}

.layout-shell::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(6, 11, 22, 0.78), rgba(6, 11, 22, 0.94)),
    radial-gradient(820px 360px at 12% 0%, rgba(63, 140, 255, 0.1), transparent 55%),
    radial-gradient(720px 280px at 88% 0%, rgba(51, 197, 201, 0.08), transparent 52%);
}

.layout-shell.user-mode::before {
  background:
    linear-gradient(180deg, rgba(6, 11, 22, 0.64), rgba(6, 11, 22, 0.9)),
    radial-gradient(900px 400px at 0% 0%, rgba(63, 140, 255, 0.08), transparent 55%),
    radial-gradient(740px 300px at 100% 0%, rgba(51, 197, 201, 0.06), transparent 50%);
}

.sidebar,
.main-area {
  position: relative;
  z-index: 1;
}

.sidebar {
  width: 252px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(76, 108, 157, 0.36);
  background: rgba(12, 20, 38, 0.84);
  backdrop-filter: blur(14px);
  box-shadow: var(--shadow);
  transition: width 0.24s ease;
}

.layout-shell.user-mode .sidebar {
  background: rgba(12, 20, 38, 0.72);
}

.sidebar.collapsed {
  width: 92px;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(76, 108, 157, 0.28);
}

.brand-anchor {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.brand-anchor.centered {
  justify-content: center;
}

.brand-icon {
  width: 42px;
  height: 42px;
  object-fit: contain;
  border-radius: 12px;
  flex-shrink: 0;
}

.brand-copy {
  min-width: 0;
}

.brand-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.1;
}

.brand-sub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.collapse-btn {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(17, 26, 42, 0.9);
  color: var(--text);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.collapse-btn:hover {
  background: #1b2940;
  border-color: var(--accent);
}

.sidebar-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 0 16px;
  min-height: 0;
}

.back-btn-sidebar {
  margin: 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(17, 26, 42, 0.88);
  color: var(--text);
  cursor: pointer;
}

.back-btn-sidebar:hover {
  border-color: var(--accent);
  background: #1b2940;
}

.nav-label {
  padding: 0 18px;
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
  display: grid;
  grid-auto-rows: max-content;
  align-content: start;
  gap: 8px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 54px;
  padding: 10px 12px;
  border-radius: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
  border: 1px solid transparent;
}

.nav-item:hover {
  color: var(--text);
  background: rgba(17, 26, 42, 0.78);
  border-color: rgba(82, 162, 228, 0.16);
}

.nav-item.active {
  color: var(--text);
  background: linear-gradient(90deg, rgba(63, 140, 255, 0.2), rgba(63, 140, 255, 0.02));
  border-color: rgba(82, 162, 228, 0.22);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: -1px;
  top: 9px;
  bottom: 9px;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--accent), var(--accent-2));
}

.nav-icon {
  width: 38px;
  height: 30px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 9px;
  border: 1px solid rgba(82, 162, 228, 0.14);
  background: rgba(17, 26, 42, 0.88);
  color: var(--text);
}

.nav-text {
  font-size: 14px;
  line-height: 1.2;
}

.sidebar-footer {
  display: grid;
  gap: 8px;
  padding: 14px 16px 16px;
  border-top: 1px solid rgba(76, 108, 157, 0.28);
}

.user-chip {
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(17, 26, 42, 0.8);
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
}

.user-text .name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.user-text .role {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.logout {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 52px;
  padding: 10px 14px;
  border-radius: 14px;
  border: 1px solid rgba(82, 162, 228, 0.22);
  background: rgba(17, 26, 42, 0.8);
  color: var(--text);
  cursor: pointer;
}

.logout:hover {
  border-color: rgba(82, 162, 228, 0.42);
  background: #1b2940;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
}

.topbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 26px;
  border-bottom: 1px solid rgba(76, 108, 157, 0.26);
  backdrop-filter: blur(14px);
  background: rgba(20, 32, 58, 0.7);
}

.topbar-screen {
  padding: 0 12px 10px;
  background: linear-gradient(180deg, rgba(8, 14, 28, 0.82), rgba(8, 14, 28, 0.65));
}

.page-meta {
  min-width: 0;
}

.page-kicker {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(82, 162, 228, 0.24);
  background: rgba(17, 26, 42, 0.7);
  color: #9dc6ff;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.page-title-row {
  display: flex;
  align-items: baseline;
  gap: 14px;
  flex-wrap: wrap;
}

.crumb {
  margin: 0;
  font-size: 32px;
  line-height: 1;
  font-weight: 700;
  color: var(--text);
}

.time {
  color: var(--text-muted);
  font-size: 13px;
}

.page-desc {
  margin: 12px 0 0;
  max-width: 680px;
  color: #a7bdd9;
  font-size: 14px;
  line-height: 1.6;
}

.topbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.role-badge-top {
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(51, 197, 201, 0.12);
  border: 1px solid rgba(51, 197, 201, 0.2);
  color: #9be7ea;
  font-size: 13px;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon-top {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  object-fit: contain;
}

.brand-meta-top .brand-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.brand-meta-top .brand-sub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-muted);
}

.screen-user-chip {
  font-size: 14px;
  color: #9db8da;
}

.screen-logout {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid rgba(82, 162, 228, 0.36);
  background: rgba(17, 26, 42, 0.78);
  color: var(--text);
  cursor: pointer;
}

.screen-logout:hover {
  background: #1b2940;
}

.content-area {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 22px;
}

.layout-shell.user-mode .content-area {
  padding: clamp(24px, 3vw, 36px);
}

.layout-shell.screen-mode .content-area {
  padding: 16px 22px 24px;
}

.sidebar-nav::-webkit-scrollbar,
.content-area::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-thumb,
.content-area::-webkit-scrollbar-thumb {
  background: rgba(76, 108, 157, 0.65);
  border-radius: 999px;
}

@media (max-width: 1024px) {
  .sidebar {
    width: 220px;
  }

  .crumb {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .layout-shell {
    flex-direction: column;
  }

  .sidebar,
  .sidebar.collapsed {
    width: 100%;
  }

  .sidebar-body {
    padding-top: 12px;
  }

  .topbar {
    padding: 16px;
  }

  .page-title-row {
    gap: 8px;
  }

  .crumb {
    font-size: 24px;
  }

  .content-area {
    padding: 16px;
  }
}
</style>
