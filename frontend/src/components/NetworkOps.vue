<template>
  <div class="max-w-7xl mx-auto space-y-6 relative z-10">
    <!-- Training Statistics Banner -->
    <div v-if="metrics.length > 0" class="glass-panel rounded-2xl p-4 animation-fade-in">
      <div class="grid grid-cols-5 gap-4">
        <!-- Progress -->
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-blue-900/50 flex items-center justify-center">
            <i class="fa-solid fa-chart-line text-blue-400 text-xl"></i>
          </div>
          <div>
            <div class="text-xs text-slate-400">Progress</div>
            <div class="text-lg font-bold text-white">
              {{ latestMetric.progress_percentage?.toFixed(0) || 0 }}%
            </div>
          </div>
        </div>

        <!-- Elapsed Time -->
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-purple-900/50 flex items-center justify-center">
            <i class="fa-solid fa-clock text-purple-400 text-xl"></i>
          </div>
          <div>
            <div class="text-xs text-slate-400">Elapsed</div>
            <div class="text-lg font-bold text-white">
              {{ latestMetric.elapsed_minutes?.toFixed(1) || 0 }}m
            </div>
          </div>
        </div>

        <!-- ETA -->
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-green-900/50 flex items-center justify-center">
            <i class="fa-solid fa-hourglass-half text-green-400 text-xl"></i>
          </div>
          <div>
            <div class="text-xs text-slate-400">ETA</div>
            <div class="text-lg font-bold text-white">
              {{ latestMetric.eta_minutes?.toFixed(1) || 0 }}m
            </div>
          </div>
        </div>

        <!-- Training Speed -->
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-orange-900/50 flex items-center justify-center">
            <i class="fa-solid fa-gauge-high text-orange-400 text-xl"></i>
          </div>
          <div>
            <div class="text-xs text-slate-400">Speed</div>
            <div class="text-lg font-bold text-white">
              {{ latestMetric.training_speed?.toFixed(2) || 0 }}
            </div>
            <div class="text-xs text-slate-500">rounds/min</div>
          </div>
        </div>

        <!-- Current Round -->
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-cyan-900/50 flex items-center justify-center">
            <i class="fa-solid fa-rotate text-cyan-400 text-xl"></i>
          </div>
          <div>
            <div class="text-xs text-slate-400">Round</div>
            <div class="text-lg font-bold text-white">
              {{ metrics.length }} / 25
            </div>
          </div>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="mt-4">
        <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
            :style="{ width: `${latestMetric.progress_percentage || 0}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Top Row: Visualizer + Controls -->
    <div class="grid grid-cols-12 gap-6">
      <!-- Visualizer Panel -->
      <div class="col-span-12 lg:col-span-7 glass-panel rounded-2xl p-6 h-[500px] relative flex flex-col">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-lg font-semibold flex items-center">
            <span class="w-3 h-3 rounded-full mr-2" :class="isTraining ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
            Real-Time Network Topology
          </h2>
          <div class="text-xs text-slate-400 font-mono">
            ENCRYPTION: AES-256 <span class="mx-2">|</span> PRIVACY: ε={{ latestMetric.privacy_epsilon ? latestMetric.privacy_epsilon.toFixed(1) : '4.2' }}
          </div>
        </div>

        <div class="flex-1 relative border border-slate-700/50 rounded-xl bg-slate-900/50 overflow-hidden">
          <!-- Server Node -->
          <div class="absolute top-[20%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-20">
            <div class="w-16 h-16 rounded-full bg-slate-800 border-2 border-blue-500 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(59,130,246,0.3)]" :class="{ 'pulse-ring': isTraining }">
              <i class="fa-solid fa-server text-blue-400"></i>
            </div>
            <span class="mt-2 text-sm font-bold text-blue-200 bg-slate-900/80 px-2 rounded">AGGREGATOR</span>
          </div>

          <!-- Hospital A -->
          <div class="absolute bottom-[20%] left-[20%] transform -translate-x-1/2 flex flex-col items-center z-20">
            <div class="w-14 h-14 rounded-full bg-slate-800 border-2 border-green-500 flex items-center justify-center text-xl shadow-[0_0_20px_rgba(34,197,94,0.3)]">
              <i class="fa-solid fa-hospital text-green-400"></i>
            </div>
            <span class="mt-2 text-xs text-slate-300">Client A (Boston)</span>
          </div>

          <!-- Hospital B -->
          <div class="absolute bottom-[20%] left-[80%] transform -translate-x-1/2 flex flex-col items-center z-20">
            <div class="w-14 h-14 rounded-full bg-slate-800 border-2 border-green-500 flex items-center justify-center text-xl shadow-[0_0_20px_rgba(34,197,94,0.3)]">
              <i class="fa-solid fa-hospital text-green-400"></i>
            </div>
            <span class="mt-2 text-xs text-slate-300">Client B (London)</span>
          </div>

          <svg class="absolute top-0 left-0 w-full h-full pointer-events-none stroke-slate-700" stroke-width="2">
            <line x1="50%" y1="20%" x2="20%" y2="60%" stroke-dasharray="5,5" />
            <line x1="50%" y1="20%" x2="80%" y2="60%" stroke-dasharray="5,5" />
          </svg>

          <div v-if="isTraining">
            <div class="packet packet-down-a"></div>
            <div class="packet packet-down-b"></div>
            <div class="packet packet-up-a"></div>
            <div class="packet packet-up-b"></div>
          </div>
        </div>
      </div>

      <!-- Controls & Live Graph -->
      <div class="col-span-12 lg:col-span-5 flex flex-col gap-6">
        <!-- Action Card -->
        <div class="glass-panel p-6 rounded-2xl">
          <h3 class="text-sm uppercase text-slate-400 font-bold mb-4">Protocol Controls</h3>
          <div class="flex gap-4">
            <button v-if="!isTraining" @click="$emit('start')" class="flex-1 bg-green-600 hover:bg-green-500 text-white font-bold py-4 rounded-xl shadow-lg shadow-green-900/20 transition-all active:scale-95 flex items-center justify-center gap-2">
              <i class="fa-solid fa-rocket"></i> INITIALIZE NETWORK
            </button>
            <button v-else @click="$emit('stop')" class="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-4 rounded-xl shadow-lg shadow-red-900/20 transition-all active:scale-95 flex items-center justify-center gap-2">
              <i class="fa-solid fa-power-off"></i> TERMINATE
            </button>
          </div>
        </div>

        <!-- Live Graph -->
        <div class="glass-panel p-6 rounded-2xl flex-1 flex flex-col">
          <div class="flex justify-between items-end mb-4">
            <div>
              <h3 class="text-sm uppercase text-slate-400 font-bold">Global Accuracy</h3>
              <div class="text-3xl font-mono font-bold text-white mt-1">
                {{ latestMetric.accuracy ? (latestMetric.accuracy * 100).toFixed(2) : "0.00" }}%
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm text-slate-400">Current Round</div>
              <div class="text-xl font-bold text-blue-400">{{ metrics.length }} / 25</div>
            </div>
          </div>

          <div class="flex-1 w-full h-40">
            <MetricsChart :metrics="metrics" />
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Row: Privacy + Fairness -->
    <div class="grid grid-cols-12 gap-6">
      <!-- Privacy Budget Panel -->
      <div class="col-span-12 lg:col-span-6 glass-panel p-6 rounded-2xl">
        <div class="flex items-center gap-2 mb-4">
          <i class="fa-solid fa-shield-halved text-purple-400 text-xl"></i>
          <h3 class="text-sm uppercase text-slate-400 font-bold">Differential Privacy Tracker</h3>
        </div>

        <div v-if="latestMetric.privacy_epsilon" class="space-y-4">
          <div class="bg-slate-800/50 rounded-lg p-4">
            <div class="flex justify-between items-center mb-2">
              <span class="text-slate-400 text-sm">Differential Privacy Metric (ε)</span>
              <span class="px-2 py-1 rounded text-xs font-bold"
                :class="{
                  'bg-green-900/50 text-green-400': latestMetric.privacy_risk === 'LOW',
                  'bg-yellow-900/50 text-yellow-400': latestMetric.privacy_risk === 'MEDIUM',
                  'bg-red-900/50 text-red-400': latestMetric.privacy_risk === 'HIGH'
                }">
                {{ latestMetric.privacy_risk }} RISK
              </span>
            </div>
            <div class="text-3xl font-mono font-bold text-purple-400">
              ε = {{ latestMetric.privacy_epsilon.toFixed(2) }}
            </div>
            <div class="text-xs text-slate-500 mt-1">
              δ = {{ latestMetric.privacy_delta.toExponential(1) }}
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex justify-between text-xs text-slate-400">
              <span>Differential Privacy Applied</span>
              <span>
                {{ Math.min(100, (latestMetric.privacy_epsilon / 10) * 100).toFixed(0) }}%
              </span>
            </div>

            <div class="h-3 bg-slate-700 rounded-full overflow-hidden">
              <div
                class="h-full transition-all duration-500"
                :class="{
                  'bg-green-500': latestMetric.privacy_risk === 'LOW',
                  'bg-yellow-500': latestMetric.privacy_risk === 'MEDIUM',
                  'bg-red-500': latestMetric.privacy_risk === 'HIGH'
                }"
                :style="{ width: `${Math.min(100, (latestMetric.privacy_epsilon / 10) * 100)}%` }"
              ></div>
            </div>

            <p class="text-xs text-slate-400 leading-relaxed">
              🔒 <strong>Patient Privacy Status:</strong>
              The model uses <span class="text-purple-400 font-medium">differential privacy</span> to ensure that
              individual patient records <strong>cannot be identified or reconstructed</strong>.
              Lower ε values indicate stronger privacy protection.
            </p>
          </div>
        </div>
        <div v-else class="text-center text-slate-500 py-8">
          <i class="fa-solid fa-shield text-3xl mb-2"></i>
          <p class="text-sm">Start training to track privacy budget</p>
        </div>
      </div>

      <!-- Fairness Analysis Panel -->
      <div class="col-span-12 lg:col-span-6 glass-panel p-6 rounded-2xl">
        <div class="flex items-center gap-2 mb-4">
          <i class="fa-solid fa-scale-balanced text-green-400 text-xl"></i>
          <h3 class="text-sm uppercase text-slate-400 font-bold">Fairness & Bias Analysis</h3>
        </div>

        <div v-if="latestMetric.fairness_score !== undefined" class="space-y-4">
          <div class="grid grid-cols-3 gap-3">
            <!-- Hospital A Performance -->
            <div class="bg-slate-800/50 rounded-lg p-3">
              <div class="flex items-center gap-1 mb-1">
                <i class="fa-solid fa-hospital text-blue-400 text-xs"></i>
                <span class="text-xs text-slate-400">Hospital A</span>
              </div>
              <div class="text-xl font-bold text-blue-400">
                {{ (latestMetric.hospital_a_accuracy * 100).toFixed(1) }}%
              </div>
            </div>

            <!-- Hospital B Performance -->
            <div class="bg-slate-800/50 rounded-lg p-3">
              <div class="flex items-center gap-1 mb-1">
                <i class="fa-solid fa-hospital text-purple-400 text-xs"></i>
                <span class="text-xs text-slate-400">Hospital B</span>
              </div>
              <div class="text-xl font-bold text-purple-400">
                {{ (latestMetric.hospital_b_accuracy * 100).toFixed(1) }}%
              </div>
            </div>

            <!-- Fairness Score -->
            <div class="bg-slate-800/50 rounded-lg p-3">
              <div class="flex items-center gap-1 mb-1">
                <i class="fa-solid fa-balance-scale text-green-400 text-xs"></i>
                <span class="text-xs text-slate-400">Fairness</span>
              </div>
              <div class="text-xl font-bold"
                :class="{
                  'text-green-400': latestMetric.fairness_score > 0.95,
                  'text-yellow-400': latestMetric.fairness_score > 0.90 && latestMetric.fairness_score <= 0.95,
                  'text-red-400': latestMetric.fairness_score <= 0.90
                }">
                {{ (latestMetric.fairness_score * 100).toFixed(1) }}%
              </div>
            </div>
          </div>

          <div class="bg-slate-800/30 rounded-lg p-3 border-l-4 border-green-500">
            <p class="text-xs text-slate-400">
              <i class="fa-solid fa-info-circle mr-1"></i>
              <strong>Fairness Score:</strong> Measures equal performance across hospitals.
              Gap: {{ (latestMetric.fairness_gap * 100).toFixed(2) }}%
              {{ latestMetric.fairness_score > 0.95 ? " ✅ No significant bias detected." : " ⚠️ Performance gap detected." }}
            </p>
          </div>
        </div>
        <div v-else class="text-center text-slate-500 py-8">
          <i class="fa-solid fa-chart-bar text-3xl mb-2"></i>
          <p class="text-sm">Fairness metrics will appear after training starts</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import MetricsChart from './MetricsChart.vue'
import { computed } from 'vue'

const props = defineProps({
  metrics: {
    type: Array,
    default: () => []
  },
  isTraining: Boolean
})

defineEmits(['start', 'stop'])

const latestMetric = computed(() => {
  return props.metrics.length > 0 ? props.metrics[props.metrics.length - 1] : {}
})
</script>
