<template>
  <div class="screen-header-tmpl">
    <div class="header-left">
      <h1>医疗数据可视化分析系统</h1>
    </div>
    <nav class="header-nav" aria-label="大屏导航">
      <div :class="['header-nav-item', 'cool-border', dashActive ? 'active' : '']">
        <span class="nav content nav-click" @click="goOverview">总览</span>
        <div :class="[dashActive ? 'top-left' : '', 'corner']" />
        <div :class="[dashActive ? 'top-right' : '', 'corner']" />
        <div :class="[dashActive ? 'bottom-left' : '', 'corner']" />
        <div :class="[dashActive ? 'bottom-right' : '', 'corner']" />
      </div>

      <div class="header-nav-item cool-border">
        <span class="nav content nav-click" @click="goBackend">后台管理</span>
        <div class="corner" />
        <div class="corner" />
        <div class="corner" />
        <div class="corner" />
      </div>
    </nav>
    <div class="header-right">
      <span class="header-time">{{ displayTime }}</span>
      <div class="header-actions">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script>
import { showFullscreenLoading } from '@/utils/fullscreenLoading'

export default {
  name: 'ScreenHeader',
  data() {
    return {
      displayTime: '',
      tick: null
    }
  },
  computed: {
    dashActive() {
      return this.$route.path === '/admin/dashboard'
    }
  },
  mounted() {
    this.tickTime()
    this.tick = setInterval(this.tickTime, 1000)
  },
  beforeDestroy() {
    if (this.tick) clearInterval(this.tick)
  },
  methods: {
    goOverview() {
      if (this.$route.path === '/admin/dashboard') return
      this.$router.push('/admin/dashboard')
    },
    async goBackend() {
      if (this.$route.path === '/admin/users' || this.$route.path === '/admin/cases') return
      const loader = showFullscreenLoading('正在进入后台管理')
      await this.$nextTick()
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
      try {
        await this.$router.push('/admin/users')
      } finally {
        loader.close()
      }
    },
    tickTime() {
      const now = new Date()
      const y = now.getFullYear()
      const m = String(now.getMonth() + 1).padStart(2, '0')
      const d = String(now.getDate()).padStart(2, '0')
      const h = String(now.getHours()).padStart(2, '0')
      const min = String(now.getMinutes()).padStart(2, '0')
      const s = String(now.getSeconds()).padStart(2, '0')
      this.displayTime = `${y}-${m}-${d} ${h}:${min}:${s}`
    }
  }
}
</script>

<style lang="less" scoped>
.screen-header-tmpl {
  display: flex;
  width: 100%;
  padding: 10px 24px 0;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left h1 {
  color: #fff;
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.5px;
}
.header-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 8px;
}
.nav-click {
  cursor: pointer;
}
.cool-border {
  position: relative;
}
.corner {
  position: absolute;
  width: 0;
  height: 0;
  border: 5px solid transparent;
  pointer-events: none;
}
.corner.top-left {
  top: 0;
  left: 0;
  border-top-color: #fff;
  border-left-color: #fff;
}
.corner.top-right {
  top: 0;
  right: 0;
  border-top-color: #fff;
  border-right-color: #fff;
}
.corner.bottom-left {
  bottom: 0;
  left: 0;
  border-bottom-color: #fff;
  border-left-color: #fff;
}
.corner.bottom-right {
  bottom: 0;
  right: 0;
  border-bottom-color: #fff;
  border-right-color: #fff;
}
.header-nav-item {
  margin-right: 4px;
  padding: 10px 28px;
  border: 1px solid transparent;
  border-radius: 80px;
}
.header-nav-item.active {
  background: #1b2d4a;
}
.nav {
  text-decoration: none;
  color: #52a2e4;
  font-size: 15px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.header-time {
  color: #52a2e4;
  font-size: 17px;
  font-variant-numeric: tabular-nums;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.content {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
