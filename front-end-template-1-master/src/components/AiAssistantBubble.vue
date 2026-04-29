<template>
  <div class="ai-assistant" :style="fabPositionStyle">
    <button
      class="ai-fab"
      :class="{ 'ai-fab--dragging': fabDragging }"
      type="button"
      @click="handleFabClick"
      @pointerdown="startFabDrag"
    >
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
          可用于解释预测结果、分析当前图表，并给出参考性的挂号方向。内容仅供参考，不替代医生诊断或正式业务决策。
        </div>

        <div class="quick-actions">
          <el-button
            v-if="canExplainPrediction"
            class="action-chip"
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
            class="action-chip"
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

        <div class="result-box">
          <div class="result-title">{{ resultTitle }}</div>
          <div v-if="loading" class="loading-box">
            <i class="el-icon-loading"></i>
            <span>{{ streamStatus }}</span>
          </div>
          <div class="result-content">{{ displayResultContent }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
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
      resultContent: '',
      streamStatus: 'AI 正在连接模型...',
      streamController: null,
      fabPosition: {
        left: null,
        top: null
      },
      fabDragging: false,
      fabDragState: {
        pointerId: null,
        startX: 0,
        startY: 0,
        startLeft: 0,
        startTop: 0,
        moved: false,
        target: null
      },
      suppressFabClick: false
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
    },
    displayResultContent() {
      if (this.resultContent) {
        return this.resultContent
      }
      if (this.loading) {
        return '正在等待模型返回内容...'
      }
      return '点击上方按钮开始使用 AI 助手。'
    },
    fabPositionStyle() {
      if (this.fabPosition.left === null || this.fabPosition.top === null) {
        return {}
      }

      return {
        left: `${this.fabPosition.left}px`,
        top: `${this.fabPosition.top}px`,
        right: 'auto',
        bottom: 'auto'
      }
    }
  },
  watch: {
    dialogVisible(value) {
      if (!value) {
        this.abortActiveStream()
      }
    }
  },
  mounted() {
    this.syncFabPositionFromDom()
    window.addEventListener('resize', this.keepFabInViewport)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.keepFabInViewport)
    this.removeFabDragListeners()
    this.abortActiveStream()
  },
  methods: {
    handleFabClick(event) {
      if (this.suppressFabClick) {
        if (event) {
          event.preventDefault()
          event.stopPropagation()
        }
        this.suppressFabClick = false
        return
      }

      this.dialogVisible = true
    },
    syncFabPositionFromDom() {
      this.$nextTick(() => {
        if (!this.$el) {
          return
        }

        const rect = this.$el.getBoundingClientRect()
        this.fabPosition = this.clampFabPosition(rect.left, rect.top)
      })
    },
    keepFabInViewport() {
      if (this.fabPosition.left === null || this.fabPosition.top === null) {
        this.syncFabPositionFromDom()
        return
      }

      this.fabPosition = this.clampFabPosition(this.fabPosition.left, this.fabPosition.top)
    },
    clampFabPosition(left, top) {
      const margin = 8
      const width = this.$el ? this.$el.offsetWidth : 68
      const height = this.$el ? this.$el.offsetHeight : 68
      const maxLeft = Math.max(margin, window.innerWidth - width - margin)
      const maxTop = Math.max(margin, window.innerHeight - height - margin)

      return {
        left: Math.min(Math.max(left, margin), maxLeft),
        top: Math.min(Math.max(top, margin), maxTop)
      }
    },
    startFabDrag(event) {
      if (event.button !== undefined && event.button !== 0) {
        return
      }

      const rect = this.$el.getBoundingClientRect()
      const startPosition = this.clampFabPosition(rect.left, rect.top)
      this.fabPosition = startPosition
      this.fabDragging = true
      this.fabDragState = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        startLeft: startPosition.left,
        startTop: startPosition.top,
        moved: false,
        target: event.currentTarget
      }

      if (event.currentTarget && event.currentTarget.setPointerCapture) {
        event.currentTarget.setPointerCapture(event.pointerId)
      }

      window.addEventListener('pointermove', this.onFabDrag)
      window.addEventListener('pointerup', this.endFabDrag)
      window.addEventListener('pointercancel', this.endFabDrag)
    },
    onFabDrag(event) {
      if (!this.fabDragging || event.pointerId !== this.fabDragState.pointerId) {
        return
      }

      const offsetX = event.clientX - this.fabDragState.startX
      const offsetY = event.clientY - this.fabDragState.startY
      if (Math.abs(offsetX) > 3 || Math.abs(offsetY) > 3) {
        this.fabDragState.moved = true
      }

      this.fabPosition = this.clampFabPosition(
        this.fabDragState.startLeft + offsetX,
        this.fabDragState.startTop + offsetY
      )
    },
    endFabDrag(event) {
      if (!this.fabDragging || event.pointerId !== this.fabDragState.pointerId) {
        return
      }

      if (this.fabDragState.target && this.fabDragState.target.releasePointerCapture) {
        this.fabDragState.target.releasePointerCapture(event.pointerId)
      }

      if (this.fabDragState.moved) {
        this.suppressFabClick = true
        window.setTimeout(() => {
          this.suppressFabClick = false
        }, 0)
      }

      this.fabDragging = false
      this.fabDragState = {
        pointerId: null,
        startX: 0,
        startY: 0,
        startLeft: 0,
        startTop: 0,
        moved: false,
        target: null
      }
      this.removeFabDragListeners()
    },
    removeFabDragListeners() {
      window.removeEventListener('pointermove', this.onFabDrag)
      window.removeEventListener('pointerup', this.endFabDrag)
      window.removeEventListener('pointercancel', this.endFabDrag)
    },
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
    abortActiveStream() {
      if (this.streamController) {
        this.streamController.abort()
        this.streamController = null
      }
      this.loading = false
    },
    parseStreamBlock(block) {
      const lines = block.split('\n')
      let eventName = 'message'
      const dataLines = []

      lines.forEach((line) => {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trim())
        }
      })

      if (!dataLines.length) {
        return null
      }

      return {
        eventName,
        payload: JSON.parse(dataLines.join('\n'))
      }
    },
    handleStreamEvent(eventName, payload) {
      if (eventName === 'status') {
        this.streamStatus = payload.message || 'AI 正在思考，请稍等...'
        return
      }

      if (eventName === 'message') {
        if (payload.content) {
          this.resultContent += payload.content
          this.streamStatus = 'AI 正在生成内容...'
        }
        return
      }

      if (eventName === 'done') {
        this.streamStatus = '生成完成'
        return
      }

      if (eventName === 'error') {
        throw new Error(payload.message || 'AI 流式请求失败')
      }
    },
    async requestAi(task, title, extraPayload = {}) {
      this.abortActiveStream()
      this.loading = true
      this.resultTitle = title
      this.resultContent = ''
      this.streamStatus = 'AI 正在连接模型...'

      const controller = new AbortController()
      this.streamController = controller

      try {
        const response = await fetch('/api/ai/assistant/stream', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            task,
            symptom_text: this.symptomText,
            prediction_result: this.predictionResult,
            ...extraPayload
          }),
          signal: controller.signal
        })

        if (!response.ok) {
          let message = 'AI 请求失败'
          try {
            const errorData = await response.json()
            message = errorData.message || message
          } catch (parseError) {
            const text = await response.text()
            if (text) {
              message = text
            }
          }
          throw new Error(message)
        }

        if (!response.body) {
          throw new Error('当前浏览器不支持流式响应')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            break
          }

          buffer += decoder.decode(value, { stream: true })

          while (buffer.includes('\n\n')) {
            const boundary = buffer.indexOf('\n\n')
            const block = buffer.slice(0, boundary)
            buffer = buffer.slice(boundary + 2)
            const parsed = this.parseStreamBlock(block)
            if (parsed) {
              this.handleStreamEvent(parsed.eventName, parsed.payload)
            }
          }
        }

        if (buffer.trim()) {
          const parsed = this.parseStreamBlock(buffer)
          if (parsed) {
            this.handleStreamEvent(parsed.eventName, parsed.payload)
          }
        }
      } catch (error) {
        if (error && error.name === 'AbortError') {
          return
        }
        console.error('AI 流式请求失败:', error)
        const message = (error && error.message) || '请检查后端接口和 API 配置'
        this.$message.error(`AI 请求失败：${message}`)
      } finally {
        if (this.streamController === controller) {
          this.streamController = null
        }
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
  cursor: grab;
  box-shadow: 0 0 22px rgba(79, 217, 255, 0.45);
  z-index: 99999;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  outline: none;
  border: 1px solid rgba(173, 234, 255, 0.75);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.45);
  touch-action: none;
  user-select: none;
}

