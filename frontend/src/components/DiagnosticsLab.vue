<template>
  <div class="max-w-6xl mx-auto glass-panel rounded-2xl p-6 relative z-10">
    <h2 class="text-2xl font-bold mb-6 flex items-center gap-3 text-white">
      <div class="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center">
        <i class="fa-solid fa-microscope text-blue-400"></i>
      </div>
      AI Diagnostics Lab
    </h2>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Upload Section -->
      <div class="border-2 border-dashed border-slate-700/50 rounded-xl p-8 text-center hover:border-blue-500/50 transition-all duration-300 bg-slate-900/30 group">
        <input
          type="file"
          id="fileInput"
          class="hidden"
          accept="image/*"
          @change="handleFileSelect"
        />
        <label for="fileInput" class="cursor-pointer flex flex-col items-center gap-4 h-full justify-center">
          <img v-if="preview" :src="preview" alt="Preview" class="max-h-80 rounded-lg shadow-2xl border border-slate-700/50" />
          <div v-else class="py-12">
             <div class="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center text-3xl mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-black/20">
                <i class="fa-solid fa-cloud-arrow-up text-blue-400"></i>
             </div>
             <div>
                <p class="font-bold text-lg text-slate-200">Click to upload X-Ray</p>
                <p class="text-sm text-slate-500 mt-2">Supports PNG, JPG (DICOM sim)</p>
             </div>
          </div>
        </label>
      </div>

      <!-- Results Section -->
      <div class="flex flex-col justify-center">
         <div v-if="!preview" class="text-center text-slate-500 py-12 bg-slate-900/30 rounded-xl border border-slate-800/50">
            <i class="fa-solid fa-arrow-left mr-2"></i> Upload scan to begin analysis
         </div>
         <div v-else class="space-y-6">
            <div v-if="!prediction" class="space-y-4">
               <button
                  @click="runDiagnosis"
                  :disabled="loadingPred"
                  class="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 disabled:from-slate-700 disabled:to-slate-800 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-900/20 active:scale-[0.98]"
               >
                  <i v-if="loadingPred" class="fa-solid fa-circle-notch fa-spin mr-2"></i>
                  <span v-else>RUN ANALYSIS</span>
               </button>
               <button
                  @click="resetUpload"
                  class="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold py-4 rounded-xl transition-all border border-slate-700 hover:border-slate-600"
               >
                  CANCEL
               </button>
            </div>
            <div v-else>
               <!-- Prediction Result -->
               <div class="bg-slate-900/50 rounded-xl p-6 border border-slate-700/50 animation-fade-in shadow-xl">
                  <div class="flex justify-between items-start mb-6">
                     <div>
                        <p class="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Prediction</p>
                        <h3 class="text-4xl font-bold tracking-tight" :class="prediction.prediction === 'PNEUMONIA' ? 'text-red-400' : 'text-emerald-400'">
                           {{ prediction.prediction }}
                        </h3>
                     </div>
                     <div class="text-right">
                        <p class="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Confidence</p>
                        <p class="text-3xl font-mono text-white">{{ prediction.confidence.toFixed(1) }}%</p>
                     </div>
                  </div>

                  <div class="space-y-3">
                     <div class="flex justify-between text-xs text-slate-400 font-medium">
                        <span>Normal</span>
                        <span>Pneumonia</span>
                     </div>
                     <div class="h-3 bg-slate-800 rounded-full overflow-hidden flex relative shadow-inner">
                        <div class="h-full bg-emerald-500 transition-all duration-1000" :style="{ width: `${prediction.probabilities?.normal * 100 || 0}%` }"></div>
                        <div class="h-full bg-red-500 transition-all duration-1000" :style="{ width: `${prediction.probabilities?.pneumonia * 100 || 0}%` }"></div>
                     </div>
                  </div>
               </div>
               

               <div class="grid grid-cols-2 gap-4 p-4">
                 <button v-if="heatmapUrl"
                    @click="showExplanation = !showExplanation"
                    class="bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-bold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
                 >
                    <i class="fa-solid fa-brain"></i>
                    {{ showExplanation ? 'Hide' : 'Show' }} Explanation
                 </button>

                 <button
                    @click="resetUpload"
                    class="bg-slate-800 hover:bg-slate-700 text-white font-bold py-3 rounded-xl transition-all flex items-center justify-center gap-2 border border-slate-700"
                 >
                    <i class="fa-solid fa-rotate-right"></i> New Scan
                 </button>
               </div>
            </div>
         </div>
      </div>
    </div>

    <div v-if="showExplanation && heatmapUrl" class="mt-6 glass-panel rounded-xl p-6 animation-fade-in border border-slate-700/50 bg-slate-900/40">
       <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center">
            <i class="fa-solid fa-fire text-orange-400"></i>
          </div>
          <h3 class="text-lg font-bold text-slate-200">Explainable AI Analysis</h3>
       </div>
       <p class="text-sm text-slate-400 mb-6 leading-relaxed">
          The heatmap highlights regions of interest. <span class="text-orange-400 font-bold">Warmer colors</span> indicate areas that most influenced the model's decision.
       </p>
       <div class="flex justify-center bg-black/20 p-4 rounded-xl">
          <img :src="heatmapUrl" alt="Grad-CAM Heatmap" class="max-w-md w-full rounded-lg shadow-2xl border border-slate-700" />
       </div>
    </div>

    <!-- Feedback Section -->
    <div v-if="prediction && !feedbackSubmitted" class="mt-6 bg-slate-900/40 rounded-xl p-6 animation-fade-in border border-slate-700/50">
      <div class="flex justify-between items-center cursor-pointer group" @click="showFeedbackForm = !showFeedbackForm">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center group-hover:bg-blue-500/30 transition-colors">
            <i class="fa-solid fa-user-doctor text-blue-400"></i>
          </div>
          <h3 class="text-lg font-bold text-slate-200">Doctor's Verification</h3>
        </div>
        <div class="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 group-hover:border-slate-600 transition-colors">
          <i class="fa-solid text-slate-400 text-sm" :class="showFeedbackForm ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
        </div>
      </div>

      <div v-if="showFeedbackForm" class="mt-6 space-y-6 border-t border-slate-800 pt-6">
        
        <!-- 1. Diagnosis Verification -->
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Is the diagnosis correct?</label>
          <div class="flex gap-4">
            <button 
              @click="feedback.isCorrect = true; feedback.correctLabel = prediction.prediction"
              class="flex-1 py-3 rounded-xl border transition-all flex items-center justify-center gap-2 font-medium"
              :class="feedback.isCorrect === true ? 'bg-emerald-600 border-emerald-500 text-white shadow-lg shadow-emerald-900/20' : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-750 hover:border-slate-600'"
            >
              <i class="fa-solid fa-check"></i> Yes, Correct
            </button>
            <button 
              @click="feedback.isCorrect = false; feedback.correctLabel = prediction.prediction === 'NORMAL' ? 'PNEUMONIA' : 'NORMAL'"
              class="flex-1 py-3 rounded-xl border transition-all flex items-center justify-center gap-2 font-medium"
              :class="feedback.isCorrect === false ? 'bg-red-600 border-red-500 text-white shadow-lg shadow-red-900/20' : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-750 hover:border-slate-600'"
            >
              <i class="fa-solid fa-xmark"></i> No, Incorrect
            </button>
          </div>
        </div>

        <!-- 2. Correct Label (only if incorrect) -->
        <div v-if="feedback.isCorrect === false" class="animation-fade-in">
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Correct Diagnosis</label>
          <div class="flex gap-4">
            <button 
              @click="feedback.correctLabel = 'NORMAL'"
              class="flex-1 py-3 rounded-xl border transition-all font-medium"
              :class="feedback.correctLabel === 'NORMAL' ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-900/20' : 'bg-slate-800 border-slate-700 text-slate-400'"
            >
              NORMAL
            </button>
            <button 
              @click="feedback.correctLabel = 'PNEUMONIA'"
              class="flex-1 py-3 rounded-xl border transition-all font-medium"
              :class="feedback.correctLabel === 'PNEUMONIA' ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-900/20' : 'bg-slate-800 border-slate-700 text-slate-400'"
            >
              PNEUMONIA
            </button>
          </div>
        </div>

        <!-- 3. Heatmap Feedback -->
        <div v-if="heatmapUrl">
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Heatmap Accuracy</label>
          <div class="relative">
            <select v-model="feedback.heatmapRating" class="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-white focus:border-blue-500 outline-none appearance-none cursor-pointer">
              <option value="accurate">Accurate Area</option>
              <option value="wrong_area">Wrong Area (False Attention)</option>
              <option value="irrelevant">Irrelevant / No Focus</option>
            </select>
            <div class="absolute right-4 top-1/2 transform -translate-y-1/2 text-slate-400 pointer-events-none">
              <i class="fa-solid fa-chevron-down text-xs"></i>
            </div>
          </div>
        </div>

        <!-- 4. Comments -->
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Clinical Notes (Optional)</label>
          <textarea v-model="feedback.comments" rows="3" class="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-white focus:border-blue-500 outline-none resize-none placeholder-slate-600" placeholder="Add clinical observations..."></textarea>
        </div>

        <!-- Submit -->
        <button 
          @click="submitFeedback"
          :disabled="submittingFeedback"
          class="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 disabled:from-slate-700 disabled:to-slate-800 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-900/20 active:scale-[0.98]"
        >
          <i v-if="submittingFeedback" class="fa-solid fa-circle-notch fa-spin mr-2"></i>
          <span v-else>SUBMIT FEEDBACK</span>
        </button>
      </div>
    </div>
    
    <div v-if="feedbackSubmitted" class="mt-6 bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-8 text-center animation-fade-in">
      <div class="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 shadow-[0_0_20px_rgba(16,185,129,0.2)]">
        <i class="fa-solid fa-check text-emerald-400 text-2xl"></i>
      </div>
      <h3 class="text-xl font-bold text-white mb-2">Feedback Recorded</h3>
      <p class="text-slate-400">Thank you. The model will be updated with this case in the next training cycle.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const API_URL = `http://${window.location.hostname}:8081`

