<template>
  <div v-if="!isLoggedIn" class="min-h-screen flex items-center justify-center bg-slate-900 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
            <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600 rounded-full blur-3xl"></div>
            <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600 rounded-full blur-3xl"></div>
        </div>

        <div class="glass-panel p-8 rounded-2xl w-full max-w-md relative z-10 border border-purple-500/30">
             <div class="text-center mb-8">
                <div class="w-16 h-16 bg-purple-600 rounded-xl flex items-center justify-center text-3xl shadow-lg shadow-purple-500/50 mx-auto mb-4">
                    <i class="fa-solid fa-shield-cat"></i>
                </div>
                <h1 class="text-2xl font-bold text-white">Admin Console</h1>
                <p class="text-slate-400 text-sm">Network Orchestration</p>
            </div>
            <form @submit.prevent="handleLogin" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">ADMIN ID</label>
                    <input 
                        type="text" 
                        v-model="username"
                        class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:border-purple-500 focus:outline-none"
                        placeholder="admin"
                    />
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">PASSWORD</label>
                    <input 
                        type="password" 
                        v-model="password"
                        class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:border-purple-500 focus:outline-none"
                        placeholder="••••••••"
                    />
                </div>
                <button type="submit" :disabled="loading" class="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded-lg shadow-lg transition-all flex justify-center items-center">
                    <span v-if="loading" class="mr-2"><i class="fas fa-spinner fa-spin"></i></span>
                    AUTHENTICATE
                </button>
            </form>
             <p v-if="error" class="text-red-400 text-center text-sm mt-4">{{ error }}</p>
        </div>
    </div>

  <div v-else class="min-h-screen flex flex-col bg-slate-900 text-white font-sans">
    <nav class="border-b border-slate-700 bg-slate-900 p-4 flex justify-between items-center shadow-lg z-10">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center text-xl shadow-lg shadow-purple-500/50">
                <i class="fa-solid fa-users-gear"></i>
            </div>
            <div>
                <h1 class="text-xl font-bold tracking-wider">FED-X <span class="text-purple-400">ADMIN</span></h1>
                <p class="text-xs text-slate-400">Network Orchestrator</p>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <div class="flex bg-slate-800 rounded-lg p-1">
                <button
                    @click="activeTab = 'network'"
                    :class="['px-4 py-2 rounded-md text-sm font-medium transition-all', activeTab === 'network' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white']"
                >
                    <i class="fa-solid fa-network-wired mr-2"></i>Ops
                </button>
                <button
                    @click="activeTab = 'versions'"
                    :class="['px-4 py-2 rounded-md text-sm font-medium transition-all', activeTab === 'versions' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white']"
                >
                    <i class="fa-solid fa-code-branch mr-2"></i>Versions
                </button>
            </div>
             <button @click="isLoggedIn = false" class="text-slate-400 hover:text-white transition-colors">
                <i class="fa-solid fa-sign-out-alt mr-1"></i>
            </button>
        </div>
    </nav>

    <main class="flex-1 p-6 relative overflow-hidden">
      <!-- Background Decor -->
      <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
      </div>
        
      <div class="relative z-10">
          <NetworkOps 
            v-if="activeTab === 'network'"
            :metrics="metrics"
            :isTraining="isTraining"
            @start="startProtocol"
            @stop="stopProtocol"
          />
          <ModelVersions v-if="activeTab === 'versions'" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NetworkOps from '../components/NetworkOps.vue'
import ModelVersions from '../components/ModelVersions.vue'

// API Configuration
const API_BASE = window.location.origin;

const isLoggedIn = ref(false)
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const activeTab = ref('network')
const isTraining = ref(false)
const metrics = ref([])
let ws = null

const handleLogin = async () => {
    loading.value = true
    error.value = ''
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username.value, password: password.value, role: 'admin' })
        })
        
        if (res.ok) {
            isLoggedIn.value = true
            // Connect to websocket upon login
            connectWs()
            fetchMetrics()
        } else {
            error.value = 'Invalid Credentials'
        }
    } catch (e) {
        error.value = 'Connection Error: Is the API running?'
        console.error(e)
    } finally {
        loading.value = false
    }
}

const connectWs = () => {
  // Use API_BASE hostname but adjust scheme to ws/wss
  const url = new URL(API_BASE)
  const wsProtocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${url.hostname}:${url.port}/ws`
  
  ws = new WebSocket(wsUrl)

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
    if(isLoggedIn.value) {
        console.log("⚠️ WebSocket disconnected, retrying in 3s...")
        setTimeout(connectWs, 3000)
    }
  }
}

const fetchMetrics = async () => {
  try {
    const res = await fetch(`${API_BASE}/metrics`)
    const data = await res.json()
    if (data && data.length > 0) metrics.value = data
  } catch (e) {
    console.error(e)
  }
}

const startProtocol = async () => {
  metrics.value = []
  isTraining.value = true
  await fetch(`${API_BASE}/train/start`, { method: 'POST' })
}

const stopProtocol = async () => {
  isTraining.value = false
  await fetch(`${API_BASE}/train/stop`, { method: 'POST' })
}

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style>
/* Glassmorphism helpers */
.glass-panel {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
