<template>
  <div class="dashboard-screen">
    <!-- 加载状态 -->
    <div v-if="!config4.data.length" class="loading-overlay">
      <div class="loader"></div>
      <p>加载中...</p>
    </div>

    <!-- 主内容 -->
    <div v-else class="screen-container">
      <!-- 页面标题 -->
      <header class="screen-header">
        <h1 class="screen-title">医疗数据可视化大屏</h1>
      </header>

      <!-- 三栏布局 -->
      <div class="screen-grid">
        <!-- 左侧栏 -->
        <aside class="left-column">
          <!-- 各年龄段患病占比 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">各年龄段患病占比</div>
            </header>
            <div ref="firstMain" class="chart"></div>
          </section>

          <!-- 疾病类型分布 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">疾病类型分布</div>
            </header>
            <dv-capsule-chart :config="config1" style="width: 100%; height: 140px" />
          </section>

          <!-- 病例列表 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">病例列表</div>
            </header>
            <div class="case-table-wrap">
              <div class="case-row head">
                <span>编号</span>
                <span>类型</span>
                <span>性别</span>
                <span>年龄</span>
                <span>身高</span>
                <span>体重</span>
                <span>患病时长</span>
              </div>
              <div class="case-scroll">
                <div
                  v-for="(cases, idx) in casesData"
                  :key="idx"
                  class="case-row"
                  :class="{ active: selectedCaseIndex === idx }"
                  @click="handleCaseSelect(idx)"
                >
                  <span>{{ cases[0] }}</span>
                  <span>{{ cases[1] }}</span>
                  <span>{{ cases[2] }}</span>
                  <span>{{ cases[3] }}</span>
                  <span>{{ cases[10] }}</span>
                  <span>{{ cases[11] }}</span>
                  <span>{{ cases[12] }}</span>
                </div>
              </div>
            </div>
          </section>
        </aside>

        <!-- 中间栏 -->
        <main class="center-column">
          <!-- 疾病数据概览（KPI 卡片） -->
          <section class="panel kpi-section">
            <header class="panel-head">
              <div class="section-title">疾病数据概览</div>
            </header>
            <div class="kpi-grid">
              <div class="kpi-item">
                <span class="kpi-label">数据数量</span>
                <span class="kpi-value">{{ centerData.maxNum }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">最多疾病类型</span>
                <span class="kpi-value">{{ centerData.maxType }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">求诊最多科室</span>
                <span class="kpi-value">{{ centerData.maxDep }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">最大患者年龄</span>
                <span class="kpi-value">{{ centerData.maxAge }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">最小患者年龄</span>
                <span class="kpi-value">{{ centerData.minAge }}</span>
              </div>
              <div class="kpi-item">
                <span class="kpi-label">热门医院</span>
                <span class="kpi-value">{{ centerData.maxHos }}</span>
              </div>
            </div>
          </section>

          <!-- 男女患病对比 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">男女患病对比</div>
            </header>
            <div class="gender-charts">
              <dv-active-ring-chart :config="config2" style="width: 150px; height: 100px" />
              <dv-water-level-pond :config="config4" style="width: 100px; height: 90px" />
              <dv-active-ring-chart :config="config3" style="width: 150px; height: 100px" />
            </div>
          </section>

          <!-- 病患身高体重平均数图 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">病患身高体重平均数</div>
            </header>
            <div ref="lastMain" class="chart"></div>
          </section>
        </main>

        <!-- 右侧栏 -->
        <aside class="right-column">
          <!-- 医院科室环形图 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">医院科室环形图</div>
            </header>
            <div id="secondMian" class="chart"></div>
          </section>

          <!-- 疾病关键词云图 -->
          <section class="panel">
            <header class="panel-head">
              <div class="section-title">疾病关键词云图</div>
            </header>
            <div ref="thirdMain" class="chart"></div>
          </section>
        </aside>
      </div>
    </div>

    <AiAssistantBubble
      :case-text="selectedCaseContent"
      :case-meta="selectedCaseMeta"
    />
  </div>
</template>

<script>
import $ from "jquery";
import LeftTop from "@/components/LeftTop.vue";
import AiAssistantBubble from "@/components/AiAssistantBubble.vue";
import { color } from "echarts";
function formatter(number) {
  const numbers = number.toString().split("").reverse();
  const segs = [];

  while (numbers.length) segs.push(numbers.splice(0, 3).join(""));

  return segs.join(",").split("").reverse().join("");
}
export default {
  name: "Index",
  data() {
    return {
      currentIndex: 0, // 目前的index
      pieData: [], // 接收后端传来的数据
      casesData: [],
      selectedCaseIndex: 0,
      centerData: {
        maxNum: "",
        maxType: "",
        maxDep: "",
        maxHos: "",
        maxAge: "",
        minAge: "",
      },
      wordData: "",
      circleData: [],
      lastData: {},
      config1: {
        data: [],
      },
      config2: {
        lineWidth: 20,
        radius: "50%",
        activeRadius: "60%",
        activeTimeGap: 2000,
        digitalFlopStyle: {
          fontSize: 13,
        },
        data: [],
      },
      config3: {
        lineWidth: 20,
        radius: "50%",
        activeRadius: "60%",
        activeTimeGap: 2000,
        digitalFlopStyle: {
          fontSize: 13,
        },
        data: [],
      },
      config4: {
        data: [],
        shape: "roundRect",
      },
    };
  },
  computed: {
    selectedCaseRow() {
      if (!this.casesData.length) {
        return [];
      }
      return this.casesData[this.selectedCaseIndex] || this.casesData[0] || [];
    },
    selectedCaseContent() {
      return this.selectedCaseRow[4] || "";
    },
    selectedCaseMeta() {
      return {
        id: this.selectedCaseRow[0] || "",
        type: this.selectedCaseRow[1] || "",
        gender: this.selectedCaseRow[2] || "",
        age: this.selectedCaseRow[3] || "",
        height: this.selectedCaseRow[10] || "",
        weight: this.selectedCaseRow[11] || "",
        illDuration: this.selectedCaseRow[12] || "",
      };
    },
  },
  methods: {
    handleCaseSelect(index) {
      this.selectedCaseIndex = index;
    },
    setPieData() {
      $(document).ready(() => {
        var chartDom = this.$refs.firstMain; //通过获取refs的属性来定位div
        var myChart = this.$echarts.init(chartDom);
        var option; //图表配置
        myChart.dispatchAction({
          type: "downplay", //常规模式
          seriesIndex: 0,
          dataIndex: this.currentIndex,
        });
        this.currentIndex = (this.currentIndex + 1) % this.pieData.length; //执行后+1并取模进行进一步运算 实现动画效果
        myChart.dispatchAction({
          type: "highlight", //高亮模式
          seriesIndex: 0,
          dataIndex: this.currentIndex,
        });
        var option = {
          //触摸属性
          tooltip: {
            trigger: "item",
            formatter: "{a} <br/>{b}:{c} ({d}%)",
          },
          toolbox: {
            show: true,
          },
          calculable: true, //计算属性
          legend: {
            //小标签名
            orient: "vertical",
            icon: "circle",
            left: 0,
            x: "center",
            data: this.pieData.map((item) => item.name),
            textStyle: {
              color: "#fff",
            },
          },
          series: [
            // 饼图属性
            {
              name: "年龄占比",
              type: "pie",
              radius: [20, 50],
              roseType: "area",
              center: ["50%", "55%"],

              label: {
                show: true,
              },
              emphasis: {
                itemStyle: {
                  shadowBlur: 10, // 设置阴影
                  shadowOffsetX: 0,
                  label: {
                    show: true,
                    fontWeight: "bold",
                  },
                },
              },

              data: this.pieData,
            },
          ],
        };

        option && myChart.setOption(option);
      });
    },
    changeData(x) {
      var st = x[0]; //改变数组的排列方式
      for (var i = 0; i < x.length - 1; i++) {
        x[i] = x[i + 1];
      }
      x[x.length - 1] = st;
    },
    getSeriesData() {
      const series = [];
      this.circleData.forEach((item, index) => {
        //将circledata中的数据通过for 循环遍历添加到series中
        if (index < 5) {
          series.push({
            name: item.name,
            type: "pie",
            clockwise: false,
            hoverAnimation: false, //关闭鼠标悬停动画效果
            radius: [73 - index * 15 + "%", 68 - index * 15 + "%"],
            center: ["50%", "50%"],
            label: {
              show: false,
            },
            data: [
              {
                value: item.value,
                name: item.name,
              },
              {
                value: 3,
                itemStyle: {
                  color: "rgba(1,0,0,0)",
                  borderWidth: 0,
                },
                tooltip: {
                  show: false,
                },
                hoverAnimation: false,
              },
            ],
          })
        }
      });
      return series;
    },
    // randomColor() {  //随机颜色
    //   const r = Math.floor(Math.random() * 255);
    //   const g = Math.floor(Math.random() * 255);
    //   const b = Math.floor(Math.random() * 255);
    //   return `rgb(${r},${g},${b})`;
    // },
    setWordData() {
      var chartDom = this.$refs.thirdMain
      console.log(chartDom, "chartDom");
      var myChart = this.$echarts.init(chartDom)
      // var randomColorValue = this.randomColor();
      var option = {
        series: {
          type: "wordCloud",
          sizeRange: [20, 30],
          gridSize: 0,
          rotationRange: [0, 0],
          layoutAnimation: true,
          textStyle: {
            // color: this.randomColor() //颜色为随机值，不可行！wordCloud 类型并不直接支持为每个单词设置不同的颜色。
            color: (() => {
              // Random color  
              return 'rgb(' + [
                Math.floor(Math.random() * 255),
                Math.floor(Math.random() * 255),
                Math.floor(Math.random() * 255)
              ].join(',') + ')';
            })
          },
          emphasis: {
            textStyle: {
              fontWeight: "bold",
              color: "#fff"
            },
          },
          data: this.wordData,
        }
      }
      option && myChart.setOption(option);
    },
    setCircleData() {
      // $(document).ready(() => {

      // });
      var newData = this.circleData
      this.changeData(newData)
      this.circleData = newData
      var chartDom = document.getElementById("secondMian");
      // var chartDom好像是空的？？
      // console.log(chartDom, "chartDom");
      var myChart = this.$echarts.init(chartDom);
      var option = {
        legend: {
          show: true,
          icon: "circle",
          top: "8%",
          left: "10%",
          data: this.circleData.map((item) => item.name),
          width: -5,
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 6,
          textStyle: {
            fontSize: 12,
            lineHeight: 5,
            color: "#fffff",
          },
        },
        tooltip: {
          show: true,
          trigger: "item",
          formatter: "{b}<br>{c}({d}%)",
        },
        series: this.getSeriesData(),
      };

      option && myChart.setOption(option);
    },
    setLastData() {
      $(document).ready(() => {
        var newData = this.lastData;
        this.changeData(newData.xData)
        this.changeData(newData.y1Data)
        this.changeData(newData.y2Data)

        var chartDom = this.$refs.lastMain;
        var myChart = this.$echarts.init(chartDom);
        var option = {
          tooltip: {
            trigger: "axis",
            backgroundColor: "rgba(255,255,255,0.1)",
            axisPointer: {
              type: "shadow",
              label: {
                show: true,
                backgroundColor: "#7B7DDC",
              },
            },
          },
          dataZoom: [
            {
              type: "slider",
              start: 0,
              end: 80,
              show: false,
            }
          ],
          legend: {
            data: ["身高", "体重"],
            textStyle: {
              color: "#B4B4B4",
            },
            top: "0%",
          },
          grid: {
            x: "8%",
            width: "85%",
            height: "87%",
            y: "4%",
          },
          xAxis: {
            data: this.lastData.xData,
            axisLine: {
              lineStyle: {
                color: "#B4B4B4",
              },
            },
            axisLabel: {
              show: true,
              interval: 0,
            },
            axisTick: {
              show: false,
            },
          },
          yAxis: [{
            splitLine: { show: false },
            axisLine: {
              lineStyle: {
                color: "#B4B4B4",
              },
            },
            axisLabel: {
              formatter: "{value}",
            },
          },
          {
            splitLine: { show: false },
            axisLine: {
              lineStyle: {
                color: "#B4B4B4",
              },
            },
            axisLabel: {
              formatter: "{value}",
            },

          },
          ],
          series: [
            {
              name: "身高",
              type: "line",
              smooth: true,
              showAllSymbol: true,
              symbol: "emptyCircle",
              symbolSize: 8,
              yAxisIndex: 1,
              // areaStyle:{},
              itemStyle: {
                normal: {
                  barBorderRadius: 5,
                  color: new this.$echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: "#082e53" },
                    { offset: 1, color: "white" },
                  ]),
                },
              },
              data: this.lastData.y1Data,
            },
            {
              name: "体重",
              type: "bar",
              barWidth: "60%",
              itemStyle: {
                normal: {
                  barBorderRadius: 5,
                  color: new this.$echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: "#082e53" },
                    { offset: 1, color: "white" },
                  ]),
                },
              },
              data: this.lastData.y2Data,
            },
          ],
        };
        option && myChart.setOption(option);
      })
    },
    setConfig1() {
      var newData = this.config1.data;
      this.changeData(newData);
      this.config1 = {
        data: newData,
        showValue: true,
      };
    },
  },
  //用生命周期函数 发送请求
  async created() {
    $(document).ready(async () => {
      setInterval(() => {
        this.setPieData(); //添加计时器 渲染数据
        this.setConfig1();
        this.setWordData();
        
      }, 1000);
      setInterval(() => {
        this.setCircleData();
      }, 3000);
      setInterval(() => {
        this.setLastData();
      }, 2000);
    });
  },

  mounted() {
    //生命周期函数 mounted钩子 加载

    this.$http.get("/getHomeData").then((res) => {
      this.pieData = res.data.pieData;
      this.config1.data = res.data.ConfigOne;
      this.casesData = res.data.casesData;
      this.centerData.maxNum = res.data.maxNum;
      this.centerData.maxType = res.data.maxType;
      this.centerData.maxDep = res.data.maxDep;
      this.centerData.maxHos = res.data.maxHos;
      this.centerData.maxAge = res.data.maxAge;
      this.centerData.minAge = res.data.minAge;
      // this.getSeriesData();
      this.wordData = res.data.wordData;
      this.lastData = res.data.lastData;
      this.circleData = res.data.circleData;
      this.config2.data = res.data.boyList;
      this.config3.data = res.data.girlList;
      this.config4.data = res.data.ratioData;
      // console.log(this.lastData);
    });
    //console.log(res);
    // console.log("mounted");
    // setTimeout(() => {
    //   this.setCircleData();
    // }, 2000);
    // console.log(this.centerData.minAge)
  },
  components: {
    LeftTop,
    AiAssistantBubble,
  },
};
</script>

