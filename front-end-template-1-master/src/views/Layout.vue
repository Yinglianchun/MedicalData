<template>
  <div class="layout-shell" :class="{ 'screen-mode': isSingleScreenMode }">
    <aside v-if="!isSingleScreenMode" class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="brand-row brand-row-minimal">
        <button
          v-if="showBackToDashboard"
          type="button"
          class="back-btn-sidebar"
          :title="sidebarCollapsed ? '返回总览' : ''"
          @click="goDashboard"
        >
          <i class="el-icon-back"></i>
          <span v-if="!sidebarCollapsed">返回</span>
        </button>
        <span v-else class="brand-spacer" />
        <button class="collapse-btn" @click="toggleSidebar" :title="sidebarCollapsed ? '展开' : '收起'">
          <i v-if="!sidebarCollapsed" class="el-icon-s-fold"></i>
          <i v-else class="el-icon-s-unfold"></i>
        </button>
      </div>

      <nav class="sidebar-nav">
        <p v-if="!sidebarCollapsed" class="nav-label">控制台</p>
        <template v-if="userRole === 'admin'">
          <router-link
            to="/admin/users"
            class="nav-item"
            title="用户管理"
            :class="{ 'router-link-active': $route.path === '/admin/users' }"
          >
            <span class="nav-icon"><i class="el-icon-s-operation"></i></span>
            <span v-if="!sidebarCollapsed" class="nav-text">用户管理</span>
          </router-link>

          <router-link
            to="/admin/cases"
            class="nav-item"
            title="病例管理"
            :class="{ 'router-link-active': $route.path === '/admin/cases' }"
          >
            <span class="nav-icon"><i class="el-icon-folder-opened"></i></span>
            <span v-if="!sidebarCollapsed" class="nav-text">病例管理</span>
          </router-link>
        </template>
        <template v-else>
          <router-link to="/user/predict" class="nav-item" title="病情预测">
            <span class="nav-icon"><i class="el-icon-view"></i></span>
            <span v-if="!sidebarCollapsed" class="nav-text">病情预测</span>
          </router-link>
          <router-link to="/user/cases" class="nav-item" title="我的病例">
            <span class="nav-icon"><i class="el-icon-folder-opened"></i></span>
            <span v-if="!sidebarCollapsed" class="nav-text">我的病例</span>
          </router-link>
        </template>
      </nav>

      <div class="sidebar-footer">
        <div class="user-chip" v-if="!sidebarCollapsed">
          <div class="avatar">{{ username ? username.charAt(0).toUpperCase() : 'U' }}</div>
          <div class="user-text">
            <div class="name">{{ username || '未登录' }}</div>
            <div class="role">{{ userRole === 'admin' ? '管理员' : '普通用户' }}</div>
          </div>
        </div>
        <button class="logout" @click="handleLogout" :title="sidebarCollapsed ? '退出登录' : ''">
          <span class="nav-icon"><i class="el-icon-switch-button"></i></span>
          <span v-if="!sidebarCollapsed" class="nav-text">退出登录</span>
        </button>
      </div>
    </aside>

    <main class="main-area">
      <header v-if="isSingleScreenMode && userRole === 'admin'" class="topbar topbar-screen-tmpl">
        <ScreenHeader>
          <template #actions>
            <span class="screen-user-chip">{{ username || 'Admin' }}</span>
            <button type="button" class="screen-logout" @click="handleLogout">退出</button>
          </template>
        </ScreenHeader>
      </header>
      <header v-else class="topbar topbar-main" :class="{ compact: isSingleScreenMode }">
        <div class="topbar-left">
          <div class="page-meta">
            <div class="crumb">{{ pageTitle }}</div>
            <span class="time">{{ currentTime }}</span>
          </div>
          <div v-if="adminBackendActive" class="backend-tabs">
            <router-link
              to="/admin/users"
              class="backend-tab"
              active-class="active"
              exact
            >
              用户管理
            </router-link>
            <router-link to="/admin/cases" class="backend-tab" active-class="active">
              病例管理
            </router-link>
          </div>
        </div>
        <div class="topbar-brand">
          <img :src="logoImg" class="brand-icon-top" alt="" />
          <div class="brand-meta-top">
            <div class="brand-title">Medical Data</div>
            <div class="brand-sub">Visualization</div>
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

