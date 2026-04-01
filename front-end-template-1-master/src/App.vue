<template>
  <div id="app" class="app-root">
    <!-- 登录页面独立显示，不需要外层容器 -->
    <template v-if="isLoginPage">
      <router-view></router-view>
    </template>
    
    <!-- 其他页面使用原来的布局（如果需要） -->
    <template v-else>
      <transition name="fade" mode="out-in">
        <router-view></router-view>
      </transition>
    </template>
  </div>
</template>

<script>
export default {
  computed: {
    // 判断是否是登录页
    isLoginPage() {
      return this.$route.path === '/login'
    }
  }
}
</script>

<style>
/* 全局重置与暗色基调 */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--bg);
  color: var(--text);
}
#app { min-height: 100vh; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.24s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
