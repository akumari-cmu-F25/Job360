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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setLoading(true)
        try {
          const result = await api.uploadResume(acceptedFiles[0])
          if (result.success) {
            onProfileUploaded(result.profile)
          }
        } catch (error) {
          console.error('Error uploading resume:', error)
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
        onJobListingsChange(result.jobs)
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
    
    if (!jobQueue.find(j => j.url === job.url)) {
      onJobQueueChange([...jobQueue, job])
      setJdUrl('')
    }
  }

  const handleAddToQueue = (job: Job) => {
    if (!jobQueue.find(j => j.url === job.url)) {
      onJobQueueChange([...jobQueue, { ...job, status: 'queued' }])
    }
  }

  const handleApplyToAll = async () => {
    if (jobQueue.length === 0 || !profile) return
    
    onCurrentJobIndexChange(0)
    await processNextJob(0)
  }

  const processNextJob = async (index: number) => {
    if (index >= jobQueue.length) return

    const job = jobQueue[index]
    const updatedQueue = [...jobQueue]
    updatedQueue[index] = { ...job, status: 'processing' }
    onJobQueueChange(updatedQueue)
    onCurrentJobIndexChange(index)

    try {
      const result = await api.applyToJob(job, profile!)
      if (result.success) {
        updatedQueue[index] = {
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
          processNextJob(index + 1)
        }, 2000)
      } else {
        updatedQueue[index] = { ...job, status: 'error' }
        onJobQueueChange(updatedQueue)
        // Continue to next job even if this one failed
        setTimeout(() => {
          processNextJob(index + 1)
        }, 1000)
      }
    } catch (error) {
      console.error('Error processing job:', error)
      updatedQueue[index] = { ...job, status: 'error' }
      onJobQueueChange(updatedQueue)
      // Continue to next job even if this one failed
      setTimeout(() => {
        processNextJob(index + 1)
      }, 1000)
    }
  }

  return (
    <div className="left-panel">
      <div className="section">
        <div className="section-title">Upload Resume</div>
        <div
          {...getRootProps()}
          className={`upload-zone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          {loading ? (
            <div>Processing...</div>
          ) : profile ? (
            <div className="upload-text">Resume loaded</div>
          ) : (
            <>
              <div className="upload-text">Drop resume here</div>
              <div className="upload-hint">PDF or DOCX</div>
            </>
          )}
        </div>
      </div>

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
      </div>

      {jobListings.length > 0 && (
        <div className="section">
          <div className="section-title">
            Results ({jobListings.length})
          </div>
          <div className="job-list">
            {jobListings.map((job, index) => (
              <div key={index} className="job-card">
                <div className="job-title">{job.title}</div>
                <div className="job-company">{job.company}</div>
                <div className="job-meta">
                  <span>{job.location || 'Remote'}</span>
                  <span>{job.source || ''}</span>
                </div>
                <button
                  onClick={() => handleAddToQueue(job)}
                  className="add-button"
                >
                  Add to Queue
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {jobQueue.length > 0 && (
        <div className="section">
          <div className="section-title">Queue ({jobQueue.length})</div>
          <div className="queue-list">
            {jobQueue.map((job, index) => (
              <div
                key={index}
                className={`queue-item ${job.status || 'queued'} ${index === currentJobIndex ? 'current' : ''}`}
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
            ))}
          </div>
          <button
            onClick={handleApplyToAll}
            disabled={!profile || currentJobIndex >= 0}
            className="apply-button"
          >
            {currentJobIndex >= 0 ? 'Processing...' : 'Apply to All'}
          </button>
        </div>
      )}
    </div>
  )
}