.ai-fab:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 0 28px rgba(79, 217, 255, 0.58);
}

.ai-fab--dragging,
.ai-fab--dragging:hover {
  transform: none;
  cursor: grabbing;
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
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(23, 46, 96, 0.34), rgba(8, 18, 45, 0.18));
  border: 1px solid rgba(94, 151, 255, 0.14);
  box-shadow:
    inset 0 1px 0 rgba(173, 222, 255, 0.08),
    inset 0 -1px 0 rgba(7, 21, 58, 0.3);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.quick-actions ::v-deep .action-chip.el-button {
  width: 100%;
  min-width: 0;
  height: 40px;
  margin: 0;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 1px solid rgba(128, 199, 255, 0.22);
  background:
    linear-gradient(180deg, rgba(198, 232, 255, 0.14), rgba(63, 120, 205, 0.08)),
    rgba(10, 26, 59, 0.42);
  color: #cbe8ff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    0 10px 18px rgba(3, 11, 30, 0.18);
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease,
    color 0.18s ease;
}

.quick-actions ::v-deep .action-chip.el-button:hover,
.quick-actions ::v-deep .action-chip.el-button:focus {
  transform: translateY(-1px);
  border-color: rgba(112, 217, 255, 0.42);
  background:
    linear-gradient(180deg, rgba(185, 241, 255, 0.2), rgba(76, 146, 255, 0.12)),
    rgba(11, 31, 69, 0.58);
  color: #eff8ff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 14px 24px rgba(5, 15, 41, 0.24),
    0 0 0 1px rgba(88, 191, 255, 0.08);
}

.quick-actions ::v-deep .action-chip.el-button:active {
  transform: translateY(0);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 6px 14px rgba(5, 15, 41, 0.22);
}

.quick-actions ::v-deep .action-chip.el-button.is-disabled,
.quick-actions ::v-deep .action-chip.el-button.is-disabled:hover,
.quick-actions ::v-deep .action-chip.el-button.is-disabled:focus {
  transform: none;
  border-color: rgba(113, 143, 198, 0.16);
  background:
    linear-gradient(180deg, rgba(126, 160, 211, 0.08), rgba(40, 65, 110, 0.08)),
    rgba(10, 22, 45, 0.3);
  color: rgba(167, 193, 224, 0.52);
  box-shadow: none;
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
  margin-bottom: 12px;
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

@media (max-width: 520px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
