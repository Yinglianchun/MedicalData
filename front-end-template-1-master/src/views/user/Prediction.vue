<template>
  <div class="prediction-page">
    <section class="hero-panel glass-card">
      <div class="hero-copy">
        <span class="hero-kicker">个人健康服务</span>
        <div class="hero-title-row">
          <img :src="logoImg" class="hero-logo" alt="Medical Data logo" />
          <div>
            <h1>病情初步预测</h1>
            <p>把症状描述清楚，系统会给出一个用于演示的初步结果参考。</p>
          </div>
        </div>
      </div>

      <div class="mode-card">
        <span class="mode-label">预测模式</span>
        <el-radio-group v-model="predictRealOnly" size="mini" class="mode-switch">
          <el-radio-button :label="false">真实 + 合成</el-radio-button>
          <el-radio-button :label="true">仅真实</el-radio-button>
        </el-radio-group>
      </div>
    </section>

    <section class="prediction-grid">
      <form class="editor-panel glass-card" @submit.prevent="submitPrediction">
        <div class="panel-head">
          <div>
            <h2>症状描述</h2>
            <p>尽量写出持续时间、疼痛部位、伴随症状等关键信息。</p>
          </div>
          <span class="count-pill">{{ symptomLength }} 字</span>
        </div>

        <label class="editor-label" for="symptom-input">请输入病情描述</label>
        <textarea
          id="symptom-input"
          v-model="symptomInput"
          class="editor-textarea"
          rows="8"
          :disabled="loading"
          placeholder="例如：近三天持续咳嗽，夜间明显，伴轻微发热和胸闷。"
        ></textarea>

        <div class="editor-foot">
          <p class="editor-tip">结果仅用于课程演示与参考，不可替代专业问诊。</p>
          <button
            type="submit"
            class="submit-btn glass-btn glass-btn--primary"
            :disabled="loading || !symptomInput.trim()"
          >
            {{ loading ? '分析中...' : '提交预测' }}
          </button>
        </div>
      </form>

      <aside class="result-column">
        <section class="note-panel glass-card">
          <div class="panel-head compact">
            <h2>提示</h2>
          </div>
          <p class="note-copy">
            这里展示的预测结果仅有参考价值，如有身体不适请尽快就医。当前模型：
            <strong>{{ currentModelText }}</strong>。当前模型仅支持 10 类病种分类，若症状涉及多个系统或超出训练范围，结果可能出现偏差。
          </p>
        </section>

        <section class="result-panel glass-card">
          <div class="panel-head compact">
            <div>
              <h2>预测结果</h2>
              <p>提交后会在这里展示模型返回结果。</p>
            </div>
          </div>

          <AppLoading v-if="loading" label="正在分析症状..." compact></AppLoading>

          <div v-else class="result-shell" :class="{ 'result-shell--filled': hasResult }">
            <span class="result-state">{{ hasResult ? '分析完成' : '等待提交' }}</span>
            <div class="result-value">{{ displayResult }}</div>
          </div>
          <ul v-if="topPredictions.length" class="top-predictions">
            <li v-for="item in topPredictions" :key="item.label" class="top-predictions__item">
              <span class="top-predictions__label">{{ item.label }}</span>
              <strong class="top-predictions__value">{{ item.percent }}</strong>
            </li>
          </ul>
        </section>

        <section v-if="historyCount > 0" class="history-panel glass-card">
          <span class="history-label">体验记录</span>
          <strong>已累计预测 {{ historyCount }} 次</strong>
        </section>
      </aside>
    </section>

    <AiAssistantBubble
      :symptom-text="symptomInput"
      :prediction-result="predictionResult"
      :case-text="symptomInput"
      :case-meta="{ type: predictionResult || '待预测病例' }"
    />
  </div>
</template>

<script>
import { submitPrediction as predictRequest } from '@/api/admin'
import logoImg from '@/assets/logo.png'
import AppLoading from '@/components/AppLoading.vue'
import AiAssistantBubble from '@/components/AiAssistantBubble.vue'

