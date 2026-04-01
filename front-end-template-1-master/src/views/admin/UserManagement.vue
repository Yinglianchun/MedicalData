<template>
  <div class="user-management">
    <div class="page-header">
      <h1>用户管理</h1>
      <p>管理系统用户权限和状态</p>
    </div>

    <!-- 工具栏：搜索 + 新增 -->
    <div class="toolbar">
      <div class="search-box">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="输入用户名（模糊）或 ID（精确）..."
          @keyup.enter="loadUsers"
        />
        <span class="search-mode-tag" :class="isIdSearch ? 'tag-id' : 'tag-name'">
          {{ isIdSearch ? 'ID 精确' : '用户名模糊' }}
        </span>
        <button class="btn-search" @click="loadUsers">搜索</button>
        <button class="btn-reset" @click="resetSearch">重置</button>
      </div>
      <button class="btn-primary" @click="openCreate">+ 新增用户</button>
    </div>

    <!-- 用户列表 -->
    <div class="table-card">
      <div class="table-header">
        <h3>用户列表</h3>
        <button class="btn-refresh" @click="loadUsers">刷新</button>
      </div>

      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>

      <div v-else-if="users.length === 0" class="empty-state">
        <p>暂无用户数据</p>
      </div>

      <table v-else class="user-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>
              <div class="user-name">
                <span class="user-avatar">{{ user.username.charAt(0).toUpperCase() }}</span>
                {{ user.username }}
              </div>
            </td>
            <td>
              <span class="role-badge" :class="user.role === 'admin' ? 'role-admin' : 'role-user'">
                {{ user.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td>
              <span class="status-badge" :class="user.status === 1 ? 'status-active' : 'status-disabled'">
                {{ user.status === 1 ? '正常' : '禁用' }}
              </span>
            </td>
            <td>{{ formatTime(user.create_time) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-action btn-edit" @click="openEdit(user)">编辑</button>
                <button
                  v-if="user.status === 1"
                  class="btn-action btn-disable"
                  @click="toggleUserStatus(user.id, 0)"
                  :disabled="user.role === 'admin'"
                >禁用</button>
                <button
                  v-else
                  class="btn-action btn-enable"
                  @click="toggleUserStatus(user.id, 1)"
                >启用</button>
                <button
                  class="btn-action btn-delete"
                  @click="deleteUser(user)"
                  :disabled="user.role === 'admin'"
                >删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <div class="stat-box">
        <div class="stat-icon" style="background: linear-gradient(135deg, #3f8cff 0%, #33c5c9 100%)"><span>U</span></div>
        <div class="stat-content">
          <p>总用户数</p>
          <h2>{{ users.length }}</h2>
        </div>
      </div>
      <div class="stat-box">
        <div class="stat-icon" style="background: linear-gradient(135deg, #3f8cff 0%, #33c5c9 100%)"><span>N</span></div>
        <div class="stat-content">
          <p>正常用户</p>
          <h2>{{ activeUserCount }}</h2>
        </div>
      </div>
      <div class="stat-box">
        <div class="stat-icon" style="background: linear-gradient(135deg, #3f8cff 0%, #33c5c9 100%)"><span>D</span></div>
        <div class="stat-content">
          <p>禁用用户</p>
          <h2>{{ disabledUserCount }}</h2>
        </div>
      </div>
      <div class="stat-box">
        <div class="stat-icon" style="background: linear-gradient(135deg, #3f8cff 0%, #33c5c9 100%)"><span>A</span></div>
        <div class="stat-content">
          <p>管理员</p>
          <h2>{{ adminCount }}</h2>
        </div>
      </div>
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <div v-if="dialogVisible" class="modal-overlay" @click.self="closeDialog">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ isEdit ? '编辑用户' : '新增用户' }}</h3>
          <button class="modal-close" @click="closeDialog">×</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>用户名 <span class="required">*</span></label>
            <input v-model="form.username" class="form-input" placeholder="请输入用户名" maxlength="50" />
          </div>
          <div class="form-item">
            <label>密码 {{ isEdit ? '（不填则不修改）' : '' }} <span v-if="!isEdit" class="required">*</span></label>
            <input v-model="form.password" class="form-input" type="password" placeholder="请输入密码" maxlength="50" />
          </div>
          <div class="form-item">
            <label>角色 <span class="required">*</span></label>
            <select v-model="form.role" class="form-select">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div class="form-item">
            <label>状态</label>
            <select v-model="form.status" class="form-select">
              <option :value="1">正常</option>
              <option :value="0">禁用</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeDialog">取消</button>
          <button class="btn-confirm" @click="submitForm" :disabled="submitting">
            {{ submitting ? '提交中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  adminGetUsers,
  adminUpdateUserStatus,
  adminCreateUser,
  adminUpdateUser,
  adminDeleteUser
} from '@/api/admin'

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      loading: false,
      searchKeyword: '',
      dialogVisible: false,
      isEdit: false,
      submitting: false,
      editId: null,
      form: {
        username: '',
        password: '',
        role: 'user',
        status: 1
      }
    }
  },
  computed: {
    // 判断搜索框输入是否为纯数字（按 ID 搜索）
    isIdSearch() {
      return /^\d+$/.test(this.searchKeyword.trim())
    },
    activeUserCount() {
      return this.users.filter(u => u.status === 1).length
    },
    disabledUserCount() {
      return this.users.filter(u => u.status === 0).length
    },
    adminCount() {
      return this.users.filter(u => u.role === 'admin').length
    }
  },
  mounted() {
    this.loadUsers()
  },
  methods: {
    async loadUsers() {
      this.loading = true
      const kw = this.searchKeyword.trim()
      const params = this.isIdSearch && kw ? { id: kw } : { username: kw }
      try {
        const res = await adminGetUsers(params)
        if (res.code === 200) {
          this.users = res.data.users || []
        } else {
          this.$message.error(res.message || '加载失败')
        }
      } catch (e) {
        this.$message.error('加载失败，请刷新重试')
      } finally {
        this.loading = false
      }
    },

    resetSearch() {
      this.searchKeyword = ''
      this.loadUsers()
    },

    async toggleUserStatus(userId, newStatus) {
      const action = newStatus === 1 ? '启用' : '禁用'
      try {
        await this.$confirm(`确定要${action}该用户吗？`, '提示', {
          type: 'warning',
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        })
      } catch {
        return
      }
      try {
        const res = await adminUpdateUserStatus(userId, newStatus)
        if (res.code === 200) {
          this.$message.success(`${action}成功`)
          const user = this.users.find(u => u.id === userId)
          if (user) user.status = newStatus
        } else {
          this.$message.error(res.message || `${action}失败`)
        }
      } catch {
        this.$message.error(`${action}失败，请重试`)
      }
    },

    openCreate() {
      this.isEdit = false
      this.editId = null
      this.form = { username: '', password: '', role: 'user', status: 1 }
      this.dialogVisible = true
    },

    openEdit(user) {
      this.isEdit = true
      this.editId = user.id
      this.form = {
        username: user.username,
        password: '',
        role: user.role,
        status: user.status
      }
      this.dialogVisible = true
    },

    closeDialog() {
      this.dialogVisible = false
    },

    async submitForm() {
      if (!this.form.username.trim()) {
        this.$message.warning('用户名不能为空')
        return
      }
      if (!this.isEdit && !this.form.password.trim()) {
        this.$message.warning('密码不能为空')
        return
      }
      this.submitting = true
      try {
        let res
        if (this.isEdit) {
          res = await adminUpdateUser(this.editId, this.form)
        } else {
          res = await adminCreateUser(this.form)
        }
        if (res.code === 200) {
          this.$message.success(this.isEdit ? '修改成功' : '创建成功')
          this.closeDialog()
          this.loadUsers()
        } else {
          this.$message.error(res.message || '操作失败')
        }
      } catch {
        this.$message.error('操作失败，请重试')
      } finally {
        this.submitting = false
      }
    },

    async deleteUser(user) {
      try {
        await this.$confirm(
          `确定要删除用户 "${user.username}" 吗？此操作不可恢复！`,
          '警告',
          {
            type: 'error',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
          }
        )
      } catch {
        return
      }
      try {
        const res = await adminDeleteUser(user.id)
        if (res.code === 200) {
          this.$message.success('删除成功')
          this.users = this.users.filter(u => u.id !== user.id)
        } else {
          this.$message.error(res.message || '删除失败')
        }
      } catch {
        this.$message.error('删除失败，请重试')
      }
    },

    formatTime(timeStr) {
      if (!timeStr) return '-'
      return timeStr.split(' ')[0] || timeStr.substring(0, 10)
    }
  }
}
</script>

