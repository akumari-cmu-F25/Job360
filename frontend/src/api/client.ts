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

    // Start the upload
    const startResponse = await client.post('/api/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    if (!startResponse.data.success) {
      return startResponse.data
    }

    const uploadId = startResponse.data.upload_id

    // Poll for the result
    const maxAttempts = 300 // 5 minutes with 1 second intervals
    let attempts = 0

    while (attempts < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, 1000)) // Wait 1 second

      const resultResponse = await client.get(`/api/resume/upload/${uploadId}`)
      const result = resultResponse.data

      if (result.success !== false || result.status !== 'processing') {
        return result
      }

      attempts++
    }

    return {
      success: false,
      error: 'Resume upload timeout',
    }
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
    // Start the job processing
    const startResponse = await client.post('/api/jobs/apply', {
      job_id: job.id || job.url,
      job_url: job.url,
      job_description: job.description || '', // Always include description
      profile_data: profile,
      job: job, // Include full job object for fallback
    })

    if (!startResponse.data.success) {
      return startResponse.data
    }

    const jobId = startResponse.data.job_id

    // Poll for the result
    const maxAttempts = 300 // 5 minutes with 1 second intervals
    let attempts = 0

    while (attempts < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, 1000)) // Wait 1 second

      const resultResponse = await client.get(`/api/jobs/apply/${jobId}`)
      const result = resultResponse.data

      if (result.success !== false || result.status !== 'processing') {
        return result
      }

      attempts++
    }

    return {
      success: false,
      error: 'Job processing timeout',
    }
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
  generateLinkedInMessage: async (job: any, profile: any, tone: string, customRequirements?: string) => {
    const response = await client.post('/api/linkedin/generate-message', {
      job,
      profile,
      tone,
      custom_requirements: customRequirements || '',
    })
    return response.data
  },

  // LinkedIn employee list
  getCompanyEmployees: async (companyName: string, companyLinkedInUrl?: string) => {
    const response = await client.post('/api/linkedin/employees', {
      company_name: companyName,
      company_linkedin_url: companyLinkedInUrl,
    })
    return response.data
  },

  // Job description fetch (URL pre-fetch before queuing)
  fetchJD: async (url: string) => {
    const response = await client.post('/api/jd/fetch', { url })
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
