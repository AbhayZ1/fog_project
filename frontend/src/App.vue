<template>
  <div class="min-h-screen flex flex-col">
    <Navbar
      :activeTab="activeTab"
      :isTraining="isTraining"
      @update:activeTab="activeTab = $event"
    />

    <main class="flex-1 p-6 relative overflow-hidden">
      <!-- Background Decor -->
      <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-green-500 rounded-full blur-3xl"></div>
      </div>

      <NetworkOps
        v-if="activeTab === 'network'"
        :metrics="metrics"
        :isTraining="isTraining"
        @start="startProtocol"
        @stop="stopProtocol"
      />
      <DiagnosticsLab v-else-if="activeTab === 'doctor'" />
      <ModelVersions v-else-if="activeTab === 'versions'" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import Navbar from './components/Navbar.vue'

// Lazy load heavy components
const NetworkOps = defineAsyncComponent(() => import('./components/NetworkOps.vue'))
const DiagnosticsLab = defineAsyncComponent(() => import('./components/DiagnosticsLab.vue'))
const ModelVersions = defineAsyncComponent(() => import('./components/ModelVersions.vue'))

const API_URL = `http://${window.location.hostname}:8081`
const activeTab = ref('network')
const isTraining = ref(false)
const metrics = ref([])
let ws = null

const connectWs = () => {
  const wsHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname
  ws = new WebSocket(`ws://${wsHost}:8081/ws`)

  ws.onopen = () => {
    console.log("✅ Connected to Real-time WebSocket")
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.is_training !== undefined) isTraining.value = data.is_training
      if (data.metrics) metrics.value = data.metrics
    } catch (e) {
      console.error("Error parsing WS message:", e)
    }
  }

  ws.onclose = () => {
    console.log("⚠️ WebSocket disconnected, retrying in 3s...")
    setTimeout(connectWs, 3000)
  }
}

const fetchMetrics = async () => {
  try {
    const res = await fetch(`${API_URL}/metrics`)
    const data = await res.json()
    if (data && data.length > 0) metrics.value = data
  } catch (e) {
    console.error(e)
  }
}

const startProtocol = async () => {
  metrics.value = []
  isTraining.value = true
  await fetch(`${API_URL}/train/start`, { method: 'POST' })
}

const stopProtocol = async () => {
  isTraining.value = false
  await fetch(`${API_URL}/train/stop`, { method: 'POST' })
}

onMounted(() => {
  connectWs()
  fetchMetrics()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>
