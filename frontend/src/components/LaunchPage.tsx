import { useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Profile } from '../types'
import { api } from '../api/client'
import './LaunchPage.css'

interface LaunchPageProps {
  onStartSearch: (profile: Profile, category: string) => void
  existingProfile?: Profile | null
}

const JOB_CATEGORIES = ['ML', 'SWE', 'SDE', 'Product', 'Data Analytics', 'Data', 'AI']

export default function LaunchPage({ onStartSearch, existingProfile }: LaunchPageProps) {
  const [profile, setProfile] = useState<Profile | null>(existingProfile || null)
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [resumeFileName, setResumeFileName] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (existingProfile && !resumeFileName) {
      setResumeFileName('Resume uploaded')
    }
  }, [existingProfile, resumeFileName])

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
        setError('')
        try {
          const result = await api.uploadResume(file)
          if (result.success) {
            setProfile(result.profile)
          } else {
            setError('Failed to upload resume. Please try again.')
            setResumeFileName('')
          }
        } catch (err) {
          setError('Error uploading resume. Please try again.')
          setResumeFileName('')
        } finally {
          setLoading(false)
        }
      }
    },
  })

  const handleStartSearch = () => {
    if (!profile || !selectedCategory) {
      setError('Please upload a resume and select a job category.')
      return
    }
    onStartSearch(profile, selectedCategory)
  }

  const isReady = profile !== null && selectedCategory !== ''

  return (
    <div className="launch-page">
      <div className="launch-header">
        <h1 className="launch-title">Job360</h1>
        <p className="launch-subtitle">Tailor your resume to any job in seconds</p>
      </div>

      <div className="launch-content">
        {/* Resume Upload Section */}
        <div className="upload-section">
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'active' : ''} ${profile ? 'uploaded' : ''}`}
          >
            <input {...getInputProps()} />
            {loading ? (
              <div className="dropzone-content">
                <div className="spinner"></div>
                <p>Processing your resume...</p>
              </div>
            ) : profile ? (
              <div className="dropzone-content">
                <div className="checkmark">✓</div>
                <p className="file-name">{resumeFileName}</p>
                <p className="upload-hint">Click to change resume</p>
              </div>
            ) : (
              <div className="dropzone-content">
                <div className="upload-icon">📄</div>
                <p className="upload-text">
                  {isDragActive ? 'Drop your resume here' : 'Upload your resume'}
                </p>
                <p className="upload-hint">PDF, DOCX, or DOC • Max 10MB</p>
              </div>
            )}
          </div>
        </div>

        {/* Job Category Selection */}
        <div className="category-section">
          <label htmlFor="category-select" className="category-label">
            Select Job Category
          </label>
          <select
            id="category-select"
            className="category-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">Choose a category...</option>
            {JOB_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        {/* Error Message */}
        {error && <div className="error-message">{error}</div>}

        {/* Start Searching Button */}
        <button
          className={`start-btn ${isReady ? 'ready' : 'disabled'}`}
          onClick={handleStartSearch}
          disabled={!isReady || loading}
        >
          {loading ? 'Processing...' : 'Start Searching'}
        </button>
      </div>
    </div>
  )
}
