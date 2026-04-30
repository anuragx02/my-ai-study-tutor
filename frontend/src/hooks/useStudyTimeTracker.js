import { useEffect, useRef } from 'react'
import { addOpenStudySeconds } from '../utils/studyTime'

export default function useStudyTimeTracker(user) {
  const lastVisibleAtRef = useRef(null)

  useEffect(() => {
    if (!user?.id && !user?.email) {
      lastVisibleAtRef.current = null
      return undefined
    }

    if (document.visibilityState === 'visible') {
      lastVisibleAtRef.current = Date.now()
    }

    function flushVisibleTime() {
      if (!lastVisibleAtRef.current) {
        return
      }

      const elapsedSeconds = Math.floor((Date.now() - lastVisibleAtRef.current) / 1000)
      if (elapsedSeconds > 0) {
        addOpenStudySeconds(elapsedSeconds, user)
      }
      lastVisibleAtRef.current = Date.now()
    }

    function handleVisibilityChange() {
      if (document.visibilityState === 'hidden') {
        flushVisibleTime()
        lastVisibleAtRef.current = null
        return
      }

      lastVisibleAtRef.current = Date.now()
    }

    const intervalId = window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        flushVisibleTime()
      }
    }, 15000)

    window.addEventListener('beforeunload', flushVisibleTime)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      flushVisibleTime()
      window.clearInterval(intervalId)
      window.removeEventListener('beforeunload', flushVisibleTime)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [user?.id, user?.email])
}
