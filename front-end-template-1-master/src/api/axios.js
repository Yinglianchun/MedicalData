import axios from "axios";
import NProgress from 'nprogress'


const axiosInstance = axios.create({
    // 统一走 vue devServer 代理，避免跨域/跨站 cookie 丢失登录态
    // 对应 vue.config.js: /api -> http://localhost:5000
    baseURL:'/api',
    timeout:10000,
    withCredentials: true // 允许携带cookie，用于session认证
})

// 配置拦截器 发送请求
axiosInstance.interceptors.request.use(
    (config) => {
        NProgress.start()
        return config
    },
    (error) => {
        NProgress.done()
        return Promise.reject(error)
    }
);
axiosInstance.interceptors.response.use(
    (response) => {
        NProgress.done()
        return response.data;
    },
    (error) => {
        NProgress.done()
        const res = error.response
        // Flask 返回的 JSON（401/403/500 等）仍带上 { code, message, data }，reject 会导致大屏只显示笼统失败
        if (res && res.data && typeof res.data === 'object' && !Array.isArray(res.data)) {
            return res.data
        }
        return Promise.reject(error)
    }   
);

export default axiosInstance;  // export 使其他文件可以引用