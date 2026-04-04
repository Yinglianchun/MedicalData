<template>
  <div class="ai-assistant">
    <button class="ai-fab" type="button" @click="dialogVisible = true">
      AI
    </button>

    <el-dialog
      :visible.sync="dialogVisible"
      :append-to-body="true"
      custom-class="ai-dialog"
      title="AI 助手"
      width="420px"
    >
      <div class="ai-panel">
        <div class="ai-intro">
          可用于解释预测结果、分析当前图表。内容仅供参考，不替代医生诊断或正式业务决策。
        </div>

        <div class="quick-actions">
          <el-button
            v-if="canExplainPrediction"
            size="mini"
            type="primary"
            plain
            :disabled="loading"
            @click="runExplainPrediction"
          >
            解释预测结果
          </el-button>
          <el-button
            v-for="action in availableChartActions"
            :key="action.key || action.label"
            size="mini"
            type="primary"
            plain
            :disabled="loading"
            @click="runChartAnalysis(action)"
          >
            {{ action.label }}
          </el-button>
        </div>

        <div class="status-box">
          <div>预测结果：{{ canExplainPrediction ? '可解释' : '暂无可解释结果' }}</div>
          <div>图表分析：{{ availableChartActions.length ? `可分析 ${availableChartActions.length} 项` : '暂无可分析图表' }}</div>
        </div>

        <div v-if="loading" class="loading-box">
          <i class="el-icon-loading"></i>
          <span>AI 正在整理内容...</span>
        </div>

        <div v-else class="result-box">
          <div class="result-title">{{ resultTitle }}</div>
          <div class="result-content">{{ resultContent || '点击上方按钮开始使用 AI 助手。' }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { aiAssistant } from '@/api/admin'

export default {
  name: 'AiAssistantBubble',
  props: {
    symptomText: {
      type: String,
      default: ''
    },
    predictionResult: {
      type: String,
      default: ''
    },
    chartActions: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      dialogVisible: false,
      loading: false,
      resultTitle: 'AI 回复',
      resultContent: ''
    }
  },
  computed: {
    canExplainPrediction() {
      return !!(this.predictionResult || '').trim()
    },
    availableChartActions() {
      return (this.chartActions || []).filter((item) => {
        return item && item.label && Array.isArray(item.data) && item.data.length
      })
    }
  },
  methods: {
    async runExplainPrediction() {
      if (!this.canExplainPrediction) {
        this.$message.warning('当前没有可解释的预测结果')
        return
      }
      await this.requestAi('explain_prediction', '预测结果解释')
    },
    async runChartAnalysis(action) {
      if (!action || !Array.isArray(action.data) || !action.data.length) {
        this.$message.warning('当前图表暂无可分析数据')
        return
      }
      await this.requestAi('analyze_chart', action.label, {
        chart_title: action.title || action.label,
        chart_type: action.type || '图表',
        chart_data: action.data
      })
    },
    async requestAi(task, title, extraPayload = {}) {
      this.loading = true
      this.resultTitle = title
      try {
        const res = await aiAssistant({
          task,
          symptom_text: this.symptomText,
          prediction_result: this.predictionResult,
          ...extraPayload
        })
        if (res.code === 200 && res.data) {
          this.resultContent = res.data.content || 'AI 未返回有效内容'
        } else {
          this.$message.error(res.message || 'AI 请求失败')
        }
      } catch (error) {
        console.error('AI 请求失败:', error)
        const message =
          (error && error.response && error.response.data && error.response.data.message) ||
          (error && error.message) ||
          '请检查后端接口和 API 配置'
        this.$message.error(`AI 请求失败：${message}`)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  right: 26px;
  bottom: 32px;
  width: 68px;
  height: 68px;
  z-index: 99999;
  overflow: visible;
}

.ai-fab {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 68px;
  height: 68px;
  border: none;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #4fd9ff, #2b6bff 72%, #18337d);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  box-shadow: 0 0 22px rgba(79, 217, 255, 0.45);
  z-index: 99999;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  outline: none;
  border: 1px solid rgba(173, 234, 255, 0.75);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.45);
}

.ai-fab:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 0 28px rgba(79, 217, 255, 0.58);
}

.ai-panel {
  color: #d7e6ff;
}

.ai-intro {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(82, 132, 255, 0.12);
  color: #9ec4ff;
  line-height: 1.7;
}

.quick-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.status-box {
  margin-top: 16px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  line-height: 1.8;
  color: #b8c7e8;
  font-size: 13px;
}

.loading-box {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #6ec8ff;
}

.result-box {
  margin-top: 18px;
  padding: 14px;
  border-radius: 12px;
  min-height: 180px;
  background: rgba(6, 17, 43, 0.9);
  border: 1px solid rgba(93, 159, 255, 0.22);
}

.result-title {
  color: #6ec8ff;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
}

.result-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #dbe7ff;
  font-size: 14px;
}
</style>