import { useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Profile, Job } from '../types'
import { api } from '../api/client'
import './LeftPanel.css'

interface LeftPanelProps {
  profile: Profile | null
  originalProfile: Profile | null
  onProfileUploaded: (profile: Profile) => void
  jobListings: Job[]
  onJobListingsChange: (jobs: Job[]) => void
  jobQueue: Job[]
  onJobQueueChange: (jobs: Job[]) => void
  currentJobIndex: number
  onCurrentJobIndexChange: (index: number) => void
  onResumeEdited: (profile: Profile) => void
  initialCategory?: string
  onInitialCategoryUsed?: () => void
}

const categories = ['ML', 'SWE', 'SDE', 'Product', 'Data Analytics', 'Data', 'AI']

// Generate a stable ID for a job based on its properties
const generateJobId = (job: Job): string => {
  if (job.id) return job.id
  // Include title, company, location, source, AND URL to ensure uniqueness
  // This prevents collisions when the same URL has different job titles
  const identifier = `${job.url || ''}|${job.title}|${job.company}|${job.location || ''}|${job.source || ''}`
  // Use btoa (base64) for a more unique encoding
  const encoded = btoa(identifier)
  // Take the full base64 string without truncation to avoid collisions
  return `job_${encoded.replace(/[^a-zA-Z0-9]/g, '')}`
}