<style scoped>
/* 主容器 */
.dashboard-screen {
  min-height: 100vh;
  background: linear-gradient(180deg, var(--bg), var(--bg-2));
  padding: var(--sp-3);
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  z-index: 999;
}

.loader {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  margin-top: var(--sp-2);
  color: var(--text-muted);
  font-size: var(--fs-14);
}

/* 页面标题 */
.screen-header {
  text-align: center;
  margin-bottom: var(--sp-3);
}

.screen-title {
  font-size: 28px;
  font-weight: var(--fw-bold);
  color: var(--text);
  margin: 0;
}

/* 三栏布局 */
.screen-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: var(--sp-2);
  max-width: 1800px;
  margin: 0 auto;
}

/* 左中右栏 */
.left-column,
.center-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

/* 卡片面板 */
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: var(--sp-2);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.panel:hover {
  transform: translateY(-1px);
  box-shadow: var(--hover-glow-shadow);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-2);
}

.section-title {
  font-size: var(--fs-16);
  font-weight: var(--fw-bold);
  color: var(--text);
}

/* 图表容器 */
.chart {
  flex: 1;
  min-height: 180px;
  border-radius: 8px;
}

/* KPI 卡片区域 */
.kpi-section {
  background: linear-gradient(135deg, var(--panel), var(--panel-2));
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-2);
}

