<template>
    <div id="header">
      <div id="header-left">
        <h1>医疗数据可视化分析系统</h1>
      </div>
      <div id="header-right">
        <div id="header-time">
          {{ currentDateTime }}
        </div>
        
        <div v-if="currentUser" class="user-area">
          <span class="user-name">
            {{ currentUser.username }}（{{ currentUser.role === 'admin' ? '管理员' : '用户' }}）
          </span>
          <button class="logout-btn" @click="showLogout = true">退出</button>
        </div>
      </div>
  
      <!-- 退出确认弹窗 -->
      <div v-if="showLogout" class="modal-mask">
        <div class="modal">
          <h3>确认退出登录？</h3>
          <p>退出后需要重新登录才能访问系统。</p>
          <div class="modal-actions">
            <button @click="confirmLogout" :disabled="loading">
              <span v-if="loading" class="spinner"></span>
              <span v-else>确认</span>
            </button>
            <button @click="showLogout = false" :disabled="loading">取消</button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import request from '@/api/axios'
  
  export default {
    data () {
      return {
        currentDateTime: this.getCurrentDateTime(),
        currentUser: null,
        showLogout: false,
        loading: false
      }
    },
    created () {
      this.interval = setInterval(() => {
        this.currentDateTime = this.getCurrentDateTime()
      }, 1000)
      this.loadCurrentUser()
    },
    methods: {
      async loadCurrentUser () {
        try {
          const res = await request({
            url: '/me',
            method: 'get'
          })
          if (res.code === 200) {
            this.currentUser = res.data
          } else {
            this.currentUser = null
          }
        } catch (e) {
          this.currentUser = null
        }
      },
      getCurrentDateTime () {
        const now = new Date()
        const year = now.getFullYear()
        const month = (now.getMonth() + 1).toString().padStart(2, '0')
        const day = now.getDate().toString().padStart(2, '0')
        const hours = now.getHours().toString().padStart(2, '0')
        const minutes = now.getMinutes().toString().padStart(2, '0')
        const seconds = now.getSeconds().toString().padStart(2, '0')
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
      },
      async confirmLogout () {
        this.loading = true
        try {
          await request({
            url: '/logout',
            method: 'post'
          })
        } catch (e) {
          // ignore
        }
        this.loading = false
        this.showLogout = false
        window.location.href = '/login'
      }
    }
  }
  </script>
  
  <style lang="less" scoped>
  #header {
    display: flex;
    padding: 10px 150px 0 150px;
    align-items: center;
    justify-content: space-between;
    #header-left {
      h1 {
        color: #fff;
        font-size: 23px;
      }
    }
    #header-right {
      display: flex;
      align-items: center;
    }
  }
  #header-time {
    color: #52a2e4;
    font-size: 17px;
    margin-right: 16px;
  }
  .portal-btn {
    margin-right: 12px;
    padding: 4px 12px;
    border-radius: 16px;
    border: 1px solid #52a2e4;
    background: transparent;
    color: #52a2e4;
    cursor: pointer;
  }
  .user-area {
    display: flex;
    align-items: center;
    color: #52a2e4;
  }
  .user-name {
    margin-right: 8px;
    font-size: 14px;
  }
  .logout-btn {
    padding: 4px 10px;
    border-radius: 12px;
    border: 1px solid #52a2e4;
    background: transparent;
    color: #52a2e4;
    cursor: pointer;
  }
  .logout-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }
  .modal-mask {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
  }
  .modal {
    background: #081221;
    padding: 20px 30px;
    border-radius: 8px;
    color: #fff;
    min-width: 260px;
  }
  .modal-actions {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
  .modal-actions button {
    margin-left: 8px;
    padding: 6px 14px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
  }
  .spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid #fff;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 4px;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  </style>
  