export default function LeftPanel({
  profile,
  onProfileUploaded,
  jobListings,
  onJobListingsChange,
  jobQueue,
  onJobQueueChange,
  currentJobIndex,
  onCurrentJobIndexChange,
  onResumeEdited,
  initialCategory = '',
  onInitialCategoryUsed,
}: LeftPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [jdUrl, setJdUrl] = useState<string>('')
  const [inputMode, setInputMode] = useState<'search' | 'url'>('search')
  const [loading, setLoading] = useState(false)
  const [urlLoading, setUrlLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [activeTab, setActiveTab] = useState<'upload' | 'search' | 'queue'>('upload')
  const [isProcessing, setIsProcessing] = useState(false)
  const [resumeFileName, setResumeFileName] = useState<string>('')

  // Auto-search when initialCategory is provided from launch page
  useEffect(() => {
    if (initialCategory && !searching && selectedCategory === '') {
      setSelectedCategory(initialCategory)
      setActiveTab('search')
      onInitialCategoryUsed?.()
    }
  }, [initialCategory, onInitialCategoryUsed, searching, selectedCategory])

  // Trigger search when selectedCategory is set from initialCategory
  useEffect(() => {
    if (selectedCategory && activeTab === 'search' && !searching && jobListings.length === 0) {
      handleSearchJobs()
    }
  }, [selectedCategory, activeTab, searching, jobListings.length])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        setResumeFileName(file.name)
        setLoading(true)
        try {
          const result = await api.uploadResume(file)
          if (result.success) {
            onProfileUploaded(result.profile)
          }
        } catch (error) {
          console.error('Error uploading resume:', error)
          setResumeFileName('')
        } finally {
          setLoading(false)
        }
      }
    },
  })

  const handleSearchJobs = async () => {
    if (!selectedCategory) return
    setSearching(true)
    try {
      const result = await api.searchJobs(selectedCategory, undefined, 36)
      if (result.success) {
        // Assign stable IDs to jobs
        const jobsWithIds = result.jobs.map((job: Job) => ({
          ...job,
          id: generateJobId(job),
        }))
        onJobListingsChange(jobsWithIds)
      }
    } catch (error) {
      console.error('Error searching jobs:', error)
    } finally {
      setSearching(false)
    }
  }

  const handleAddUrlToQueue = async () => {
    if (!jdUrl.trim()) return
    setUrlLoading(true)
    try {
      const result = await api.fetchJD(jdUrl.trim())
      const job: Job = {
        title: result.title || 'Job from URL',
        company: result.company || 'Unknown',
        url: jdUrl.trim(),
        description: result.full_description,
        status: 'queued',
      }
      const jobWithId = { ...job, id: generateJobId(job) }
      if (!jobQueue.find((j) => j.id === jobWithId.id)) {
        onJobQueueChange([...jobQueue, jobWithId])
        setJdUrl('')
      }
    } catch {
      alert('Could not fetch job from URL. Try pasting the description directly.')
    } finally {
      setUrlLoading(false)
    }
  }

  const handleAddToQueue = (job: Job) => {
    const isInQueue = jobQueue.some((j) => j.id === job.id)

    if (isInQueue) {
      // Remove from queue
      const updatedQueue = jobQueue.filter((j) => j.id !== job.id)
      onJobQueueChange(updatedQueue)
    } else {
      // Add to queue
      if (!jobQueue.find((j) => j.id === job.id)) {
        onJobQueueChange([...jobQueue, { ...job, status: 'queued' }])
      }
    }
  }

  const handleApplyToAll = async () => {
    if (jobQueue.length === 0 || !profile) return

    // Filter to only process queued jobs, skip completed ones
    const queuedJobs = jobQueue.filter((job) => job.status === 'queued' || !job.status)
    if (queuedJobs.length === 0) return

    setIsProcessing(true)
    // Find the index of the first queued job
    const firstQueuedIndex = jobQueue.findIndex((job) => job.status === 'queued' || !job.status)
    onCurrentJobIndexChange(firstQueuedIndex)
    processNextJob(jobQueue, firstQueuedIndex)
  }

  const processNextJob = async (currentQueue: Job[], jobIndex: number) => {
    if (jobIndex >= currentQueue.length) {
      // All jobs processed, reset current job index and processing flag
      onCurrentJobIndexChange(-1)
      setIsProcessing(false)
      return
    }

    const job = currentQueue[jobIndex]

    // Skip completed jobs, move to next
    if (job.status === 'completed') {
      setTimeout(() => {
        processNextJob(currentQueue, jobIndex + 1)
      }, 0)
      return
    }

    const updatedQueue = [...currentQueue]
    updatedQueue[jobIndex] = { ...job, status: 'processing' }
    onJobQueueChange(updatedQueue)
    onCurrentJobIndexChange(jobIndex)

    try {
      const result = await api.applyToJob(job, profile!)
      if (result.success) {
        updatedQueue[jobIndex] = {
          ...job,
          status: 'completed',
          edited_profile: result.edited_profile,
          title: result.jd_analysis?.title || job.title,
          company: result.jd_analysis?.company || job.company,
        }
        onJobQueueChange(updatedQueue)
        onResumeEdited(result.edited_profile)

        // Process next job after a short delay
        setTimeout(() => {
          processNextJob(updatedQueue, jobIndex + 1)
        }, 2000)
      } else {
        updatedQueue[jobIndex] = { ...job, status: 'error' }
        onJobQueueChange(updatedQueue)
        // Continue to next job even if this one failed
        setTimeout(() => {
          processNextJob(updatedQueue, jobIndex + 1)
        }, 1000)
      }
    } catch (error) {
      console.error('Error processing job:', error)
      updatedQueue[jobIndex] = { ...job, status: 'error' }
      onJobQueueChange(updatedQueue)
      // Continue to next job even if this one failed
      setTimeout(() => {
        processNextJob(updatedQueue, jobIndex + 1)
      }, 1000)
    }
  }

  return (
    <div className="left-panel">
      <div className="tabs-container">
        <button
          className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload
        </button>
        <button
          className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          Search
        </button>
        <button
          className={`tab-btn ${activeTab === 'queue' ? 'active' : ''}`}
          onClick={() => setActiveTab('queue')}
        >
          Queue {jobQueue.length > 0 && <span className="queue-badge">{jobQueue.length}</span>}
        </button>
      </div>

      <div className="tabs-content">
        {activeTab === 'upload' && (
          <div className="section">
            <div className="section-title">Upload Resume</div>
            <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'active' : ''}`}>
              <input {...getInputProps()} />
              {loading ? (
                <div className="upload-text">{resumeFileName} uploading...</div>
              ) : profile ? (
                <div className="upload-text">✓ {resumeFileName || 'Resume'} uploaded</div>
              ) : (
                <>
                  <div className="upload-text">Drop resume here</div>
                  <div className="upload-hint">PDF or DOCX</div>
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <div className="section">
            <div className="section-title">Job Application</div>

            <div className="mode-toggle">
              <button
                className={`mode-btn ${inputMode === 'search' ? 'active' : ''}`}
                onClick={() => setInputMode('search')}
              >
                Search
              </button>
              <button
                className={`mode-btn ${inputMode === 'url' ? 'active' : ''}`}
                onClick={() => setInputMode('url')}
              >
                URL
              </button>
            </div>

            {inputMode === 'search' && (
              <div className="search-mode">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="category-select"
                >
                  <option value="">Select category</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleSearchJobs}
                  disabled={!selectedCategory || searching}
                  className="search-button"
                >
                  {searching ? 'Searching...' : 'Search'}
                </button>
              </div>
            )}

            {inputMode === 'url' && (
              <div className="url-mode">
                <input
                  type="text"
                  value={jdUrl}
                  onChange={(e) => setJdUrl(e.target.value)}
                  placeholder="Job description URL"
                  className="url-input"
                />
                <button
                  onClick={handleAddUrlToQueue}
                  disabled={!jdUrl.trim() || urlLoading}
                  className="add-url-button"
                >
                  {urlLoading ? 'Fetching...' : 'Add to Queue'}
                </button>
              </div>
            )}

            {jobListings.length > 0 && (
              <div className="results-section">
                <div className="section-title">Results ({jobListings.length})</div>
                <div className="job-list">
                  {jobListings.map((job, index) => {
                    const queuedJob = jobQueue.find((j) => j.id === job.id)
                    const isInQueue = !!queuedJob
                    return (
                      <div key={index} className="job-card">
                        <div className="job-title">{job.title}</div>
                        <div className="job-company">{job.company}</div>
                        <div className="job-meta">
                          <span>{job.location || 'Remote'}</span>
                          <span>{job.source || ''}</span>
                        </div>
                        {isInQueue ? (
                          <div className="job-status-display">
                            <span className={`status-badge ${queuedJob?.status || 'queued'}`}>
                              {queuedJob?.status || 'queued'}
                            </span>
                            <button
                              onClick={() => handleAddToQueue(job)}
                              className="remove-button"
                              title="Remove from queue"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <button onClick={() => handleAddToQueue(job)} className="add-button">
                            Add to Queue
                          </button>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'queue' && (
          <div className="section">
            <div className="section-title">Job Queue</div>
            {jobQueue.length === 0 ? (
              <div className="empty-queue">
                <p>No jobs in queue yet</p>
                <p className="empty-hint">Search or add jobs to get started</p>
              </div>
            ) : (
              <>
                <div className="queue-list">
                  {jobQueue.map((job, index) => (
                    <div
                      key={index}
                      className={`queue-item ${job.status || 'queued'} ${index === currentJobIndex ? 'current' : ''}`}
                    >
                      <div className="queue-item-status-icon">
                        {job.status === 'processing' && (
                          <div className="spinner-icon" title="Processing...">
                            ⏳
                          </div>
                        )}
                        {job.status === 'completed' && (
                          <div className="checkmark-icon" title="Completed">
                            ✓
                          </div>
                        )}
                        {job.status === 'error' && (
                          <div className="error-icon" title="Error">
                            ✕
                          </div>
                        )}
                        {(job.status === 'queued' || !job.status) && (
                          <div className="queued-icon" title="Queued">
                            ○
                          </div>
                        )}
                      </div>
                      <div
                        className="queue-item-content"
                        onClick={() => onCurrentJobIndexChange(index)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            onCurrentJobIndexChange(index)
                          }
                        }}
                      >
                        <div className="queue-job-title">{job.title}</div>
                        <div className="queue-job-company">{job.company}</div>
                        <div className="queue-job-status">
                          {job.status === 'processing'
                            ? 'Processing'
                            : job.status === 'completed'
                              ? 'Completed'
                              : job.status === 'error'
                                ? 'Error'
                                : 'Queued'}
                        </div>
                      </div>
                      <div className="queue-item-actions">
                        {job.status === 'error' && (
                          <button
                            className="queue-retry-btn"
                            onClick={(e) => {
                              e.stopPropagation()
                              const updatedQueue = [...jobQueue]
                              updatedQueue[index] = { ...job, status: 'queued' }
                              onJobQueueChange(updatedQueue)
                            }}
                            title="Retry processing this job"
                          >
                            ↻
                          </button>
                        )}
                        <button
                          className="queue-remove-btn"
                          onClick={(e) => {
                            e.stopPropagation()
                            const updatedQueue = jobQueue.filter((_, i) => i !== index)
                            onJobQueueChange(updatedQueue)
                            if (currentJobIndex === index) {
                              onCurrentJobIndexChange(-1)
                            }
                          }}
                          title="Remove from queue"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleApplyToAll}
                  disabled={!profile || isProcessing}
                  className="apply-button"
                >
                  {isProcessing ? 'Processing...' : 'Edit Resume for All'}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
