<template>
  <div v-if="!isLoggedIn" class="min-h-screen flex items-center justify-center bg-slate-900 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
            <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600 rounded-full blur-3xl"></div>
            <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-green-600 rounded-full blur-3xl"></div>
        </div>

        <div class="glass-panel p-8 rounded-2xl w-full max-w-md relative z-10 border border-blue-500/30">
            <div class="text-center mb-8">
                <div class="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center text-3xl shadow-lg shadow-blue-500/50 mx-auto mb-4">
                    <i class="fa-solid fa-user-doctor"></i>
                </div>
                <h1 class="text-2xl font-bold text-white">Diagnostics Portal</h1>
                <p class="text-slate-400 text-sm">Secure Client Access</p>
            </div>
            <form @submit.prevent="handleLogin" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">DOCTOR ID</label>
                    <input 
                        type="text" 
                        v-model="username"
                        class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:outline-none"
                        placeholder="doctor"
                    />
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">PASSWORD</label>
                    <input 
                        type="password" 
                        v-model="password"
                        class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:outline-none"
                        placeholder="••••••••"
                    />
                </div>
                <button type="submit" :disabled="loading" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg shadow-lg transition-all flex justify-center items-center">
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
            <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-xl shadow-lg shadow-blue-500/50">
                <i class="fa-solid fa-dna"></i>
            </div>
            <div>
                <h1 class="text-xl font-bold tracking-wider">FED-X <span class="text-blue-400">CLIENT</span></h1>
                <p class="text-xs text-slate-400">Diagnostics Portal</p>
            </div>
        </div>
        <div>
            <button @click="isLoggedIn = false" class="text-slate-400 hover:text-white transition-colors">
                <i class="fa-solid fa-sign-out-alt mr-1"></i> Logout
            </button>
        </div>
    </nav>

    <main class="flex-1 p-6 relative overflow-hidden">
      <!-- Background Decor -->
      <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-green-500 rounded-full blur-3xl"></div>
      </div>
        
      <div class="relative z-10">
          <DiagnosticsLab />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DiagnosticsLab from './components/DiagnosticsLab.vue'

// API Configuration
// If served by the Server, use relative path. If served standalone, use env var or default to localhost:5500
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5500'

const isLoggedIn = ref(false)
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
    loading.value = true
    error.value = ''
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username.value, password: password.value, role: 'doctor' })
        })
        
        if (res.ok) {
            const data = await res.json()
            isLoggedIn.value = true
            // Save token if needed
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
</script>

<style>
/* Glassmorphism helpers */
.glass-panel {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
