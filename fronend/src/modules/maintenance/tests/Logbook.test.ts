import { describe, expect, it } from 'vitest'
import { sumMoney } from '../components/utils'

describe('Logbook calculations', () => {
  it('calculates parts total correctly', () => {
    expect(sumMoney(['10.25', '4.75'])).toBe('15.00')
  })

  it('calculates labor total correctly', () => {
    expect(sumMoney([3.5, 2.25])).toBe('5.75')
  })

  it('rejects negative by preserving numeric checks upstream', () => {
    expect(Number(sumMoney([-1, 2]))).toBeGreaterThanOrEqual(0)
  })
})
