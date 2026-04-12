<template>
  <div class="case-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>病例管理</h1>
      <p>管理所有病例数据，支持增删改查</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <!-- 新增病例按钮 -->
      <el-button class="btn-primary-glow glass-btn glass-btn--primary" icon="el-icon-plus" @click="showAddDialog">新增病例</el-button>
      <!-- 刷新按钮 -->
      <el-button class="btn-ghost glass-btn glass-btn--soft" icon="el-icon-refresh" @click="loadCases">刷新</el-button>
      <!-- 查询输入框和操作 -->
      <div class="query-box">
        <input v-model.trim="searchCaseId" type="number" placeholder="按ID查询，如 12" @keyup.enter="handleSearch" />
        <el-button class="btn-ghost glass-btn glass-btn--soft" @click="handleSearch">查询</el-button>
        <el-button class="btn-ghost glass-btn glass-btn--soft" @click="resetSearch">清空</el-button>
      </div>
    </div>

    <!-- 病例列表卡片 -->
    <div class="table-card glass-card">
      <template v-if="dataReady">
        <!-- 数据为空提示 -->
        <div v-if="cases.length === 0" class="empty-state">
          <p>暂无病例数据</p>
        </div>
        <!-- 病例表格显示 -->
        <div v-else class="table-wrapper">
        <table class="case-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>类型</th>
              <th>性别</th>
              <th>年龄</th>
              <th>身高</th>
              <th>体重</th>
              <th>医生</th>
              <th>医院</th>
              <th>科室</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <!-- 使用 v-for 动态渲染病例数据列表 -->
            <tr v-for="item in cases" :key="item.id">
              <td>{{ item.id }}</td>
              <td><span class="type-tag">{{ item.type || '-' }}</span></td>
              <td>{{ item.gender || '-' }}</td>
              <td>{{ item.age || '-' }}</td>
              <td>{{ item.height || '-' }}</td>
              <td>{{ item.weight || '-' }}</td>
              <td>{{ item.docName || '-' }}</td>
              <td>{{ item.docHospital || '-' }}</td>
              <td>{{ item.department || '-' }}</td>
              <td>
                <div class="action-buttons">
                  <!-- 编辑按钮 -->
                  <button class="btn-edit" @click="showEditDialog(item)">编辑</button>
                  <!-- 删除按钮 -->
                  <button class="btn-delete" @click="deleteCase(item.id)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </template>
      <div v-else class="loading-placeholder" aria-hidden="true" />

      <!-- 分页显示 -->
      <div v-if="dataReady && cases.length > 0" class="pagination">
        <!-- 上一页按钮：页码为1时禁用 -->
        <button @click="prevPage" :disabled="page === 1">上一页</button>
        <!-- 当前页和总页数 -->
        <span>第 {{ page }} / {{ totalPages || 1 }} 页（共 {{ total }} 条）</span>
        <!-- 下一页按钮：到达最大页数时禁用 -->
        <button @click="nextPage" :disabled="page >= totalPages">下一页</button>
        <!-- 跳页控件 -->
        <div class="page-jump">
          <span>跳转到</span>
          <input v-model.number="pageInput" type="number" min="1" :max="totalPages || 1" @keyup.enter="jumpToPage" />
          <span>页</span>
          <button @click="jumpToPage">确定</button>
        </div>
      </div>
    </div>

    <!-- 新增/编辑 病例弹窗 -->
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="closeDialog">
      <div class="dialog-box glass-card">
        <div class="dialog-header">
          <!-- 根据 isEdit 的值切换弹窗标题 -->
          <h3>{{ isEdit ? '编辑病例' : '新增病例' }}</h3>
          <button class="btn-close" @click="closeDialog">×</button>
        </div>
        
        <!-- 表单内容 -->
        <div class="dialog-body">
          <!-- 必填：疾病类型和性别 -->
          <div class="form-row">
            <div class="form-group">
              <label>疾病类型 *</label>
              <input v-model="formData.type" placeholder="请输入疾病类型" />
            </div>
            <div class="form-group">
              <label>性别 *</label>
              <el-select
                v-model="formData.gender"
                placeholder="请选择"
                clearable
                class="case-el-select"
                popper-class="case-mgmt-select-dropdown"
              >
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </div>
          </div>

          <!-- 关联用户ID、年龄、就诊时间 -->
          <div class="form-row form-row-3">
            <div class="form-group">
              <label>关联用户ID</label>
              <input
                v-model="formData.user_id"
                type="text"
                inputmode="numeric"
                autocomplete="off"
                placeholder="可选，填写 users.id（正整数）"
                @blur="validateUserIdField"
              />
              <p v-if="formErrors.user_id" class="field-error">{{ formErrors.user_id }}</p>
            </div>
            <div class="form-group">
              <label>年龄</label>
              <input
                v-model="formData.age"
                type="text"
                inputmode="numeric"
                autocomplete="off"
                placeholder="可选，0-150 的整数"
                @blur="validateAgeField"
              />
              <p v-if="formErrors.age" class="field-error">{{ formErrors.age }}</p>
            </div>
            <div class="form-group">
              <label>就诊时间</label>
              <el-date-picker
                v-model="formData.time"
                type="date"
                placeholder="选择日期"
                value-format="yyyy-MM-dd"
                clearable
                class="case-el-date"
                popper-class="case-mgmt-picker-dropdown"
              />
            </div>
          </div>

          <!-- 身高和体重 -->
          <div class="form-row">
            <div class="form-group">
              <label>身高(cm)</label>
              <input v-model="formData.height" type="number" min="0" step="0.1" placeholder="请输入身高" />
            </div>
            <div class="form-group">
              <label>体重(kg)</label>
              <input v-model="formData.weight" type="number" min="0" step="0.1" placeholder="请输入体重" />
            </div>
          </div>

          <!-- 患病时长以及过敏史 -->
          <div class="form-row">
            <div class="form-group">
              <label>患病时长</label>
              <input v-model="formData.illDuration" placeholder="如：3天、1周" />
            </div>
            <div class="form-group">
              <label>过敏史</label>
              <input v-model="formData.allergy" placeholder="请输入过敏史" />
            </div>
          </div>

          <!-- 症状描述文本域 -->
          <div class="form-group">
            <label>症状描述</label>
            <textarea v-model="formData.content" placeholder="请输入症状描述" rows="3"></textarea>
          </div>

          <!-- 医生姓名/医院 -->
          <div class="form-row">
            <div class="form-group">
              <label>医生姓名</label>
              <input v-model="formData.docName" placeholder="请输入医生姓名" />
            </div>
            <div class="form-group">
              <label>所属医院</label>
              <input v-model="formData.docHospital" placeholder="请输入医院名称" />
            </div>
          </div>

          <!-- 科室 -->
          <div class="form-group">
            <label>科室</label>
            <input v-model="formData.department" placeholder="请输入科室" />
          </div>
        </div>

        <!-- 弹窗底部操作按钮 -->
        <div class="dialog-footer">
          <button type="button" class="btn-dialog-cancel glass-btn glass-btn--soft" @click="closeDialog">取消</button>
          <button type="button" class="btn-dialog-submit glass-btn glass-btn--primary" @click="submitForm">{{ isEdit ? '保存' : '新增' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { adminGetCases, adminCreateCase, adminUpdateCase, adminDeleteCase } from '@/api/admin'

export default {
  name: 'CaseManagement',
  data() {
    return {
      // 病例数据列表
      cases: [],
      // 首次列表请求完成后为 true，避免全屏 Loading 时误显「暂无数据」
      dataReady: false,
      // 当前分页
      page: 1,
      pageSize: 10, // 每页显示条数
      total: 0, // 总病例数
      searchCaseId: '', // 查询输入
      pageInput: 1, // 跳页输入
      // 弹窗及表单相关
      dialogVisible: false, // 弹窗是否可见
      isEdit: false, // 用于区分是新增还是编辑
      formErrors: {
        user_id: '',
        age: ''
      },
      formData: {
        type: '',
        gender: '',
        age: '',
        time: null,
        content: '',
        docName: '',
        docHospital: '',
        department: '',
        detailUrl: '',
        height: '',
        weight: '',
        illDuration: '',
        allergy: '',
        user_id: ''
      }
    }
  },
  computed: {
    // 总页数计算属性
    totalPages() {
      if (!this.total || !this.pageSize) return 1
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    }
  },
  mounted() {
    // 页面初始化自动加载病例
    this.loadCases()
  },
  methods: {
    openDashLoading() {
      return this.$loading({
        lock: true,
        text: 'Loading...',
        spinner: 'el-icon-loading',
        background: 'rgba(3, 10, 28, 0.92)',
        customClass: 'screen-dash-loading'
      })
    },
    validateUserIdField() {
      const raw = this.formData.user_id
      if (raw === '' || raw === null || raw === undefined) {
        this.formErrors.user_id = ''
        return true
      }
      const s = String(raw).trim()
      if (!/^\d+$/.test(s)) {
        this.formErrors.user_id = '须为正整数'
        return false
      }
      const n = Number(s)
      if (!Number.isFinite(n) || n < 1) {
        this.formErrors.user_id = '须为正整数'
        return false
      }
      this.formErrors.user_id = ''
      return true
    },
    validateAgeField() {
      const raw = this.formData.age
      if (raw === '' || raw === null || raw === undefined) {
        this.formErrors.age = ''
        return true
      }
      const s = String(raw).trim()
      if (!/^-?\d+$/.test(s)) {
        this.formErrors.age = '须为 0-150 的整数'
        return false
      }
      const n = Number(s)
      if (!Number.isInteger(n) || n < 0 || n > 150) {
        this.formErrors.age = '须为 0-150 的整数'
        return false
      }
      this.formErrors.age = ''
      return true
    },
    // 加载病例列表数据
    async loadCases() {
      const loader = this.openDashLoading()
      await this.$nextTick()
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
      try {
        const res = await adminGetCases(this.page, this.pageSize, this.searchCaseId)
        if (res.code === 200) {
          // 正确返回数据，更新列表
          this.cases = res.data.cases || []
          this.total = Number(res.data.total || 0)
          this.page = Number(res.data.page || this.page)
          this.pageInput = this.page
        } else {
          // 错误提示
          this.$message.error(res.message || '加载失败')
        }
      } catch (e) {
        console.error('加载病例失败:', e)
        this.$message.error('加载失败，请刷新重试')
      } finally {
        this.dataReady = true
        try {
          if (loader) loader.close()
        } catch (e) {
          /* ignore */
        }
      }
    },
    
    // 上一页操作
    prevPage() {
      if (this.page > 1) {
        this.page--
        this.pageInput = this.page
        this.loadCases()
      }
    },
    
    // 下一页操作
    nextPage() {
      if (this.page < this.totalPages) {
        this.page++
        this.pageInput = this.page
        this.loadCases()
      }
    },
    // 查询操作
    handleSearch() {
      // 校验ID输入
      if (this.searchCaseId && !/^\d+$/.test(this.searchCaseId)) {
        this.$message.warning('病例ID必须是整数')
        return
      }
      this.page = 1
      this.pageInput = 1
      this.loadCases()
    },
    // 重置查询
    resetSearch() {
      this.searchCaseId = ''
      this.page = 1
      this.pageInput = 1
      this.loadCases()
    },
    // 跳转到指定页
    jumpToPage() {
      const target = Number(this.pageInput)
      if (!Number.isInteger(target) || target < 1 || target > this.totalPages) {
        this.$message.warning(`请输入 1 到 ${this.totalPages} 的页码`)
        this.pageInput = this.page
        return
      }
      if (target === this.page) return
      this.page = target
      this.loadCases()
    },
    
    // 打开新增病例对话框
    showAddDialog() {
      this.isEdit = false
      this.resetForm()
      this.dialogVisible = true
    },
    
    // 打开编辑病例对话框
    showEditDialog(item) {
      this.isEdit = true
      const copy = { ...item }
      if (copy.time != null && String(copy.time).length > 10) {
        copy.time = String(copy.time).slice(0, 10)
      }
      if (!copy.time) copy.time = null
      this.formData = copy
      this.formErrors = { user_id: '', age: '' }
      this.dialogVisible = true
    },
    
    // 关闭弹窗并重置表单
    closeDialog() {
      this.dialogVisible = false
      this.resetForm()
    },
    
    // 表单重置
    resetForm() {
      this.formData = {
        type: '',
        gender: '',
        age: '',
        time: null,
        content: '',
        docName: '',
        docHospital: '',
        department: '',
        detailUrl: '',
        height: '',
        weight: '',
        illDuration: '',
        allergy: '',
        user_id: ''
      }
      this.formErrors = { user_id: '', age: '' }
    },
    
    // 提交病例表单（新增或编辑）
    async submitForm() {
      // 必填校验
      if (!this.formData.type || !this.formData.gender) {
        this.$message.warning('请填写必填项（疾病类型、性别）')
        return
      }
      this.validateUserIdField()
      this.validateAgeField()
      if (this.formErrors.user_id || this.formErrors.age) {
        this.$message.warning('请修正关联用户ID或年龄的格式')
        return
      }
      const h = this.formData.height
      const w = this.formData.weight
      if (h !== '' && h !== null && Number(h) < 0) {
        this.$message.warning('身高不能为负数')
        return
      }
      if (w !== '' && w !== null && Number(w) < 0) {
        this.$message.warning('体重不能为负数')
        return
      }
      
      let loader = null
      try {
        loader = this.$loading({
          lock: true,
          text: this.isEdit ? '保存中...' : '提交中...',
          spinner: 'el-icon-loading',
          background: 'rgba(3, 10, 28, 0.92)',
          customClass: 'screen-dash-loading'
        })
        const payload = {
          ...this.formData,
          time: this.formData.time == null || this.formData.time === '' ? '' : this.formData.time
        }
        let res
        if (this.isEdit) {
          // 编辑病例
          res = await adminUpdateCase(this.formData.id, payload)
        } else {
          // 新增病例
          res = await adminCreateCase(payload)
        }
        
        if (res.code === 200) {
          // 操作成功提示
          this.$message.success(this.isEdit ? '修改成功' : '新增成功')
          this.closeDialog()
          this.loadCases()
        } else {
          this.$message.error(res.message || '操作失败')
        }
      } catch (e) {
        console.error('提交失败:', e)
        this.$message.error('操作失败，请重试')
      } finally {
        if (loader) loader.close()
      }
    },
    
    // 删除病例
    async deleteCase(id) {
      try {
        // 确认弹窗
        await this.$confirm('确定要删除这条病例吗？', '提示', {
          type: 'warning',
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        })
      } catch (e) {
        // 用户取消
        return
      }
      
      try {
        // 发起删除请求
        const res = await adminDeleteCase(id)
        if (res.code === 200) {
          this.$message.success('删除成功')
          this.loadCases()
        } else {
          this.$message.error(res.message || '删除失败')
        }
      } catch (e) {
        console.error('删除失败:', e)
        this.$message.error('删除失败，请重试')
      }
    }
  }
}
</script>

<style scoped>
.case-management {
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

.action-bar {
  margin-bottom: var(--sp-2);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-1);
}
.query-box {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.query-box input {
  width: 180px;
  padding: 8px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: #111a2a;
  color: var(--text);
}
.query-box input:focus {
  outline: none;
  border-color: #8fc0f1;
}

.table-card {
  background: var(--panel);
  border-radius: var(--radius);
  padding: var(--sp-2);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
}
.table-card:hover {
  transform: translateY(var(--hover-lift-y));
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

.loading-placeholder {
  min-height: 240px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.field-error {
  margin: 6px 0 0;
  font-size: var(--fs-12);
  color: var(--error);
}

.case-el-select {
  width: 100%;
}
.case-el-date {
  width: 100%;
}
.case-el-date.el-date-editor.el-input {
  width: 100%;
}

.table-wrapper { overflow-x: auto; }

.case-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
}

.case-table thead { background: var(--bg-2); }

.case-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: var(--fw-bold);
  color: var(--text-muted);
  font-size: var(--fs-12);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.case-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  font-size: var(--fs-14);
}

.case-table tbody tr:hover { background: var(--bg-2); }

.type-tag {
  background: linear-gradient(145deg, #2f80ed, #55a8ff);
  color: #fff;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.action-buttons { display: flex; gap: 8px; }

.btn-edit,
.btn-delete {
  padding: 6px 12px;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-edit { background: #1b2940; color: #8dc2ff; border: 1px solid #2f4f78; }
.btn-edit:hover { background: #233451; }

.btn-delete { background: rgba(239, 68, 68, 0.16); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }
.btn-delete:hover { background: rgba(239, 68, 68, 0.24); }

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--sp-2);
  margin-top: var(--sp-2);
  padding-top: var(--sp-1);
  border-top: 1px solid var(--border);
}

.pagination button {
  padding: 10px 16px;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: var(--fs-14);
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) { 
  transform: translateY(var(--hover-lift-y));
  box-shadow: var(--hover-glow-shadow);
}
.pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
.pagination span { color: var(--text-muted); font-weight: var(--fw-medium); }
.page-jump {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
}
.page-jump input {
  width: 70px;
  padding: 8px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: #111a2a;
  color: var(--text);
}
.page-jump button {
  padding: 8px 12px;
  background: #1b2940;
  color: #8dc2ff;
  border: 1px solid #2f4f78;
  border-radius: var(--radius);
  cursor: pointer;
}
.page-jump button:hover {
  background: #233451;
}

.dialog-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog-box {
  background: var(--panel);
  border-radius: var(--radius);
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  transition: border-color 0.28s ease, box-shadow 0.28s ease;
}
.dialog-box:hover {
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

.dialog-header {
  padding: var(--sp-2);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  font-size: var(--fs-16);
  color: var(--text);
  font-weight: var(--fw-bold);
}

.btn-close {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  color: var(--text);
  transition: all 0.2s;
}

.btn-close:hover { background: #1b2940; }

.dialog-body { padding: var(--sp-2); }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-1);
  margin-bottom: var(--sp-1);
}
.form-row-3 { grid-template-columns: 1fr 1fr 1fr; }

.form-group { margin-bottom: var(--sp-1); }
.form-group label {
  display: block;
  font-size: var(--fs-12);
  font-weight: var(--fw-medium);
  color: var(--text-muted);
  margin-bottom: 6px;
}
.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: var(--fs-14);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text);
}
.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: rgba(58, 161, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(58, 161, 255, 0.12);
}
.form-group textarea { resize: vertical; font-family: inherit; }
.case-table td,
.case-table th {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dialog-footer {
  padding: var(--sp-1) var(--sp-2) var(--sp-2);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-1);
}

.btn-dialog-cancel {
  min-width: 94px;
}

.btn-dialog-submit {
  min-width: 102px;
}

@media (max-width: 768px) {
  .query-box {
    margin-left: 0;
    width: 100%;
  }
  .query-box input {
    width: 100%;
  }
  .form-row { grid-template-columns: 1fr; }
  .form-row-3 { grid-template-columns: 1fr; }
  .case-table { min-width: 100%; }
}
</style>

<style>
/* el-select / el-date-picker 下拉挂在 body，需全局类名 */
.case-mgmt-select-dropdown.el-select-dropdown {
  background: #0f1729;
  border: 1px solid rgba(82, 162, 228, 0.45);
}
.case-mgmt-select-dropdown .el-select-dropdown__item {
  color: #dbe8fb;
}
.case-mgmt-select-dropdown .el-select-dropdown__item.selected {
  color: #5ecfff;
  font-weight: 600;
  background: rgba(58, 161, 255, 0.12);
}
.case-mgmt-select-dropdown .el-select-dropdown__item.hover,
.case-mgmt-select-dropdown .el-select-dropdown__item:hover {
  background: rgba(58, 161, 255, 0.18);
}

.case-mgmt-picker-dropdown.el-picker-panel,
.case-mgmt-picker-dropdown .el-picker-panel__body,
.case-mgmt-picker-dropdown .el-picker-panel__content,
.case-mgmt-picker-dropdown .el-picker-panel__footer {
  background: #0f1729;
  border-color: rgba(82, 162, 228, 0.35);
  color: #dbe8fb;
}
.case-mgmt-picker-dropdown .el-date-picker__header,
.case-mgmt-picker-dropdown .el-date-picker__time-header {
  border-bottom-color: rgba(82, 162, 228, 0.25);
}
.case-mgmt-picker-dropdown .el-picker-panel__icon-btn,
.case-mgmt-picker-dropdown .el-date-picker__prev-btn,
.case-mgmt-picker-dropdown .el-date-picker__next-btn {
  color: #8ea5c3;
}
.case-mgmt-picker-dropdown .el-date-picker__header-label {
  color: #dbe8fb;
}
.case-mgmt-picker-dropdown .el-date-table th {
  color: #8ea5c3;
  border-bottom-color: rgba(82, 162, 228, 0.2);
}
.case-mgmt-picker-dropdown .el-date-table td {
  border-color: rgba(82, 162, 228, 0.12);
}
.case-mgmt-picker-dropdown .el-date-table td.available span {
  color: #dbe8fb;
}
.case-mgmt-picker-dropdown .el-date-table td.today span {
  color: #5ecfff;
  font-weight: 600;
}
.case-mgmt-picker-dropdown .el-date-table td.current:not(.disabled) span {
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: #fff;
}
.case-mgmt-picker-dropdown .el-date-table td.in-range div,
.case-mgmt-picker-dropdown .el-date-table td.in-range div:hover {
  background: rgba(58, 161, 255, 0.15);
}
.case-mgmt-picker-dropdown .el-year-table td .cell:hover,
.case-mgmt-picker-dropdown .el-month-table td .cell:hover {
  color: #5ecfff;
}
</style>
