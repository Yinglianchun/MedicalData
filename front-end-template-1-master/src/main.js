import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import dataV from '@jiaminghi/data-view'
import VueParticles from 'vue-particles'
import axios from '@/api/axios' //引入api 文件下的axious
import "swiper/swiper.min.css"
import * as echarts from 'echarts';
import "@/utils/echarts-wordcloud.min.js"
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
/* 必须在 Element 主题之后，才能覆盖白底 input / date-picker 等 */
import './assets/theme.css'
import 'nprogress/nprogress.css'

Vue.use(VueParticles)
Vue.use(dataV)
Vue.use(ElementUI, { size: 'small' })
Vue.config.productionTip = false
Vue.prototype.$http = axios
Vue.prototype.$echarts = echarts
new Vue({
    router,
    store,
    render: h => h(App)
}).$mount('#app')
