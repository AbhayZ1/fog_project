<template>
  <div class="max-w-6xl mx-auto relative z-10">
    <div class="glass-panel rounded-2xl p-8">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-2xl font-bold flex items-center gap-3">
            <i class="fa-solid fa-code-branch text-purple-400"></i> Model Version Control
          </h2>
          <p class="text-sm text-slate-400 mt-1">Manage, compare, and rollback model versions</p>
        </div>
        <button
          @click="fetchVersions"
          :disabled="loadingVersions"
          class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2"
        >
          <i class="fa-solid fa-sync" :class="{ 'fa-spin': loadingVersions }"></i>
          Refresh
        </button>
      </div>

      <div v-if="versions.length === 0" class="text-center py-16 text-slate-500">
        <i class="fa-solid fa-box-open text-5xl mb-4"></i>
        <p class="text-lg">No model versions available yet</p>
        <p class="text-sm mt-2">Start training to create version checkpoints</p>
      </div>
      <div v-else class="space-y-3">
        <div v-for="v in versions" :key="v.version" class="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-blue-500 transition-all">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-blue-900/50 rounded-lg flex items-center justify-center">
                <span class="text-xl font-bold text-blue-400">v{{ v.version }}</span>
              </div>
              <div>
                <h3 class="font-semibold text-white">Model Version {{ v.version }}</h3>
                <p class="text-xs text-slate-400">Round {{ v.version }} • {{ new Date(v.timestamp).toLocaleString() }}</p>
              </div>
            </div>

            <div class="flex items-center gap-6">
              <!-- Metrics -->
              <div class="flex gap-4 text-sm">
                <div class="text-center">
                  <div class="text-xs text-slate-400">Accuracy</div>
                  <div class="font-bold text-green-400">{{ (v.accuracy * 100).toFixed(1) }}%</div>
                </div>
                <div class="text-center">
                  <div class="text-xs text-slate-400">Privacy ε</div>
                  <div class="font-bold text-purple-400">{{ v.privacy_epsilon.toFixed(2) }}</div>
                </div>
                <div class="text-center">
                  <div class="text-xs text-slate-400">Fairness</div>
                  <div class="font-bold text-blue-400">{{ (v.fairness_score * 100).toFixed(1) }}%</div>
                </div>
                <div class="text-center">
                  <div class="text-xs text-slate-400">Size</div>
                  <div class="font-bold text-slate-300">{{ v.size_mb }} MB</div>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex gap-2">
                <button
                  @click="rollbackToVersion(v.version)"
                  class="bg-yellow-600 hover:bg-yellow-500 text-white px-3 py-2 rounded-lg text-sm transition-all flex items-center gap-2"
                  title="Rollback to this version"
                >
                  <i class="fa-solid fa-rotate-left"></i>
                  Rollback
                </button>
                <button
                  @click="downloadVersion(v.version)"
                  class="bg-green-600 hover:bg-green-500 text-white px-3 py-2 rounded-lg text-sm transition-all flex items-center gap-2"
                  title="Download this version"
                >
                  <i class="fa-solid fa-download"></i>
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const API_URL = `http://${window.location.hostname}:8081`
const versions = ref([])
const loadingVersions = ref(false)

const fetchVersions = async () => {
  loadingVersions.value = true
  try {
    const res = await fetch(`${API_URL}/models/versions`)
    const data = await res.json()
    if (data.versions) {
      versions.value = data.versions.sort((a, b) => b.privacy_epsilon - a.privacy_epsilon)
    }
  } catch (e) {
    console.error(e)
  }
  loadingVersions.value = false
}

const rollbackToVersion = async (version) => {
  if (!confirm(`Are you sure you want to rollback to version ${version}?`)) return

  try {
    const res = await fetch(`${API_URL}/models/rollback/${version}`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      alert(`Successfully rolled back to version ${version}`)
      fetchVersions()
    } else {
      alert('Rollback failed: ' + (data.error || 'Unknown error'))
    }
  } catch (e) {
    alert('Error: ' + e.message)
  }
}

const downloadVersion = (version) => {
  window.location.href = `${API_URL}/models/download/${version}`
}

onMounted(() => {
  fetchVersions()
})
</script>
