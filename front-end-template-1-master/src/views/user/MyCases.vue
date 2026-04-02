<template>
  <div class="my-cases-page">
    <section class="page-header">
      <span class="page-kicker">个人病例</span>
      <h1>我的病例记录</h1>
      <p>集中查看个人就诊记录、核心指标和就诊信息。</p>
    </section>

    <section class="stats-row">
      <div class="stat-card glass-card">
        <div class="stat-icon"><span>C</span></div>
        <div class="stat-content">
          <p>就诊记录</p>
          <h2>{{ cases.length }} 次</h2>
        </div>
      </div>

      <div class="stat-card glass-card">
        <div class="stat-icon"><span>H</span></div>
        <div class="stat-content">
          <p>最近就诊</p>
          <h2>{{ latestTime }}</h2>
        </div>
      </div>
    </section>

    <section class="cases-container glass-card">
      <AppLoading v-if="loading" label="正在加载病例记录..." compact></AppLoading>

      <div v-else-if="cases.length === 0" class="empty-state">
        <div class="empty-icon">CASE</div>
        <h3>暂无就诊记录</h3>
        <p>当前账号还没有病例数据，可以先体验病情预测流程。</p>
        <el-button type="primary" class="btn-goto-predict" @click="gotoPrediction">
          去进行病情预测
        </el-button>
      </div>

      <div v-else class="cases-list">
        <article v-for="(item, index) in cases" :key="item.id" class="case-card">
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
                <span class="info-value">{{ item.height ? `${item.height} cm` : '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">体重</span>
                <span class="info-value">{{ item.weight ? `${item.weight} kg` : '-' }}</span>
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
        </article>
      </div>
    </section>
  </div>
</template>

<script>
import { getMyCases } from '@/api/admin'
import AppLoading from '@/components/AppLoading.vue'

export default {
  name: 'MyCases',
  components: {
    AppLoading
  },
  data() {
    return {
      cases: [],
      loading: false
    }
  },
  computed: {
    latestTime() {
      if (this.cases.length === 0) return '-'
      const latest = this.cases[0]
      return latest.create_time ? this.formatDate(latest.create_time) : '-'
    }
  },
  mounted() {
    this.loadCases()
  },
  methods: {
    async loadCases() {
      this.loading = true
      try {
        const res = await getMyCases()
        if (res.code === 200) {
          this.cases = res.data.cases || []
        } else {
          this.$message.error(res.message || '加载失败')
        }
      } catch (error) {
        console.error('加载病例失败:', error)
        this.$message.error('加载失败，请刷新重试')
      } finally {
        this.loading = false
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return '-'
      return dateStr.split(' ')[0] || dateStr.substring(0, 10)
    },
    gotoPrediction() {
      this.$router.push('/user/predict')
    }
  }
}
</script>

<style scoped>
.my-cases-page {
  display: grid;
  gap: 24px;
  color: var(--text);
}

.page-kicker {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(63, 140, 255, 0.12);
  border: 1px solid rgba(82, 162, 228, 0.2);
  color: #9dc6ff;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.page-header h1 {
  margin: 0;
  font-size: 30px;
  color: var(--text);
}

.page-header p {
  margin: 12px 0 0;
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.7;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 22px;
  background: linear-gradient(180deg, rgba(16, 27, 49, 0.92), rgba(11, 19, 34, 0.86));
}

.stat-icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #2f80ed, #33c5c9);
  color: #04111f;
  font-size: 26px;
  font-weight: 700;
}

.stat-content p {
  margin: 0 0 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.stat-content h2 {
  margin: 0;
  font-size: 24px;
  color: var(--text);
}

.cases-container {
  padding: 24px;
  min-height: 360px;
  background: linear-gradient(180deg, rgba(16, 27, 49, 0.92), rgba(11, 19, 34, 0.88));
}

.empty-state {
  padding: 56px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 16px;
  color: rgba(142, 165, 195, 0.32);
  font-size: 44px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.empty-state h3 {
  margin: 0 0 10px;
  font-size: 22px;
  color: var(--text);
}

.empty-state p {
  margin: 0 0 24px;
  color: var(--text-muted);
  line-height: 1.7;
}

.btn-goto-predict {
  padding: 12px 28px;
}

.cases-list {
  display: grid;
  gap: 18px;
}

.case-card {
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(82, 162, 228, 0.16);
  background: rgba(11, 19, 34, 0.64);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.case-card:hover {
  transform: translateY(-1px);
  border-color: rgba(82, 162, 228, 0.32);
  box-shadow: 0 18px 32px rgba(6, 12, 24, 0.38);
}

.case-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(47, 128, 237, 0.92), rgba(51, 197, 201, 0.65));
}

.case-number {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.badge {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 12px;
}

.case-id,
.case-date {
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
}

.case-body {
  padding: 20px 18px 18px;
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
  color: var(--text-muted);
  font-size: 12px;
}

.info-value {
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}

.type-badge {
  display: inline-flex;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(63, 140, 255, 0.18);
  color: #dff3ff;
}

.symptom-section {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(82, 162, 228, 0.16);
  background: rgba(17, 26, 42, 0.74);
}

.symptom-content {
  margin: 8px 0 0;
  color: #a6bdd9;
  line-height: 1.7;
}

.medical-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(82, 162, 228, 0.12);
}

.medical-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #a6bdd9;
  font-size: 14px;
}

.medical-icon {
  padding: 3px 7px;
  border-radius: 8px;
  background: rgba(17, 26, 42, 0.82);
  border: 1px solid rgba(82, 162, 228, 0.18);
  color: var(--text);
  font-size: 12px;
  font-weight: 700;
}

.allergy-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(226, 102, 102, 0.08);
  border-left: 4px solid rgba(226, 102, 102, 0.9);
}

.allergy-icon,
.allergy-text {
  color: #f0aaaa;
  font-size: 14px;
}

@media (max-width: 768px) {
  .cases-container {
    padding: 18px;
  }

  .case-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .medical-info {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
