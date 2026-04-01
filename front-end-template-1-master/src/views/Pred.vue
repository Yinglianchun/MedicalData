<template>
  <div class="pred-container">
  <div class="left">
      <div class="title">
          <img src="../assets/logo.png" style="width:80px;height:80px;" alt="">
          病情初步预测
      </div>
      <div class="form">
          <div class="form-group">
              <div class="form-label" style="font-size: 25px;">病情描述：</div>
              <div class="form-control" style="font-size: 20px;">
                  <input type="text" v-model="symptoms" placeholder="请输入病情描述" />
              </div>
          </div>
          <!-- 提交按钮 -->
          <div class="button" style="font-size: 20px;">
              <button type="submit" @click="submitSymptoms">提交</button>
          </div>
      </div>
  </div>
  <div class="right">
      <div class="top">
          <div class="content">
              <div class="title" style="font-size: 25px;">提示</div>
              <dv-border-box-8><div class="word" style=" height: 80px;text-align: center;margin-left: 10px;margin-top: 20px;">这里展示预测结果只有参考价值，如有身体不适请尽快就医。</div></dv-border-box-8>
          </div>
      </div>
      <div class="bottom">
          <div class="content">
              <div class="title" style="font-size: 25px;">预测结果</div>
              <dv-decoration-11 style="height: 100px; text-align: center;"><div class="word">{{ predictionResult }}</div></dv-decoration-11>
          </div>
      </div>
  </div>
</div>
</template>

<script>
  export default {
      name: 'Pred',
      data() {
          return {
              symptoms: '', // 用于存储用户输入的症状描述
              predictionResult: '' // 用于存储预测结果
          }
      },
      methods: {
          submitSymptoms() {
              // 向后端发送 POST 请求
              fetch('http://localhost:5000/submitModel', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                      content: this.symptoms // 将用户输入的症状描述发送到后端
                  })
              })
                  .then(response => response.json())
                  .then(data => {
                      // 处理后端返回的预测结果
                      this.predictionResult = data.data.resultData;
                  })
                  .catch(error => {
                      console.error('Error:', error);
                  });
          }
      }
  }
</script>

<style lang="less" scoped>
  .button {
    width: 100%;
    height: 30px;
    display: flex;
    justify-content: center;
  }
  button {
    width: 80%;
    height: 100%;
    background: #26fffd;
    color: rgb(0, 0, 0);
    border-radius: 15px;
  }
  .pred-container {
    display: flex;
    width: 100%;
    height: 100vh;
    .left {
      width: 800px;
      display: flex;
      flex-direction: column;
      align-items: center;
      .title {
        color: #26fffd;
        margin-top: 80px;
        font-size: 38px;
        font-weight: bold;
      }
      .form {
        margin-top: 35px;
        .form-group {
          display: flex;
          align-items: center;
          margin-bottom: 15px;
          .form-label {
            margin-right: 25px;
            font-size: 18px;
            color: #fff;
          }
          .form-control input {
            border-radius: 15px;
            background: #d3dcf7;
            border: none;
            outline: none;
            padding: 0 5px;
            height: 25px;
            width: 200px;
          }
        }
      }
    }
    .right {
      flex: 1;
      .top {
        margin-top: 30px;
        width: 80%;
        .content {
          padding: 15px 25px;
          .title {
            display: flex;
            justify-content: center;
            color: #fff;
            font-weight: bold;
            font-size: 18px;
          }
          .word {
            font-size: 20px;
            color: orange;
            margin-top: 15px;
            padding: 0 20px;
            background: linear-gradient(to right, orange, #26fffd);
            -webkit-background-clip: text; /* 使用文本作为背景剪辑 */
            color: transparent; /* 隐藏文字本身的颜色 */
            display: inline-block; /* 确保渐变应用在文字上 */
          }
        }
      }
      .bottom {
        margin-top: 30px;
        width: 80%;
        height: 200px;
        .content {
          padding: 15px 25px;
          .title {
            display: flex;
            justify-content: center;
            color: #fff;
            font-weight: bold;
            font-size: 18px;
          }
          .word {
            font-size: 20px;
            color: orange;
            margin-top: 15px;
            padding: 0 20px;
            background: linear-gradient(to right, orange, #26fffd);
            -webkit-background-clip: text; /* 使用文本作为背景剪辑 */
            color: transparent; /* 隐藏文字本身的颜色 */
            display: inline-block; /* 确保渐变应用在文字上 */
          }
        }
      }
    }
  }
</style>

