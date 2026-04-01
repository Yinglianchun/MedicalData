import Vue from 'vue'
import VueRouter from 'vue-router'
import { getCurrentUser } from '@/api/admin'
import NProgress from 'nprogress'
import { Message } from 'element-ui'

Vue.use(VueRouter)

const routes = [
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },

  // 主布局
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      // 默认重定向
      { 
        path: '', 
        redirect: to => {
          // 根据用户角色重定向到不同页面（会在路由守卫中处理）
          return '/admin/dashboard'
        }
      },

      // 管理员路由
      {
        path: 'admin/dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'admin/dashboard-trend',
        redirect: { path: '/admin/dashboard' },
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManagement.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'admin/cases',
        name: 'AdminCases',
        component: () => import('@/views/admin/CaseManagement.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
      },

      // 用户路由
      {
        path: 'user/predict',
        name: 'UserPredict',
        component: () => import('@/views/user/Prediction.vue'),
        meta: { requiresAuth: true, requiresUser: true }
      },
      {
        path: 'user/cases',
        name: 'UserCases',
        component: () => import('@/views/user/MyCases.vue'),
        meta: { requiresAuth: true, requiresUser: true }
      }
    ]
  },

  // 404页面（可选）
  {
    path: '*',
    redirect: '/login'
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})
NProgress.configure({ showSpinner: false, easing: 'ease', speed: 360 })

// 全局路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  // 如果是访问登录页，直接放行
  if (to.path === '/login') {
    next()
    return
  }

  // 如果路由不需要认证，直接放行
  if (!to.meta.requiresAuth) {
    next()
    return
  }

  // 需要认证的路由，检查登录状态
  try {
    const res = await getCurrentUser()
    
    if (res.code === 200) {
      const user = res.data
      const userRole = user.role

      // 如果访问的是根路径，根据角色重定向
      if (to.path === '/') {
        if (userRole === 'admin') {
          next('/admin/dashboard')
        } else {
          next('/user/predict')
        }
        return
      }

      // 检查管理员权限
      if (to.meta.requiresAdmin && userRole !== 'admin') {
        Message.warning('您没有权限访问该页面')
        next('/user/predict')
        return
      }

      // 检查用户权限（防止管理员访问用户页面，可选）
      if (to.meta.requiresUser && userRole === 'admin') {
        next('/admin/dashboard')
        return
      }

      next()
    } else {
      // 未登录，跳转到登录页
      next('/login')
    }
  } catch (e) {
    console.error('路由守卫错误:', e)
    // 发生错误（如网络问题或未登录401），跳转到登录页
    next('/login')
  }
})
router.afterEach(() => {
  NProgress.done()
})

export default router
