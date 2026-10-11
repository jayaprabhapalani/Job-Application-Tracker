import { useEffect, useRef, useState } from 'react'

export function useWebSocket(jobId) {
  const [messages, setMessages] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    const ws = new WebSocket(`ws://localhost:8000/ws/${jobId}`)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        setMessages((prev) => [...prev, data])
      } catch {
        setMessages((prev) => [...prev, { raw: e.data }])
      }
    }

    return () => ws.close()
  }, [jobId])

  return { messages, isConnected }
}