const selectedFile = ref(null)
const preview = ref(null)
const prediction = ref(null)
const loadingPred = ref(false)
const showExplanation = ref(false)
const heatmapUrl = ref(null)

// Feedback State
const showFeedbackForm = ref(false)
const feedbackSubmitted = ref(false)
const submittingFeedback = ref(false)
const feedback = reactive({
  isCorrect: null,
  correctLabel: '',
  heatmapRating: 'accurate',
  comments: ''
})

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
    preview.value = URL.createObjectURL(file)
    prediction.value = null
    heatmapUrl.value = null
    showExplanation.value = false
    
    // Reset feedback
    showFeedbackForm.value = false
    feedbackSubmitted.value = false
    feedback.isCorrect = null
    feedback.correctLabel = ''
    feedback.heatmapRating = 'accurate'
    feedback.comments = ''
  }
}

const resetUpload = () => {
  selectedFile.value = null
  preview.value = null
  prediction.value = null
  loadingPred.value = false
  heatmapUrl.value = null
  showExplanation.value = false
  
  // Reset feedback
  showFeedbackForm.value = false
  feedbackSubmitted.value = false
  
  const input = document.getElementById('fileInput')
  if (input) input.value = ''
}

const runDiagnosis = async () => {
  if (!selectedFile.value) return
  loadingPred.value = true

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const res = await fetch(`${API_URL}/predict/explain`, {
      method: 'POST',
      body: formData
    })
    const data = await res.json()

    prediction.value = data

    if (data.heatmap_url) {
      heatmapUrl.value = `${API_URL}${data.heatmap_url}?t=${Date.now()}`
    }
    
    // Open feedback form automatically after result
    setTimeout(() => {
      showFeedbackForm.value = true
    }, 1500)
    
  } catch (e) {
    console.error('Error:', e)
    alert("Error running diagnosis. Is the server running?")
  }
  loadingPred.value = false
}

const submitFeedback = async () => {
  if (!selectedFile.value || !prediction.value) return
  
  // Default to prediction if not specified
  if (!feedback.correctLabel) {
    feedback.correctLabel = prediction.value.prediction
  }
  
  submittingFeedback.value = true
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('prediction', prediction.value.prediction)
  formData.append('correct_label', feedback.correctLabel)
  formData.append('heatmap_feedback', feedback.heatmapRating)
  formData.append('comments', feedback.comments)
  
  try {
    const res = await fetch(`${API_URL}/feedback`, {
      method: 'POST',
      body: formData
    })
    
    if (res.ok) {
      feedbackSubmitted.value = true
      showFeedbackForm.value = false
    } else {
      alert("Failed to submit feedback")
    }
  } catch (e) {
    console.error("Error submitting feedback:", e)
    alert("Error submitting feedback")
  }
  
  submittingFeedback.value = false
}
</script>
