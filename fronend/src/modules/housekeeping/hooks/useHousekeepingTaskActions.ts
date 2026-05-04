import { useState } from 'react'
import { assignHousekeepingBatch, reassignOverdueBatch, transitionHousekeepingTask } from '../api/housekeeping.api'

export function useAssignHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await assignHousekeepingBatch(accessToken, payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}

export function useStartHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (taskId: number, payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await transitionHousekeepingTask(accessToken, taskId, 'start', payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}

export function useCompleteHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (taskId: number, payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await transitionHousekeepingTask(accessToken, taskId, 'complete', payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}

export function useVerifyHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (taskId: number, payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await transitionHousekeepingTask(accessToken, taskId, 'verify', payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}

export function useCancelHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (taskId: number, payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await transitionHousekeepingTask(accessToken, taskId, 'cancel', payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}

export function useReopenHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (taskId: number, payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await transitionHousekeepingTask(accessToken, taskId, 'reopen', payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}

export function useReassignOverdueHousekeepingTask(accessToken?: string) {
  const [saving, setSaving] = useState(false)
  const mutate = async (payload: Record<string, unknown>) => {
    if (!accessToken) return null
    setSaving(true)
    try {
      return await reassignOverdueBatch(accessToken, payload)
    } finally {
      setSaving(false)
    }
  }
  return { mutate, saving }
}