export default {
  name: 'Layout',
  components: { ScreenHeader },
  data() {
    return {
      logoImg,
      sidebarCollapsed: false,
      username: '',
      userRole: '',
      currentTime: ''
    }
  },
  computed: {
    adminBackendActive() {
      return this.userRole === 'admin' && (this.$route.path === '/admin/users' || this.$route.path === '/admin/cases')
    },
    showBackToDashboard() {
      return this.adminBackendActive
    },
    isSingleScreenMode() {
      return this.$route.path === '/admin/dashboard'
    },
    pageTitle() {
      const route = this.$route.path
      const titleMap = {
        '/admin/dashboard': '数据总览',
        '/admin/users': '用户管理',
        '/admin/cases': '病例管理',
        '/user/predict': '病情预测',
        '/user/cases': '我的病例'
      }
      return titleMap[route] || '医疗数据看板'
    }
  },
  created() {
    this.getUserInfo()
    this.updateTime()
    this.timer = setInterval(this.updateTime, 60000)
  },
  beforeDestroy() {
    if (this.timer) {
      clearInterval(this.timer)
    }
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
      } catch (e) {
        console.error('获取用户信息失败', e)
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
        const loader = this.$loading({
          lock: true,
          text: '正在退出...',
          background: 'rgba(15, 23, 42, 0.22)'
        })
        await logout()
        loader.close()
        this.$message.success('已退出登录')
        this.$router.push('/login')
      } catch (e) {
        if (String(e).includes('cancel')) return
        console.error('退出登录异常', e)
        this.$router.push('/login')
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
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.layout-shell.screen-mode .content-area {
  padding: var(--sp-2) var(--sp-3) var(--sp-3);
  overflow-x: auto;
  overflow-y: auto;
  min-height: 0;
}

.sidebar {
  width: 244px;
  background: var(--panel);
  color: var(--text);
  display: flex;
  flex-direction: column;
  transition: width 0.24s ease;
  border-right: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.sidebar.collapsed { width: 84px; }

.sidebar.collapsed .sidebar-footer {
  padding: var(--sp-1);
}

.sidebar.collapsed .logout {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 0;
  justify-content: center;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2);
  border-bottom: 1px solid var(--border);
}
.brand-row-minimal {
  justify-content: space-between;
  align-items: center;
}
.brand-spacer {
  flex: 1;
  min-width: 4px;
}
.back-btn-sidebar {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.back-btn-sidebar:hover {
  background: #1b2940;
  border-color: var(--accent);
}
.backend-tabs {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: var(--sp-2);
  flex-wrap: wrap;
}
.backend-tab {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: var(--fs-12);
  color: var(--text-muted);
  text-decoration: none;
  border: 1px solid var(--border);
  background: var(--bg-2);
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.backend-tab:hover {
  color: var(--text);
  border-color: var(--accent);
}
.backend-tab.active {
  color: #fff;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  border-color: transparent;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  object-fit: contain;
  flex-shrink: 0;
}

.brand-meta { flex: 1; }
.brand-title { font-size: var(--fs-16); font-weight: var(--fw-bold); }
.brand-sub { font-size: var(--fs-12); color: var(--text-muted); }

.collapse-btn {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
  display: grid;
  place-items: center;
}
.collapse-btn i {
  font-size: 16px;
}
.collapse-btn:hover { background: #1b2940; }

.nav-label {
  padding: 0 var(--sp-2);
  margin: var(--sp-2) 0 var(--sp-1);
  font-size: var(--fs-12);
  color: var(--text-muted);
  letter-spacing: 0.2px;
}

.sidebar-nav {
  flex: 1;
  padding: 0 0 var(--sp-2);
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 12px var(--sp-2);
  color: var(--text-muted);
  text-decoration: none;
  transition: all 0.2s;
  position: relative;
}
.nav-item:hover { background: var(--bg-2); color: var(--text); }
.nav-item.router-link-active {
  background: linear-gradient(90deg, rgba(63, 140, 255, 0.22), transparent);
  color: var(--text);
}
.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 3px;
  background: var(--accent);
  border-radius: 2px;
}
.nav-icon {
  min-width: 42px;
  height: 28px;
  border-radius: 10px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  display: grid;
  place-items: center;
  color: var(--text);
}
.nav-icon i {
  font-size: 16px;
  color: inherit;
}
.nav-text { font-size: var(--fs-14); }

.sidebar-footer {
  padding: var(--sp-2);
  border-top: 1px solid var(--border);
  display: grid;
  gap: var(--sp-1);
}
.user-chip {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: var(--sp-1);
  align-items: center;
  background: var(--bg-2);
  border-radius: var(--radius);
  padding: var(--sp-1);
}
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  display: grid;
  place-items: center;
  font-weight: var(--fw-bold);
  color: #fff;
}
.user-text .name { font-size: var(--fs-14); font-weight: var(--fw-bold); }
.user-text .role { font-size: var(--fs-12); color: var(--text-muted); margin-top: 4px; }

.logout {
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  padding: 12px var(--sp-2);
  border-radius: var(--radius);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  transition: all 0.2s;
}
.logout:hover { background: #1b2940; }

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--border);
  background: var(--panel-2);
  backdrop-filter: blur(6px);
}
.topbar.compact {
  padding: 12px var(--sp-3);
}
.topbar-main {
  justify-content: space-between;
  align-items: center;
  gap: var(--sp-2);
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}
.topbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.brand-icon-top {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  object-fit: contain;
}
.brand-meta-top .brand-title {
  font-size: var(--fs-16);
  font-weight: var(--fw-bold);
  color: var(--text);
  line-height: 1.2;
}
.brand-meta-top .brand-sub {
  font-size: var(--fs-12);
  color: var(--text-muted);
  margin-top: 2px;
}
.topbar-screen-tmpl {
  flex-wrap: wrap;
  align-items: stretch;
  padding: 0 var(--sp-2) 8px;
  border-bottom: 1px solid rgba(82, 162, 228, 0.25);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(15, 23, 42, 0.88));
}
.topbar-screen-tmpl .screen-user-chip {
  font-size: 14px;
  color: #94a3b8;
}
.topbar-screen-tmpl .screen-logout {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(82, 162, 228, 0.45);
  background: rgba(27, 45, 74, 0.9);
  color: #e2e8f0;
  font-size: 13px;
  cursor: pointer;
}
.topbar-screen-tmpl .screen-logout:hover {
  background: #1b2d4a;
}
.page-meta { display: flex; align-items: center; gap: var(--sp-2); }
.crumb {
  font-size: var(--fs-20);
  font-weight: var(--fw-bold);
  color: var(--text);
}
.time { color: var(--text-muted); font-size: var(--fs-12); }
.top-actions { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; justify-content: flex-end; }
.screen-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  justify-content: center;
  flex-wrap: wrap;
}
.screen-nav-link {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: var(--fs-12);
  color: var(--text-muted);
  text-decoration: none;
  border: 1px solid var(--border);
  background: var(--bg-2);
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.screen-nav-link:hover {
  color: var(--text);
  border-color: var(--accent);
}
.screen-nav-link.active {
  color: #fff;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  border-color: transparent;
}
.screen-user-chip {
  font-size: var(--fs-12);
  color: var(--text-muted);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.screen-logout {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  font-size: var(--fs-12);
  cursor: pointer;
}
.screen-logout:hover {
  background: #1b2940;
}
.pill {
  padding: 8px var(--sp-2);
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
  border-radius: 20px;
  font-size: var(--fs-14);
  font-weight: var(--fw-medium);
}

.content-area {
  flex: 1;
  padding: var(--sp-2);
  overflow-y: auto;
}

.sidebar-nav::-webkit-scrollbar,
.content-area::-webkit-scrollbar { width: 6px; }
.sidebar-nav::-webkit-scrollbar-thumb,
.content-area::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}
.sidebar-nav::-webkit-scrollbar-thumb:hover,
.content-area::-webkit-scrollbar-thumb:hover {
  background: #4b628a;
}
</style>
