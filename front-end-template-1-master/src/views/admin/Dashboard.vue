<template>
  <div class="home screen-dashboard">
    <!-- // 判断config4是否存在,config4被赋值完才开始加载  -->
    <transition name="fade" mode="out-in">
      <div v-if="!config4.data.length" class="dashboard-loader-shell">
        <AppLoading label="正在加载可视化数据..." fullscreen></AppLoading>
      </div>
      <dv-border-box-10 v-else>
        <div class="naca" id="name">
          <div class="index-header" style="margin-top: 5px">
            <div>
              <dv-decoration-10 style="width: 450px; height: 1px; margin-bottom: 45px" />
              <dv-decoration-8 style="width: 180px; height: 50px" :color="['#568aea', '#000000']" />
              <div style="
                  width: 150px;
                  color: #eeecec;
                  font-size: 18px;
                  padding: 0 15px;
                  font-weight: bold;
                ">
                可视化化平台
              </div>
              <dv-decoration-8 :reverse="true" style="width: 180px; height: 50px" :color="['#568aea', '#000000']" />
              <dv-decoration-10 style="
                  width: 450px;
                  height: 1px;
                  transform: rotateY(180deg);
                  margin-bottom: 45px;
                " />
            </div>
            <dv-decoration-5 style="width: 10%; height: 20px" :color="['#568aea', '#000000']" />
          </div>

          <div class="index-content">
            <div class="left">
              <div class="left-1" style="">
                <dv-border-box-12>
                  <div style="padding: 5px">
                    <div class="title" style="margin-top: 5px">
                      各年龄段患病占比
                    </div>

                    <div ref="firstMain" style="width: 100%; height: 120px"></div>
                  </div>
                </dv-border-box-12>
                <dv-border-box-8>
                  <div style="padding: 5px; padding-bottom: 30px">
                    <div class="title" style="margin-top: 1px">
                      疾病类型分布
                    </div>
                    <dv-capsule-chart :config="config1" style="width: 80%; height: 110px" />
                  </div>
                </dv-border-box-8>

                <dv-border-box-3>
                  <div style="padding: 15px">
                    <div class="title" style="margin-top: 5px">病例列表</div>
                    <!-- <div ref="timeZhou" style="width: 100%; height: 350px"></div> -->
                    <div class="row_list" style="">
                      <ul class="cases_list" style="width: 100%; height: 159px; overflow: auto">
                        <li style="font-size: 15px">
                          <div>编号</div>
                          <div>求诊类型</div>
                          <div>性别</div>
                          <div>年龄</div>
                          <div>身高</div>
                          <div>体重</div>
                          <div>患病时长</div>
                        </li>
                        <li
                          v-for="(cases, index) in casesData"
                          :key="cases[0] || index"
                          :class="{ active: selectedCaseIndex === index }"
                          @click="handleCaseSelect(index)"
                        >
                          <div>{{ cases[0] }}</div>
                          <div>{{ cases[1] }}</div>
                          <div>{{ cases[2] }}</div>
                          <div>{{ cases[3] }}</div>
                          <div>{{ cases[10] }}</div>
                          <div>{{ cases[11] }}</div>
                          <div>{{ cases[12] }}</div>
                        </li>
                      </ul>
                    </div>
                  </div>
                </dv-border-box-3>
              </div>
            </div>
            <div class="cents">
              <div class="above">
                <div class="aboveOne">
                  <div style="padding: 15px">
                    <div class="title">疾病数据信息</div>
                    <div style="
                        display: flex;
                        flex-direction: column;
                        width: 100%;
                        height: 120px;
                        color: #eeecec;
                      ">
                      <div style="display: flex; flex: 1">
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">
                            数据数量：{{ centerData.maxNum }}
                          </div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">
                            最多疾病类型：{{ centerData.maxType }}
                          </div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">
                            求诊最多科室：{{ centerData.maxDep }}
                          </div>
                        </dv-decoration-11>
                      </div>
                      <div style="display: flex; flex: 1">
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">
                            最大患者年龄：{{ centerData.maxAge }}
                          </div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">
                            最小患者年龄：{{ centerData.minAge }}
                          </div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">
                            热门医院：{{ centerData.maxHos }}
                          </div>
                        </dv-decoration-11>
                      </div>
                    </div>
                  </div>
                  <div style="padding: 15px">
                    <div class="title" style="margin-top: -30px">
                      男女性别患病对比
                    </div>

                    <div class="content">
                      <dv-active-ring-chart :config="config2" style="width: 150px; height: 100px" />
                      <dv-water-level-pond :config="config4" style="width: 100px; height: 90px" />
                      <dv-active-ring-chart :config="config3" style="width: 150px; height: 100px" />
                    </div>
                  </div>
                </div>
                <div class="aboveTwo">
                  <dv-border-box-9 :color="['#568aea']">
                    <div style="padding: 15px">
                      <div class="title" style="margin-top: 5px">
                        医院科室环形图
                      </div>
                      <div id="secondMian" style="width: 100%; height: 110px"></div>
                    </div>
                  </dv-border-box-9>
                  <dv-border-box-1>
                    <div style="padding: 5px">
                      <div class="title" style="margin-top: 5px">
                        疾病关键词云图
                      </div>
                      <div ref="thirdMain" style="width: 400px; height: 90px"></div>
                    </div>
                  </dv-border-box-1>
                </div>
              </div>
              <div class="below">
                <dv-border-box-13>
                  <div style="padding: 7px">
                    <div class="title" style="margin-top: 5px">
                      病患身高体重平均数图
                    </div>
                    <div ref="lastMain" style="width: 100%; height: 200px; margin-top: 25px"></div>
                  </div>
                </dv-border-box-13>
              </div>
            </div>
          </div>
        </div>
      </dv-border-box-10>
    </transition>
    <AiAssistantBubble
      :chart-actions="chartActions"
    />
  </div>