<style scoped>
.user-management {
  padding: var(--sp-2);
  color: var(--text);
}

.page-header {
  margin-bottom: var(--sp-2);
}

.page-header h1 {
  font-size: var(--fs-20);
  color: var(--text);
  margin: 0 0 var(--sp-1) 0;
  font-weight: var(--fw-bold);
}

.page-header p {
  color: var(--text-muted);
  margin: 0;
  font-size: var(--fs-14);
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-2);
  gap: var(--sp-1);
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  padding: 8px 14px;
  background: #111a2a;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 14px;
  width: 220px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #8fc0f1;
}

.search-mode-tag {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s;
}

.tag-id {
  background: rgba(250, 112, 154, 0.18);
  color: #fb7185;
  border: 1px solid rgba(250, 112, 154, 0.3);
}

.tag-name {
  background: rgba(58, 161, 255, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(58, 161, 255, 0.25);
}

.btn-search,
.btn-reset {
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-search {
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
}

.btn-reset {
  background: var(--bg-2);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.btn-search:hover { 
  transform: translateY(var(--hover-lift-y));
  box-shadow: var(--hover-glow-shadow);
}
.btn-reset:hover { background: #1b2940; color: var(--text); }

.btn-primary {
  padding: 8px 20px;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary:hover {
  transform: translateY(var(--hover-lift-y));
  box-shadow: var(--hover-glow-shadow);
}

/* 表格卡片 */
.table-card {
  background: var(--panel);
  border-radius: var(--radius);
  padding: var(--sp-2);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  margin-bottom: var(--sp-2);
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
}

.table-card:hover {
  transform: translateY(var(--hover-lift-y));
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-1);
  padding-bottom: var(--sp-1);
  border-bottom: 1px solid var(--border);
}

.table-header h3 {
  font-size: var(--fs-16);
  color: var(--text);
  margin: 0;
  font-weight: var(--fw-bold);
}

.btn-refresh {
  padding: 7px 16px;
  background: var(--bg-2);
  color: var(--text-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: #1b2940;
  color: var(--text);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

/* 用户表格 */
.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table thead {
  background: var(--bg-2);
}

.user-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: var(--fw-bold);
  color: var(--text-muted);
  font-size: var(--fs-12);
  border-bottom: 1px solid var(--border);
}

.user-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  font-size: var(--fs-14);
}

.user-table tbody tr:hover {
  background: var(--bg-2);
}

.user-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.role-admin {
  background: rgba(58, 161, 255, 0.18);
  color: var(--text);
  border: 1px solid var(--border);
}

.role-user {
  background: var(--bg-2);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.status-active {
  background: rgba(45, 212, 191, 0.15);
  color: #5eead4;
}

.status-disabled {
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-action {
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-edit {
  background: #1b2940;
  color: #2f80ed;
  border: 1px solid #c9e2fb;
}

.btn-edit:hover { background: #233451; }

.btn-enable {
  background: linear-gradient(145deg, #3aa1ff, #36d8c1);
  color: #0b1220;
}

.btn-enable:hover { filter: brightness(1.08); }

.btn-disable {
  background: #ef4444;
  color: white;
}

.btn-disable:hover { filter: brightness(1.08); }

.btn-delete {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.btn-delete:hover { background: rgba(239, 68, 68, 0.3); }

.btn-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 统计信息区 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-2);
}

.stat-box {
  background: var(--panel-2);
  border-radius: var(--radius);
  padding: var(--sp-2);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
}

.stat-box:hover {
  transform: translateY(var(--hover-lift-y));
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-content p {
  font-size: var(--fs-12);
  color: var(--text-muted);
  margin: 0 0 6px 0;
}

.stat-content h2 {
  font-size: var(--fs-20);
  font-weight: var(--fw-bold);
  color: var(--text);
  margin: 0;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  width: 420px;
  max-width: 92vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: fadeInUp 0.22s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
  transition: color 0.2s;
}

.modal-close:hover { color: var(--text); }

.modal-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

.required {
  color: #ef4444;
}

.form-input,
.form-select {
  padding: 10px 14px;
  background: #111a2a;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus {
  border-color: #8fc0f1;
}

.form-select option {
  background: var(--panel);
  color: var(--text);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border);
}

.btn-cancel {
  padding: 9px 20px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover { background: #1b2940; color: var(--text); }

.btn-confirm {
  padding: 9px 24px;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  border: none;
  border-radius: var(--radius);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(47, 128, 237, 0.35);
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 768px) {
  .toolbar { flex-direction: column; align-items: stretch; }
  .search-box { flex-wrap: wrap; }
  .user-table { font-size: 12px; }
  .user-table th, .user-table td { padding: 10px 8px; }
  .stats-section { grid-template-columns: 1fr 1fr; }
  .action-buttons { flex-direction: column; }
}
</style>
