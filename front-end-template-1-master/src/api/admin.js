// src/api/admin.js - 统一的API调用文件
import request from './axios'

// ========== 用户相关 ==========
// 获取当前登录用户信息
export function getCurrentUser() {
  return request({
    url: '/me',
    method: 'get'
  })
}

// 用户登录
export function login(username, password) {
  return request({
    url: '/login',
    method: 'post',
    data: { username, password }
  })
}

// 用户注册
export function register(username, password) {
  return request({
    url: '/register',
    method: 'post',
    data: { username, password }
  })
}

// 退出登录
export function logout() {
  return request({
    url: '/logout',
    method: 'post'
  })
}

// ========== 管理员 - 用户管理 ==========
// 获取用户列表，支持按用户名模糊搜索或按 ID 精确查询
export function adminGetUsers({ username = '', id = '' } = {}) {
  const params = {}
  if (id) params.id = id
  else if (username) params.username = username
  return request({ url: '/admin/users', method: 'get', params })
}

// 修改用户状态（启用/禁用）
export function adminUpdateUserStatus(userId, status) {
  return request({
    url: '/admin/user/status',
    method: 'post',
    data: { user_id: userId, status }
  })
}

// 新增用户
export function adminCreateUser(payload) {
  return request({
    url: '/admin/user',
    method: 'post',
    data: payload
  })
}

// 修改用户信息
export function adminUpdateUser(id, payload) {
  return request({
    url: `/admin/user/${id}`,
    method: 'put',
    data: payload
  })
}

// 删除用户
export function adminDeleteUser(id) {
  return request({
    url: `/admin/user/${id}`,
    method: 'delete'
  })
}

// ========== 管理员 - 病例管理 ==========
// 获取病例列表（分页 + 按ID查询）
export function adminGetCases(page = 1, size = 10, caseId = '') {
  return request({
    url: '/admin/cases',
    method: 'get',
    params: {
      page,
      size,
      case_id: caseId || undefined
    }
  })
}

// 新增病例
export function adminCreateCase(payload) {
  return request({
    url: '/admin/case',
    method: 'post',
    data: payload
  })
}

// 更新病例
export function adminUpdateCase(id, payload) {
  return request({
    url: `/admin/case/${id}`,
    method: 'put',
    data: payload
  })
}

// 删除病例
export function adminDeleteCase(id) {
  return request({
    url: `/admin/case/${id}`,
    method: 'delete'
  })
}

// ========== 管理员 - 数据大屏 ==========
// 获取首页统计数据
export function getHomeData() {
  return request({
    url: '/getHomeData',
    method: 'get'
  })
}

// ========== 用户 - 个人病例 ==========
// 获取当前用户的病例记录
export function getMyCases() {
  return request({
    url: '/myCases',
    method: 'get'
  })
}

// ========== 用户 - 疾病预测 ==========
// 提交症状进行预测（可选指定模型模式）
export function submitPrediction(content, options = {}) {
  return request({
    url: '/submitModel',
    method: 'post',
    data: {
      content,
      ...options
    }
  })
}

// ========== 管理员 - 模型训练 ==========
// 手动重训模型，可选对比结果
export function adminRetrainModel(payload = {}) {
  return request({
    url: '/admin/model/retrain',
    method: 'post',
    data: payload
  })
}

// 获取当前缓存模型指标
export function adminGetModelMetrics() {
  return request({
    url: '/admin/model/metrics',
    method: 'get'
  })
}

// 获取数据来源统计（真实/合成）
export function adminGetModelDataStats() {
  return request({
    url: '/admin/model/data-stats',
    method: 'get'
  })
}
