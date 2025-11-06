/**
 * 监控指标 API
 */
import { get, post } from './request'
import type { Metric, MetricsSummary } from '@/types/api'

/**
 * 获取当前指标
 */
export const getCurrentMetrics = (serverId: string) => {
  return get<Metric>(`/metrics/${serverId}/current`)
}

/**
 * 获取历史指标
 */
export const getMetricsHistory = (
  serverId: string,
  startTime: string,
  endTime: string,
  interval?: number
) => {
  return get<{ metrics: Metric[] }>(`/metrics/${serverId}/history`, {
    params: { start_time: startTime, end_time: endTime, interval },
  })
}

/**
 * 获取指标摘要
 */
export const getMetricsSummary = (serverId: string, hours = 24) => {
  return get<MetricsSummary>(`/metrics/${serverId}/summary`, {
    params: { hours },
  })
}

/**
 * 触发手动采集
 */
export const collectMetrics = (serverId: string) => {
  return post(`/metrics/${serverId}/collect`)
}