export default {
  name: 'Prediction',
  components: {
    AppLoading,
    AiAssistantBubble
  },
  data() {
    return {
      logoImg,
      symptomInput: '',
      predictionResult: '',
      topPredictions: [],
      hasResult: false,
      loading: false,
      historyCount: 0,
      predictRealOnly: false
    }
  },
  computed: {
    displayResult() {
      if (this.hasResult && this.predictionResult) return this.predictionResult
      return '提交后在此显示'
    },
    currentModelText() {
      return this.predictRealOnly ? '仅真实' : '真实 + 合成'
    },
    symptomLength() {
      return this.symptomInput.trim().length
    }
  },
  methods: {
    async submitPrediction() {
      const content = this.symptomInput.trim()
      if (!content) {
        this.$message.warning('请输入症状描述')
        return
      }

      this.loading = true
      this.hasResult = false
      this.topPredictions = []

      try {
        const res = await predictRequest(content, {
          real_only: this.predictRealOnly
        })

        if (res.code === 200) {
          this.predictionResult = res.data.resultData || '未知'
          this.topPredictions = res.data.topPredictions || []
          this.hasResult = true
          this.historyCount += 1
        } else {
          this.topPredictions = []
          this.$message.error(res.message || '预测失败')
        }
      } catch (error) {
        console.error('预测失败:', error)
        this.topPredictions = []
        this.$message.error(`预测失败：${error.message || '请检查网络连接'}`)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.prediction-page {
  display: grid;
  gap: 24px;
  color: var(--text);
}

.hero-panel {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  background: linear-gradient(135deg, rgba(16, 27, 49, 0.96), rgba(14, 22, 38, 0.86));
}

.hero-kicker {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(82, 162, 228, 0.22);
  background: rgba(17, 26, 42, 0.76);
  color: #9dc6ff;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-logo {
  width: 80px;
  height: 80px;
  object-fit: contain;
  flex-shrink: 0;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(34px, 4vw, 48px);
  line-height: 1.05;
  color: #e8f2ff;
}

.hero-copy p {
  margin: 12px 0 0;
  max-width: 560px;
  color: #9fb6d4;
  font-size: 15px;
  line-height: 1.7;
}

.mode-card {
  min-width: 240px;
  padding: 18px 20px;
  border-radius: 18px;
  border: 1px solid rgba(82, 162, 228, 0.18);
  background: rgba(11, 19, 34, 0.68);
}

.mode-label {
  display: block;
  margin-bottom: 10px;
  color: #9fb6d4;
  font-size: 13px;
}

.mode-switch {
  display: inline-flex;
  padding: 4px;
  border-radius: 14px;
  border: 1px solid rgba(104, 170, 238, 0.16);
  background:
    linear-gradient(180deg, rgba(153, 191, 233, 0.07), rgba(45, 85, 148, 0.05)),
    rgba(10, 24, 51, 0.56);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 8px 16px rgba(3, 11, 30, 0.14);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.mode-switch ::v-deep .el-radio-button__inner {
  min-width: 88px;
  padding: 9px 16px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #9fbce0;
  font-weight: 600;
  box-shadow: none;
  transition:
    color 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.mode-switch ::v-deep .el-radio-button:first-child .el-radio-button__inner,
.mode-switch ::v-deep .el-radio-button:last-child .el-radio-button__inner {
  border-radius: 10px;
}

.mode-switch ::v-deep .el-radio-button__orig-radio:checked + .el-radio-button__inner {
  background:
    linear-gradient(180deg, rgba(128, 191, 248, 0.18), rgba(68, 126, 204, 0.14)),
    rgba(14, 37, 79, 0.78);
  color: #e7f1ff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 8px 16px rgba(6, 18, 42, 0.18);
}

.mode-switch ::v-deep .el-radio-button__orig-radio:checked + .el-radio-button__inner:hover {
  transform: none;
}

.mode-switch ::v-deep .el-radio-button__inner:hover {
  color: #d1e4fb;
  background: rgba(96, 155, 230, 0.07);
}

.prediction-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.86fr);
  gap: 24px;
  align-items: start;
}

.editor-panel,
.note-panel,
.result-panel,
.history-panel {
  padding: 24px;
  background: linear-gradient(180deg, rgba(16, 27, 49, 0.94), rgba(11, 19, 34, 0.9));
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.panel-head.compact {
  margin-bottom: 14px;
}

.panel-head h2 {
  margin: 0;
  font-size: 22px;
  color: #edf6ff;
}

.panel-head p {
  margin: 8px 0 0;
  color: #8ea5c3;
  font-size: 14px;
  line-height: 1.6;
}

.count-pill {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(63, 140, 255, 0.12);
  color: #9dc6ff;
  font-size: 13px;
}

.editor-label {
  display: block;
  margin-bottom: 10px;
  color: #dbe8fb;
  font-size: 14px;
  font-weight: 600;
}

.editor-textarea {
  width: 100%;
  min-height: 230px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(82, 162, 228, 0.16);
  background: rgba(232, 240, 255, 0.9);
  color: #122033;
  font-size: 15px;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.editor-textarea:focus {
  border-color: rgba(63, 140, 255, 0.42);
  box-shadow: 0 0 0 4px rgba(63, 140, 255, 0.14);
}

.editor-foot {
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.editor-tip {
  margin: 0;
  color: #8ea5c3;
  font-size: 13px;
}

.submit-btn {
  min-width: 168px;
  height: 46px;
  padding: 0 24px;
  font-size: 15px;
  font-weight: 700;
}

.result-column {
  display: grid;
  gap: 18px;
}

.note-copy {
  margin: 0;
  color: #a9c1de;
  font-size: 15px;
  line-height: 1.75;
}

.note-copy strong {
  color: #dff3ff;
  font-weight: 600;
}

.result-shell {
  display: grid;
  gap: 18px;
  min-height: 220px;
  align-content: center;
  justify-items: start;
  padding: 22px;
  border-radius: 20px;
  border: 1px dashed rgba(82, 162, 228, 0.28);
  background:
    linear-gradient(180deg, rgba(11, 19, 34, 0.86), rgba(11, 19, 34, 0.68)),
    radial-gradient(320px 180px at 0% 0%, rgba(63, 140, 255, 0.12), transparent 58%);
}

.result-shell--filled {
  border-style: solid;
  border-color: rgba(82, 162, 228, 0.24);
}

.result-state {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(51, 197, 201, 0.12);
  color: #9be7ea;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.result-value {
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.15;
  font-weight: 700;
  color: #edf6ff;
  word-break: break-word;
}

.top-predictions {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.top-predictions__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(14, 25, 47, 0.82);
  border: 1px solid rgba(110, 200, 255, 0.14);
}

.top-predictions__label {
  color: #cfe0fb;
}

.top-predictions__value {
  color: #6ec8ff;
}

.history-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.history-label {
  color: #8ea5c3;
  font-size: 13px;
}

.history-panel strong {
  color: #e8f2ff;
  font-size: 15px;
}

@media (max-width: 1024px) {
  .hero-panel,
  .prediction-grid {
    grid-template-columns: 1fr;
  }

  .hero-panel {
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .hero-panel,
  .editor-panel,
  .note-panel,
  .result-panel,
  .history-panel {
    padding: 18px;
  }

  .hero-title-row {
    align-items: flex-start;
  }

  .hero-logo {
    width: 60px;
    height: 60px;
  }

  .editor-foot {
    align-items: stretch;
  }

  .submit-btn {
    width: 100%;
  }
}
</style>
