/**
 * 监控指标 API
 */
import { get, post } from './request'
import type { Metric, MetricsSummary } from '@/types/api'

/**
 * 立即采集服务器指标
 */
export const collectMetrics = (serverId: string) => post(`/metrics/servers/${serverId}/collect`)

/**
 * 获取当前指标
 */
export const getCurrentMetrics = (serverId: string) =>
  get<Metric>(`/metrics/servers/${serverId}/current`)

/**
 * 获取历史指标
 */
export const getMetricsHistory = (
  serverId: string,
  startTime?: string,
  endTime?: string,
  limit?: number
) =>
  get<{ total: number; items: Metric[] }>(`/metrics/servers/${serverId}/history`, {
    params: { start_time: startTime, end_time: endTime, limit },
  })

/**
 * 获取指标摘要
 */
export const getMetricsSummary = (serverId: string, hours = 24) =>
  get<MetricsSummary>(`/metrics/servers/${serverId}/summary`, {
    params: { hours },
  })
