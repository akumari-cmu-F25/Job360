import { useState } from 'react'
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
}: LeftPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [jdUrl, setJdUrl] = useState<string>('')
  const [inputMode, setInputMode] = useState<'search' | 'url'>('search')
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [activeTab, setActiveTab] = useState<'upload' | 'search' | 'queue'>('upload')
  const [isProcessing, setIsProcessing] = useState(false)
  const [resumeFileName, setResumeFileName] = useState<string>('')

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

  const handleAddUrlToQueue = () => {
    if (!jdUrl.trim()) return

    const job: Job = {
      title: 'Job from URL',
      company: 'Unknown',
      url: jdUrl.trim(),
      status: 'queued',
    }

    const jobWithId = { ...job, id: generateJobId(job) }

    if (!jobQueue.find((j) => j.id === jobWithId.id)) {
      onJobQueueChange([...jobQueue, jobWithId])
      setJdUrl('')
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

    setIsProcessing(true)
    onCurrentJobIndexChange(0)
    processNextJobById(jobQueue.map((j) => j.id!).filter((id) => id))
  }

  const processNextJobById = async (jobIds: string[]) => {
    if (jobIds.length === 0) {
      // All jobs processed, reset current job index and processing flag
      onCurrentJobIndexChange(-1)
      setIsProcessing(false)
      return
    }

    const jobIdToProcess = jobIds[0]
    const currentQueue = jobQueue
    const jobIndex = currentQueue.findIndex((j) => j.id === jobIdToProcess)

    // Job was removed from queue, skip it
    if (jobIndex === -1) {
      processNextJobById(jobIds.slice(1))
      return
    }

    const job = currentQueue[jobIndex]
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
          processNextJobById(jobIds.slice(1))
        }, 2000)
      } else {
        updatedQueue[jobIndex] = { ...job, status: 'error' }
        onJobQueueChange(updatedQueue)
        // Continue to next job even if this one failed
        setTimeout(() => {
          processNextJobById(jobIds.slice(1))
        }, 1000)
      }
    } catch (error) {
      console.error('Error processing job:', error)
      updatedQueue[jobIndex] = { ...job, status: 'error' }
      onJobQueueChange(updatedQueue)
      // Continue to next job even if this one failed
      setTimeout(() => {
        processNextJobById(jobIds.slice(1))
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
                  disabled={!jdUrl.trim()}
                  className="add-url-button"
                >
                  Add to Queue
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
                        <div className="queue-status">
                          {job.status || 'queued'}
                          {index === currentJobIndex && job.status === 'processing' && (
                            <span className="processing-indicator"> Processing...</span>
                          )}
                        </div>
                      </div>
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
