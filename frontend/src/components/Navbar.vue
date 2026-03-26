<template>
  <nav class="border-b border-slate-700 bg-slate-900 p-4 flex justify-between items-center shadow-lg z-10">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-xl shadow-lg shadow-blue-500/50">
        <i class="fa-solid fa-dna"></i>
      </div>
      <div>
        <h1 class="text-xl font-bold tracking-wider">MedCure <span class="text-blue-400">MEDICAL</span></h1>
        <p class="text-xs text-slate-400">Secure Distributed Orchestrator</p>
      </div>
      
      <!-- Status Badge -->
      <div class="ml-4 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-2 border transition-all"
           :class="isTraining ? 'bg-green-900/30 text-green-400 border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.3)]' : 'bg-slate-800 text-slate-500 border-slate-700'">
        <div class="w-2 h-2 rounded-full" :class="isTraining ? 'bg-green-500 animate-pulse' : 'bg-slate-500'"></div>
        {{ isTraining ? 'TRAINING IN PROGRESS' : 'SYSTEM IDLE' }}
      </div>
    </div>
    <div class="flex bg-slate-800 rounded-lg p-1">
      <button
        @click="$emit('update:activeTab', 'network')"
        class="px-4 py-2 rounded-md text-sm font-medium transition-all"
        :class="activeTab === 'network' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'"
      >
        <i class="fa-solid fa-network-wired mr-2"></i>Network Ops
      </button>
      <button
        @click="$emit('update:activeTab', 'doctor')"
        class="px-4 py-2 rounded-md text-sm font-medium transition-all"
        :class="activeTab === 'doctor' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'"
      >
        <i class="fa-solid fa-user-doctor mr-2"></i>Diagnostics Lab
      </button>
      <button
        @click="$emit('update:activeTab', 'versions')"
        class="px-4 py-2 rounded-md text-sm font-medium transition-all"
        :class="activeTab === 'versions' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'"
      >
        <i class="fa-solid fa-code-branch mr-2"></i>Model Versions
      </button>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  activeTab: String,
  isTraining: Boolean
})
defineEmits(['update:activeTab'])
</script>
