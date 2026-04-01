<template>
  <div class="trend-redirect" />
</template>

<script>
export default {
  name: 'DashboardTrend',
  created() {
    if (this.$route.path !== '/admin/dashboard') {
      this.$router.replace('/admin/dashboard')
    }
  }
}
</script>

<style scoped>
.trend-redirect {
  display: none;
}
</style>
