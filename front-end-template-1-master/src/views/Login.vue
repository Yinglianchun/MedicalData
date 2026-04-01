<template>
  <div class="login-shell">
    <div class="login-card glass-card">
      <section class="intro">
        <p class="badge">Medical Data Platform</p>
        <h1>医疗疾病数据分析平台</h1>
        <p class="lede">聚合病例数据，辅助完成趋势洞察与风险研判。</p>
        <div class="chips">
          <span class="chip">病例可视化看板</span>
          <span class="chip">分类预测与对比</span>
          <span class="chip">多角色权限协作</span>
        </div>
        <ul class="highlights">
          <li>聚焦核心指标：病例类型、年龄结构、性别占比一屏呈现</li>
          <li>内置疾病分类预测模型，支持输入症状文本快速研判</li>
          <li>管理员维护用户与病例，普通用户可查询个人病例记录</li>
        </ul>
      </section>

      <section class="form-panel">
        <div class="form-head">
          <h2>登录控制台</h2>
          <p class="sub">输入账号密码，进入数据大屏</p>
        </div>
        <form @submit.prevent="handleLogin">
          <label class="field">
            <span>账号</span>
            <el-input v-model="username" placeholder="请输入账号" size="large"></el-input>
          </label>
          <label class="field">
            <span>密码</span>
            <el-input v-model="password" type="password" placeholder="请输入密码" size="large" show-password></el-input>
          </label>
          <div class="row">
            <label class="remember">
              <input type="checkbox" v-model="remember" />
              <span>记住我</span>
            </label>
            <span class="muted">管理员可管理全局数据，用户可预测与查看病例</span>
          </div>
          <div class="btn-group">
            <el-button type="primary" native-type="submit" :loading="loading" class="btn-primary">{{ loading ? '登录中...' : '登录' }}</el-button>
            <el-button type="text" class="btn-text" @click.prevent="handleRegister" :disabled="loading">注册账号</el-button>
          </div>
        </form>
      </section>
    </div>

    <el-dialog title="注册账号" :visible.sync="registerVisible" width="420px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model.trim="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="registerForm.password" type="password" show-password placeholder="请输入密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="registerForm.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="registerVisible = false">取消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="submitRegister">提交注册</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { login, register } from '@/api/admin'

export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      remember: false,
      loading: false,
      registerVisible: false,
      registerLoading: false,
      registerForm: { username: '', password: '', confirmPassword: '' }
    }
  },
  methods: {
    async handleLogin() {
      if (!this.username || !this.password) {
        this.$message.warning('账号和密码不能为空')
        return
      }
      const loader = this.$loading({ lock: true, text: '登录中...', background: 'rgba(243, 247, 252, 0.85)' })
      try {
        this.loading = true
        const res = await login(this.username, this.password)
        if (res.code === 200) {
          this.$message.success('登录成功')
          const role = res.data.role
          if (this.remember) {
            // 简单记忆用户名
            localStorage.setItem('md-username', this.username)
          } else {
            localStorage.removeItem('md-username')
          }
          if (role === 'admin') this.$router.push('/admin/dashboard')
          else this.$router.push('/user/predict')
        } else {
          this.$message.error(res.message || '登录失败')
        }
      } catch (e) {
        console.error(e)
        this.$message.error('登录异常：' + (e.message || '请检查网络'))
      } finally {
        loader.close()
        this.loading = false
      }
    },
    handleRegister() {
      this.registerVisible = true
      this.registerForm = { username: '', password: '', confirmPassword: '' }
    },
    async submitRegister() {
      if (!this.registerForm.username || !this.registerForm.password) {
        this.$message.warning('用户名和密码不能为空')
        return
      }
      if (this.registerForm.password.length < 6) {
        this.$message.warning('密码长度至少6位')
        return
      }
      if (this.registerForm.password !== this.registerForm.confirmPassword) {
        this.$message.warning('两次输入密码不一致')
        return
      }
      try {
        this.registerLoading = true
        const res = await register(this.registerForm.username, this.registerForm.password)
        if (res.code === 200) {
          this.$message.success('注册成功，请登录')
          this.registerVisible = false
          this.username = this.registerForm.username
        } else {
          this.$message.error(res.message || '注册失败')
        }
      } catch (e) {
        console.error(e)
        this.$message.error('注册异常：' + (e.message || '请检查网络'))
      } finally {
        this.registerLoading = false
      }
    }
  },
  mounted() {
    const cached = localStorage.getItem('md-username')
    if (cached) {
      this.username = cached
      this.remember = true
    }
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(180deg, var(--bg), var(--bg-2));
  padding: var(--sp-4) var(--sp-2);
}

.login-card {
  width: min(1080px, 96vw);
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: var(--sp-3);
  padding: var(--sp-3);
}

.intro {
  padding: var(--sp-3);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--panel-2);
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #1b2940;
  color: var(--accent);
  font-size: var(--fs-12);
  margin-bottom: var(--sp-2);
}
.intro h1 {
  font-size: var(--fs-28);
  font-weight: var(--fw-bold);
  margin-bottom: var(--sp-2);
  color: var(--text);
}
.lede {
  color: var(--text-muted);
  font-size: var(--fs-16);
  margin-bottom: var(--sp-2);
  line-height: 1.6;
}
.chips { display: flex; flex-wrap: wrap; gap: var(--sp-1); margin-bottom: var(--sp-2); }
.chip {
  padding: 8px 12px;
  border-radius: 999px;
  background: #16243a;
  color: var(--text);
  font-size: var(--fs-12);
  border: 1px solid var(--border);
}
.highlights { list-style: none; padding: 0; margin: 0; display: grid; gap: var(--sp-1); color: var(--text-muted); font-size: var(--fs-14); }
.highlights li::before { content: '•'; color: var(--accent); margin-right: 8px; }

.form-panel {
  padding: var(--sp-3);
  border-radius: var(--radius);
  background: var(--panel);
  border: 1px solid var(--border);
}
.form-head h2 {
  margin: 0 0 var(--sp-1) 0;
  font-size: var(--fs-20);
  font-weight: var(--fw-bold);
}
.form-head .sub { margin: 0 0 var(--sp-2) 0; color: var(--text-muted); font-size: var(--fs-14); }

.field { display: grid; gap: 6px; margin-bottom: var(--sp-2); font-size: var(--fs-14); color: var(--text-muted); }

.row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--sp-2); gap: var(--sp-1); color: var(--text-muted); font-size: var(--fs-12); }
.remember { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }
.remember input { accent-color: var(--accent); }

.btn-group { display: flex; align-items: center; gap: var(--sp-1); }
.btn-primary { flex: 1; height: 44px; border-radius: var(--radius); background: linear-gradient(145deg, #2f80ed, #55a8ff); border: none; color: #fff; }
.btn-text { color: var(--accent); font-weight: var(--fw-medium); }

@media (max-width: 960px) {
  .login-card { grid-template-columns: 1fr; }
  .intro { order: 2; }
  .form-panel { order: 1; }
}
</style>
