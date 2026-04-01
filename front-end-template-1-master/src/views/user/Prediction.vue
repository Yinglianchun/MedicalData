<template>
  <div class="pred-container">
    <div class="left">
      <div class="title">
        <img :src="logoImg" class="logo" alt="" />
        病情初步预测
      </div>
      <div class="mode-row">
        <span class="mode-label">预测模式</span>
        <el-radio-group v-model="predictRealOnly" size="mini">
          <el-radio-button :label="false">真实+合成</el-radio-button>
          <el-radio-button :label="true">仅真实</el-radio-button>
        </el-radio-group>
      </div>
      <div class="form">
        <div class="form-group">
          <div class="form-label">病情描述：</div>
          <div class="form-control">
            <textarea
              v-model="symptomInput"
              placeholder="请输入病情描述"
              rows="4"
              :disabled="loading"
            />
          </div>
        </div>
        <div class="button">
          <button type="button" :disabled="loading || !symptomInput.trim()" @click="submitPrediction">
            {{ loading ? '分析中...' : '提交' }}
          </button>
        </div>
      </div>
    </div>
    <div class="right">
      <div class="top">
        <div class="content">
          <div class="block-title">提示</div>
          <dv-border-box-8>
            <div class="word tip-inner">
              这里展示预测结果只有参考价值，如有身体不适请尽快就医。当前模型：{{ resultModelText }}
            </div>
          </dv-border-box-8>
        </div>
      </div>
      <div class="bottom">
        <div class="content">
          <div class="block-title">预测结果</div>
          <dv-decoration-11 class="decoration-result">
            <div class="word result-inner">
              {{ displayResult }}
            </div>
          </dv-decoration-11>
        </div>
      </div>
      <div v-if="historyCount > 0" class="history-hint">已累计预测 {{ historyCount }} 次（演示）</div>
    </div>
  </div>
</template>

<script>
import { submitPrediction as predictRequest } from '@/api/admin'
import logoImg from '@/assets/logo.png'

export default {
  name: 'Prediction',
  data() {
    return {
      logoImg,
      symptomInput: '',
      predictionResult: '',
      hasResult: false,
      loading: false,
      historyCount: 0,
      predictRealOnly: false,
      resultModelText: '真实+合成'
    }
  },
  computed: {
    displayResult() {
      if (this.loading) return '分析中...'
      if (this.hasResult && this.predictionResult) return this.predictionResult
      return '提交后在此显示'
    }
  },
  methods: {
    async submitPrediction() {
      if (!this.symptomInput.trim()) {
        this.$message.warning('请输入症状描述')
        return
      }
      this.loading = true
      this.hasResult = false
      try {
        const res = await predictRequest(this.symptomInput.trim(), {
          real_only: this.predictRealOnly
        })
        if (res.code === 200) {
          this.predictionResult = res.data.resultData || '未知'
          this.resultModelText = res.data.modelMode === 'real_only' ? '仅真实' : '真实+合成'
          this.hasResult = true
          this.historyCount += 1
        } else {
          this.$message.error(res.message || '预测失败')
        }
      } catch (e) {
        console.error('预测失败:', e)
        this.$message.error('预测失败：' + (e.message || '请检查网络连接'))
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style lang="less" scoped>
.button {
  width: 100%;
  height: 40px;
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
button {
  width: 80%;
  height: 100%;
  background: #26fffd;
  color: rgb(0, 0, 0);
  border-radius: 15px;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pred-container {
  display: flex;
  width: 100%;
  min-height: calc(100vh - 100px);
  .left {
    width: 800px;
    max-width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    .title {
      color: #26fffd;
      margin-top: 48px;
      font-size: 38px;
      font-weight: bold;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .logo {
      width: 80px;
      height: 80px;
    }
    .mode-row {
      margin-top: 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .mode-label {
      font-size: 14px;
      color: #fff;
    }
    .form {
      margin-top: 24px;
      width: 90%;
      max-width: 480px;
      .form-group {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 12px;
        .form-label {
          font-size: 18px;
          color: #fff;
        }
        .form-control textarea {
          width: 100%;
          border-radius: 15px;
          background: #d3dcf7;
          border: none;
          outline: none;
          padding: 10px 12px;
          font-size: 15px;
          box-sizing: border-box;
          resize: vertical;
          font-family: inherit;
        }
      }
    }
  }
  .right {
    flex: 1;
    min-width: 280px;
    .top {
      margin-top: 30px;
      width: 90%;
      .content {
        padding: 15px 25px;
        .block-title {
          display: flex;
          justify-content: center;
          color: #fff;
          font-weight: bold;
          font-size: 22px;
          margin-bottom: 8px;
        }
        .tip-inner {
          min-height: 80px;
          text-align: center;
          margin: 12px 10px 8px;
          font-size: 15px;
          line-height: 1.5;
        }
      }
    }
    .bottom {
      margin-top: 24px;
      width: 90%;
      .content {
        padding: 15px 25px;
        .block-title {
          display: flex;
          justify-content: center;
          color: #fff;
          font-weight: bold;
          font-size: 22px;
          margin-bottom: 8px;
        }
        .decoration-result {
          height: 120px;
          text-align: center;
        }
        .result-inner {
          font-size: 18px;
          padding: 8px 16px;
        }
      }
    }
    .history-hint {
      margin: 16px 25px;
      font-size: 13px;
      color: #8ea5c3;
    }
  }
}
.word {
  background: linear-gradient(to right, orange, #26fffd);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: inline-block;
}
@media (max-width: 1100px) {
  .pred-container {
    flex-direction: column;
    .left {
      width: 100%;
    }
  }
}
</style>
