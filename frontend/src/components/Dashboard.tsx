import { useState } from 'react'
import { Job, Profile } from '../types'
import './Dashboard.css'

interface DashboardProps {
  jobQueue: Job[]
  profile: Profile | null
  onEditResume: (job: Job) => void
  onInterviewPrep: (job: Job) => void
  onLinkedInReferral: (job: Job) => void
}

export default function Dashboard({
  jobQueue,
  profile,
  onEditResume,
  onInterviewPrep,
  onLinkedInReferral,
}: DashboardProps) {
  const [filter, setFilter] = useState<'all' | 'queued' | 'completed'>('all')

  const filteredJobs = jobQueue.filter(job => {
    if (filter === 'all') return true
    return job.status === filter
  })

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Job Dashboard</h1>
          <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem', margin: '0.5rem 0 0 0' }}>
            Track and manage your job applications
          </p>
        </div>
      </div>
      
      <div className="dashboard-stats-section">
        <div className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-number">{jobQueue.length}</div>
            <div className="stat-label">Total Jobs</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {jobQueue.filter(j => j.status === 'completed').length}
            </div>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {jobQueue.filter(j => j.status === 'queued').length}
            </div>
            <div className="stat-label">Pending</div>
          </div>
        </div>
      </div>

      <div className="filter-tabs">
        <button
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Jobs
        </button>
        <button
          className={`filter-tab ${filter === 'queued' ? 'active' : ''}`}
          onClick={() => setFilter('queued')}
        >
          Pending
        </button>
        <button
          className={`filter-tab ${filter === 'completed' ? 'active' : ''}`}
          onClick={() => setFilter('completed')}
        >
          Completed
        </button>
      </div>

      <div className="jobs-grid">
        {filteredJobs.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>💼</div>
            <p style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>No jobs in your queue yet</p>
            <p className="empty-hint">Switch to "Resume Editor" to upload your resume and add jobs to your queue</p>
          </div>
        ) : (
          filteredJobs.map((job, index) => (
            <div key={index} className="job-dashboard-card">
              <div className="job-card-header">
                <div>
                  <h3 className="job-card-title">{job.title}</h3>
                  <p className="job-card-company">{job.company}</p>
                  {job.location && (
                    <p className="job-card-location">{job.location}</p>
                  )}
                </div>
                <span className={`status-badge ${job.status || 'queued'}`}>
                  {job.status || 'queued'}
                </span>
              </div>

              <div className="job-card-actions">
                <button
                  className="action-btn primary"
                  onClick={() => onEditResume(job)}
                  disabled={!profile}
                  title="Tailor resume for this job"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  Edit Resume
                </button>

                <button
                  className="action-btn secondary"
                  onClick={() => onLinkedInReferral(job)}
                  disabled={!profile}
                  title="Generate LinkedIn referral message"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                    <rect x="2" y="9" width="4" height="12" />
                    <circle cx="4" cy="4" r="2" />
                  </svg>
                  LinkedIn Referral
                </button>

                <button
                  className="action-btn tertiary"
                  onClick={() => onInterviewPrep(job)}
                  title="Get interview preparation plan"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                  </svg>
                  Interview Prep
                </button>
              </div>

              {job.url && (
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="job-link"
                >
                  View Job Posting →
                </a>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
