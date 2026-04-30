export const STUDY_TIME_STORAGE_KEY = 'study_open_seconds'

export function getStudyTimeStorageKey(user) {
  const identifier = user?.id ?? user?.email
  if (identifier === undefined || identifier === null || identifier === '') {
    return null
  }

  return `${STUDY_TIME_STORAGE_KEY}:${encodeURIComponent(String(identifier))}`
}

function getStoredOpenStudySecondsForKey(storageKey) {
  if (!storageKey) {
    return 0
  }

  const value = Number(localStorage.getItem(storageKey) || '0')
  if (!Number.isFinite(value) || value < 0) {
    return 0
  }
  return Math.floor(value)
}

export function getStoredOpenStudySeconds(user) {
  return getStoredOpenStudySecondsForKey(getStudyTimeStorageKey(user))
}

export function addOpenStudySeconds(secondsToAdd, user) {
  const amount = Math.max(0, Math.floor(Number(secondsToAdd) || 0))
  const storageKey = getStudyTimeStorageKey(user)
  if (!amount || !storageKey) return

  const current = getStoredOpenStudySecondsForKey(storageKey)
  localStorage.setItem(storageKey, String(current + amount))
}

export function resetStoredOpenStudySeconds(user) {
  const storageKey = getStudyTimeStorageKey(user)
  if (!storageKey) return

  localStorage.setItem(storageKey, '0')
}

export function getStoredOpenStudyMinutes(user) {
  return Math.floor(getStoredOpenStudySeconds(user) / 60)
}
