<template>
  <div class="admin-page">
    <div class="admin-header">
      <h2>后台管理</h2>
      <button class="back-btn" @click="$router.push('/portal')">返回功能入口</button>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'users' }" @click="switchTab('users')">用户管理</button>
      <button :class="{ active: activeTab === 'cases' }" @click="switchTab('cases')">病例数据管理</button>
    </div>

    <!-- 用户管理 -->
    <div v-if="activeTab === 'users'" class="panel">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.role }}</td>
            <td>{{ u.status === 1 ? '正常' : '禁用' }}</td>
            <td>{{ u.create_time }}</td>
            <td>
              <button @click="toggleUserStatus(u)">
                {{ u.status === 1 ? '禁用' : '启用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 病例管理 -->
    <div v-else class="panel">
      <div class="toolbar">
        <button @click="openCreateCase">新增病例</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>类型</th>
            <th>性别</th>
            <th>年龄</th>
            <th>就诊时间</th>
            <th>医生</th>
            <th>医院</th>
            <th>科室</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in cases" :key="c.id">
            <td>{{ c.id }}</td>
            <td>{{ c.type }}</td>
            <td>{{ c.gender }}</td>
            <td>{{ c.age }}</td>
            <td>{{ c.time }}</td>
            <td>{{ c.docName }}</td>
            <td>{{ c.docHospital }}</td>
            <td>{{ c.department }}</td>
            <td>
              <button @click="editCase(c)">编辑</button>
              <button @click="removeCase(c)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 简单编辑/新增弹窗 -->
    <div v-if="showCaseDialog" class="modal-mask">
      <div class="modal">
        <h3>{{ editingCase && editingCase.id ? '编辑病例' : '新增病例' }}</h3>
        <div class="form-grid">
          <label>类型：<input v-model="editingCase.type" /></label>
          <label>性别：<input v-model="editingCase.gender" /></label>
          <label>年龄：<input v-model="editingCase.age" /></label>
          <label>就诊时间：<input v-model="editingCase.time" /></label>
          <label>医生：<input v-model="editingCase.docName" /></label>
          <label>医院：<input v-model="editingCase.docHospital" /></label>
          <label>科室：<input v-model="editingCase.department" /></label>
          <label>详情链接：<input v-model="editingCase.detailUrl" /></label>
          <label>身高：<input v-model="editingCase.height" /></label>
          <label>体重：<input v-model="editingCase.weight" /></label>
          <label>患病时长：<input v-model="editingCase.illDuration" /></label>
          <label>过敏史：<input v-model="editingCase.allergy" /></label>
        </div>
        <div class="modal-actions">
          <button @click="saveCase">保存</button>
          <button @click="showCaseDialog = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getCurrentUser,
  adminGetUsers,
  adminUpdateUserStatus,
  adminGetCases,
  adminCreateCase,
  adminUpdateCase,
  adminDeleteCase
} from '@/api/admin'

export default {
  name: 'Admin',
  data () {
    return {
      activeTab: 'users',
      users: [],
      cases: [],
      page: 1,
      size: 50,
      editingCase: null,
      showCaseDialog: false
    }
  },
  created () {
    this.checkAdmin()
  },
  methods: {
    async checkAdmin () {
      try {
        const res = await getCurrentUser()
        if (res.code !== 200 || !res.data || res.data.role !== 'admin') {
          this.$router.push('/login')
          return
        }
        this.loadUsers()
      } catch (e) {
        this.$router.push('/login')
      }
    },
    async loadUsers () {
      const res = await adminGetUsers()
      if (res.code === 200 && res.data) {
        this.users = res.data.users
      }
    },
    async toggleUserStatus (user) {
      const newStatus = user.status === 1 ? 0 : 1
      const res = await adminUpdateUserStatus(user.id, newStatus)
      if (res.code === 200) {
        user.status = newStatus
      }
    },
    async loadCases () {
      const res = await adminGetCases(this.page, this.size)
      if (res.code === 200 && res.data) {
        this.cases = res.data.cases
      }
    },
    async switchTab (tab) {
      this.activeTab = tab
      if (tab === 'users') {
        this.loadUsers()
      } else {
        this.loadCases()
      }
    },
    openCreateCase () {
      this.editingCase = {
        type: '',
        gender: '',
        age: '',
        time: '',
        content: '',
        docName: '',
        docHospital: '',
        department: '',
        detailUrl: '',
        height: '',
        weight: '',
        illDuration: '',
        allergy: ''
      }
      this.showCaseDialog = true
    },
    editCase (c) {
      this.editingCase = { ...c }
      this.showCaseDialog = true
    },
    async saveCase () {
      let res
      if (this.editingCase.id) {
        const { id, ...payload } = this.editingCase
        res = await adminUpdateCase(id, payload)
      } else {
        res = await adminCreateCase(this.editingCase)
      }
      if (res.code === 200) {
        this.showCaseDialog = false
        this.loadCases()
      }
    },
    async removeCase (c) {
      if (!window.confirm(`确认删除病例 ${c.id} 吗？`)) return
      const res = await adminDeleteCase(c.id)
      if (res.code === 200) {
        this.loadCases()
      }
    }
  }
}
</script>

<style scoped>
.admin-page {
  color: var(--text);
  padding: var(--sp-3);
  background: linear-gradient(180deg, var(--bg), var(--bg-2));
  min-height: 100vh;
}
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.back-btn {
  padding: 6px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}
.back-btn:hover {
  background: #dde9f7;
}
.tabs {
  margin-bottom: 12px;
}
.tabs button {
  margin-right: 8px;
  padding: 6px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}
.tabs button:hover {
  background: #dde9f7;
}
.tabs button.active {
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
  border-color: transparent;
}
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-2);
  box-shadow: var(--shadow);
}
.panel table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.panel th,
.panel td {
  border-bottom: 1px solid var(--border);
  padding: 6px 8px;
  text-align: left;
}
.panel th {
  background: var(--bg-2);
  color: var(--text-muted);
  font-weight: var(--fw-bold);
}
.panel td button {
  padding: 4px 10px;
  margin: 0 4px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #edf6ff;
  color: #2f80ed;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.panel td button:hover {
  background: #deefff;
}
.toolbar {
  margin-bottom: 8px;
}
.toolbar button {
  padding: 6px 12px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}
.toolbar button:hover {
  transform: translateY(var(--hover-lift-y));
  box-shadow: var(--hover-glow-shadow);
}
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}
.modal {
  background: var(--panel);
  padding: 20px 24px;
  border-radius: var(--radius);
  width: 520px;
  box-shadow: var(--shadow);
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 12px;
  margin-top: 12px;
}
.form-grid label {
  font-size: 12px;
  color: var(--text-muted);
}
.form-grid input {
  width: 100%;
  margin-top: 2px;
  padding: 8px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: #fbfdff;
  color: var(--text);
}
.form-grid input:focus {
  outline: none;
  border-color: #8fc0f1;
}
.modal-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.modal-actions button {
  padding: 8px 16px;
  border-radius: var(--radius);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.modal-actions button:first-child {
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
}
.modal-actions button:first-child:hover {
  transform: translateY(var(--hover-lift-y));
  box-shadow: var(--hover-glow-shadow);
}
.modal-actions button:last-child {
  background: var(--bg-2);
  color: var(--text);
  border: 1px solid var(--border);
}
.modal-actions button:last-child:hover {
  background: #dde9f7;
}
</style>

