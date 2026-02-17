import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Resume operations
  uploadResume: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await client.post('/api/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  exportResume: async (profile: any) => {
    const response = await client.post('/api/resume/export', profile)
    return response.data
  },

  // Job operations
  searchJobs: async (category: string, location?: string, hoursAgo: number = 36) => {
    const response = await client.post('/api/jobs/search', {
      category,
      location,
      hours_ago: hoursAgo,
    })
    return response.data
  },

  applyToJob: async (job: any, profile: any) => {
    const response = await client.post('/api/jobs/apply', {
      job_id: job.id || job.url,
      job_url: job.url,
      job_description: job.description || '', // Always include description
      profile_data: profile,
      job: job, // Include full job object for fallback
    })
    return response.data
  },

  // Voice operations
  processVoiceInstruction: async (text?: string, audioUrl?: string) => {
    const response = await client.post('/api/voice/process', {
      text,
      audio_url: audioUrl,
    })
    return response.data
  },

  // LinkedIn referral message
  generateLinkedInMessage: async (job: any, profile: any, tone: string) => {
    const response = await client.post('/api/linkedin/generate-message', {
      job,
      profile,
      tone,
    })
    return response.data
  },

  // Interview prep
  generateInterviewPrep: async (job: any) => {
    const response = await client.post('/api/interview/prep-plan', {
      job,
    })
    return response.data
  },
}

export default api
