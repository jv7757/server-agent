/**
 * Axios 请求封装
 */
import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建 axios 实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 添加 token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 未授权，清除 token 并跳转到登录页
          const authStore = useAuthStore()
          authStore.logout()
          router.push('/login')
          ElMessage.error(data.detail || '未授权，请重新登录')
          break

        case 403:
          ElMessage.error(data.detail || '权限不足')
          break

        case 404:
          ElMessage.error(data.detail || '资源不存在')
          break

        case 422:
          // 验证错误
          if (data.detail && Array.isArray(data.detail)) {
            const errors = data.detail.map((err: any) => err.msg).join('; ')
            ElMessage.error(errors)
          } else {
            ElMessage.error(data.detail || '验证失败')
          }
          break

        case 500:
          ElMessage.error(data.detail || '服务器错误')
          break

        default:
          ElMessage.error(data.detail || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查您的网络连接')
    } else {
      ElMessage.error('请求失败: ' + error.message)
    }

    return Promise.reject(error)
  }
)

// 导出封装的请求方法
export default request

// 泛型请求方法
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.get(url, config).then((res) => res.data)
}

export const post = <T = any>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> => {
  return request.post(url, data, config).then((res) => res.data)
}

export const put = <T = any>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> => {
  return request.put(url, data, config).then((res) => res.data)
}

export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.delete(url, config).then((res) => res.data)
}
