<template>
  <div class="my-cases">
    <div class="page-header">
      <h1>我的病例记录</h1>
      <p>查看您的个人就诊记录</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #2f80ed, #55a8ff)">
          <span>C</span>
        </div>
        <div class="stat-content">
          <p>就诊记录</p>
          <h2>{{ cases.length }} 次</h2>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #2f80ed, #55a8ff)">
          <span>H</span>
        </div>
        <div class="stat-content">
          <p>最近就诊</p>
          <h2>{{ latestTime }}</h2>
        </div>
      </div>
    </div>

    <!-- 病例列表 -->
    <div class="cases-container">
      <div v-if="loading" class="loading-state">
        <div class="loader"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="cases.length === 0" class="empty-state">
        <div class="empty-icon">CASE</div>
        <h3>暂无就诊记录</h3>
        <p>您还没有任何就诊记录</p>
        <el-button type="primary" class="btn-goto-predict" @click="gotoPrediction">
          去进行疾病预测
        </el-button>
      </div>

      <div v-else class="cases-list">
        <div v-for="(item, index) in cases" :key="item.id" class="case-card">
          <div class="case-header">
            <div class="case-number">
              <span class="badge">病例 #{{ index + 1 }}</span>
              <span class="case-id">ID: {{ item.id }}</span>
            </div>
            <div class="case-date">{{ formatDate(item.create_time) }}</div>
          </div>

          <div class="case-body">
            <div class="info-row">
              <div class="info-item">
                <span class="info-label">疾病类型</span>
                <span class="info-value type-badge">{{ item.type || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">性别</span>
                <span class="info-value">{{ item.gender || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">年龄</span>
                <span class="info-value">{{ item.age || '-' }}</span>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <span class="info-label">身高</span>
                <span class="info-value">{{ item.height ? item.height + ' cm' : '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">体重</span>
                <span class="info-value">{{ item.weight ? item.weight + ' kg' : '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">患病时长</span>
                <span class="info-value">{{ item.illDuration || '-' }}</span>
              </div>
            </div>

            <div v-if="item.content" class="symptom-section">
              <span class="info-label">症状描述</span>
              <p class="symptom-content">{{ item.content }}</p>
            </div>

            <div class="medical-info">
              <div class="medical-item">
                <span class="medical-icon">DR</span>
                <span>{{ item.docName || '未知医生' }}</span>
              </div>
              <div class="medical-item">
                <span class="medical-icon">HP</span>
                <span>{{ item.docHospital || '未知医院' }}</span>
              </div>
              <div class="medical-item">
                <span class="medical-icon">DP</span>
                <span>{{ item.department || '未知科室' }}</span>
              </div>
            </div>

            <div v-if="item.allergy && item.allergy !== '无'" class="allergy-section">
              <span class="allergy-icon">!</span>
              <span class="allergy-text">过敏史：{{ item.allergy }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getMyCases } from '@/api/admin'

export default {
  name: 'MyCases',
  data() {
    return {
      cases: [],
      loading: false
    }
  },
  computed: {
    // 最近就诊时间
    latestTime() {
      if (this.cases.length === 0) return '-'
      // 获取最新一条记录的时间
      const latest = this.cases[0]
      if (latest.create_time) {
        return this.formatDate(latest.create_time)
      }
      return '-'
    }
  },
  mounted() {
    this.loadCases()
  },
  methods: {
    // 加载个人病例
    async loadCases() {
      this.loading = true
      try {
        const res = await getMyCases()
        if (res.code === 200) {
          this.cases = res.data.cases || []
        } else {
          this.$message.error(res.message || '加载失败')
        }
      } catch (e) {
        console.error('加载病例失败:', e)
        this.$message.error('加载失败，请刷新重试')
      } finally {
        this.loading = false
      }
    },

    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return '-'
      // 如果是完整的datetime字符串，取日期部分
      const date = dateStr.split(' ')[0] || dateStr.substring(0, 10)
      return date
    },

    // 跳转到预测页面
    gotoPrediction() {
      this.$router.push('/user/predict')
    }
  }
}
</script>

<style scoped>
.my-cases {
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

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}

.stat-card {
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

.stat-card:hover {
  transform: translateY(var(--hover-lift-y));
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
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

/* 病例容器 */
.cases-container {
  background: var(--panel);
  border-radius: var(--radius);
  padding: var(--sp-2);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  min-height: 400px;
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
}

.cases-container:hover {
  transform: translateY(var(--hover-lift-y));
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loader {
  width: 50px;
  height: 50px;
  border: 4px solid var(--border);
  border-top-color: #2f80ed;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  margin-top: 16px;
  color: var(--text-muted);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.3;
  color: var(--text-muted);
  font-weight: 700;
  letter-spacing: 2px;
}

.empty-state h3 {
  font-size: var(--fs-16);
  color: var(--text);
  margin: 0 0 8px 0;
}

.empty-state p {
  color: var(--text-muted);
  margin: 0 0 24px 0;
  font-size: var(--fs-14);
}

.btn-goto-predict {
  padding: 12px 32px;
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: var(--fs-14);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-goto-predict:hover {
  transform: translateY(var(--hover-lift-y));
  box-shadow: var(--hover-glow-shadow);
}

/* 病例列表 */
.cases-list {
  display: grid;
  gap: var(--sp-2);
}

.case-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
}

.case-card:hover {
  transform: translateY(var(--hover-lift-y));
  border-color: var(--hover-glow-border);
  box-shadow: var(--hover-glow-shadow);
}

.case-header {
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.case-number {
  display: flex;
  align-items: center;
  gap: 12px;
}

.badge {
  background: rgba(255, 255, 255, 0.14);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.case-id {
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
}

.case-date {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--fs-14);
  font-weight: 500;
}

.case-body {
  padding: 20px;
  background: var(--panel);
}

.info-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: var(--fs-12);
  color: var(--text-muted);
  font-weight: 500;
}

.info-value {
  font-size: var(--fs-14);
  color: var(--text);
  font-weight: 600;
}

.type-badge {
  background: linear-gradient(135deg, #2f80ed, #55a8ff);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  display: inline-block;
  width: fit-content;
}

/* 症状描述 */
.symptom-section {
  margin-top: 16px;
  padding: 14px 16px;
  background: #111a2a;
  border-radius: var(--radius);
  border: 1px solid var(--border);
}

.symptom-content {
  margin: 8px 0 0 0;
  color: var(--text-muted);
  line-height: 1.6;
  font-size: var(--fs-14);
  word-break: break-word;
}

/* 医疗信息 */
.medical-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.medical-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-14);
  color: var(--text-muted);
  min-width: 0;
}

.medical-icon {
  font-size: 13px;
  font-weight: 700;
  background: var(--bg-2);
  padding: 3px 7px;
  border-radius: 8px;
  color: var(--text);
  border: 1px solid var(--border);
}

/* 过敏信息 */
.allergy-section {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border-radius: var(--radius);
  border-left: 4px solid #ef4444;
  display: flex;
  align-items: center;
  gap: 10px;
}

.allergy-icon {
  font-size: 18px;
  font-weight: 700;
  color: #fca5a5;
}

.allergy-text {
  color: #fca5a5;
  font-size: var(--fs-14);
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .info-row {
    grid-template-columns: 1fr;
  }

  .case-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .medical-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