.kpi-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sp-2);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.kpi-item:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 12px rgba(47, 128, 237, 0.15);
}

.kpi-label {
  font-size: var(--fs-12);
  color: var(--text-muted);
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 20px;
  font-weight: var(--fw-bold);
  color: var(--accent);
}

/* 男女患病对比图表容器 */
.gender-charts {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: var(--sp-2) 0;
}

/* 病例表格 */
.case-table-wrap {
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.case-row {
  display: grid;
  grid-template-columns: 40px 80px 50px 50px 50px 50px 80px;
  gap: 8px;
  padding: 10px var(--sp-1);
  border-bottom: 1px solid var(--border);
  font-size: var(--fs-12);
  color: var(--text);
  text-align: center;
  cursor: pointer;
}

.case-row.head {
  background: var(--bg-2);
  font-weight: var(--fw-bold);
  color: var(--text-muted);
  position: sticky;
  top: 0;
  z-index: 2;
}

.case-scroll {
  max-height: 200px;
  overflow-y: auto;
}

.case-scroll::-webkit-scrollbar {
  width: 6px;
}

.case-scroll::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

.case-scroll::-webkit-scrollbar-thumb:hover {
  background: #b7d4f2;
}

.case-row.active {
  background: rgba(77, 170, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(84, 204, 255, 0.45);
  border-radius: 6px;
}

/* 响应式 */
@media (max-width: 1400px) {
  .screen-grid {
    grid-template-columns: 1fr;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