</template>

<script>
import $ from "jquery";
import LeftTop from "@/components/LeftTop.vue";
import AppLoading from "@/components/AppLoading.vue";
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
    chartActions() {
      return [
        {
          key: 'age-distribution',
          label: '各年龄段患病占比',
          title: '各年龄段患病占比',
          type: '年龄分布图',
          data: this.pieData,
        },
        {
          key: 'disease-distribution',
          label: '疾病类型分布',
          title: '疾病类型分布',
          type: '疾病类型分布图',
          data: this.config1.data,
        },
        {
          key: 'department-distribution',
          label: '医院科室环形图',
          title: '医院科室环形图',
          type: '科室活跃度分布图',
          data: this.circleData.slice(0, 5),
        },
      ];
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
    AppLoading,
    AiAssistantBubble,
  },
};
</script>

<style lang="less" scoped>
.screen-dashboard {
  position: relative;
  min-height: calc(100vh - 140px);
}

.dashboard-loader-shell {
  position: relative;
  min-height: calc(100vh - 140px);
}

.loading {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.cent-1-content {
  padding: 20px;
  display: flex;
}

.right-content {
  margin-left: 30px;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}

.right-content div {
  display: flex;
  font-size: 15px;
  align-items: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.cents {
  display: flex;
  flex-direction: column;
}

.above {
  display: flex;
}

.aboveOne {
  display: flex;
  flex-direction: column;
}

.aboveTwo {
  display: flex;
  flex-direction: column;
}

.cent {
  width: 850px;
  height: 300px;
}

.cent-1 {
  margin: 10px;
  color: aliceblue;
  width: 500px;
  height: 220px;
  /* background-color: rgb(26, 26, 133); */
}

.left {
  display: flex;
  flex-direction: column;
}

.left-1 {
  margin: 15px;
  color: aliceblue;
  width: 550px;
  display: flex;
  flex-direction: column;
}

.left-2 {
  margin: 15px;
  color: aliceblue;
  width: 530px;
  display: flex;
  flex-direction: column;
}

.naca {
  // padding: 35px 15px 0 15px;
  box-sizing: border-box;
  width: 100%;
  // height: 40rem;
  display: flex;
  flex-direction: column;
}

.naca .index-header {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.naca .index-header div {
  display: flex;
  justify-content: center;
  align-items: center;
}

.naca .index-content {
  display: flex;
  justify-content: center;
  align-items: center;
}

.bg {
  width: 100%;
  height: 45rem;
  background-color: black;
  position: relative;
}

.title {
  color: #3f96a5;
  font-size: 18px;
  margin-top: -20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-weight: bold;
}

.content {
  display: flex;
  align-items: center;
}

.content-word {
  width: 140px;
  height: 130px;
  background: #11193e;
  border-radius: 40px;
  border: 1px solid #3d3d3d;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.content-word-item {
  margin-left: 19px;
  margin-bottom: 10px;

  img {
    width: 20px;
    height: 20px;
  }
}

.content-word-item-title {
  font-size: 18px;
}

.content-word-item-content {
  margin-top: 5px;

  display: flex;
  align-items: center;
}

.row_list {
  list-style: none;
}

.cases_list::-webkit-scrollbar {
  display: none;
}

.cases_list li {
  display: grid; // 固定每一列的属性
  -ms-grid-columns: 30px 110px 60px 60px 60px 50px 100px;
  grid-template-columns: 30px 110px 60px 60px 60px 50px 100px;
  cursor: pointer;
  margin-left: 23px;
  text-align: center;
  line-height: 30px;
  color: rgb(238, 236, 236);
}

.cases_list li.active {
  background: rgba(77, 170, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(84, 204, 255, 0.45);
  border-radius: 6px;
}

.list_time {
  height: 30px;
  overflow: auto;
}

.list_time::-webkit-scrollbar {
  display: none;
}
</style>
