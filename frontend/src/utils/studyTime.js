export const STUDY_TIME_STORAGE_KEY = 'study_open_seconds'

export function getStoredOpenStudySeconds() {
  const value = Number(localStorage.getItem(STUDY_TIME_STORAGE_KEY) || '0')
  if (!Number.isFinite(value) || value < 0) {
    return 0
  }
  return Math.floor(value)
}

export function addOpenStudySeconds(secondsToAdd) {
  const amount = Math.max(0, Math.floor(Number(secondsToAdd) || 0))
  if (!amount) return

  const current = getStoredOpenStudySeconds()
  localStorage.setItem(STUDY_TIME_STORAGE_KEY, String(current + amount))
}

export function resetStoredOpenStudySeconds() {
  localStorage.setItem(STUDY_TIME_STORAGE_KEY, '0')
}

export function getStoredOpenStudyMinutes() {
  return Math.floor(getStoredOpenStudySeconds() / 60)
}
