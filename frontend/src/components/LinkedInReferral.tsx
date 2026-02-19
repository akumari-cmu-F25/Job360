import { useState, useEffect } from 'react'
import { Job, Profile } from '../types'
import { api } from '../api/client'
import './LinkedInReferral.css'

interface Employee {
  name: string
  title: string
  avatar_url: string | null
  linkedin_url: string
}

interface LinkedInReferralProps {
  job: Job
  profile: Profile
  onClose: () => void
}

export default function LinkedInReferral({ job, profile, onClose }: LinkedInReferralProps) {
  const [message, setMessage] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [tone, setTone] = useState<'professional' | 'friendly' | 'concise'>('professional')
  const [copied, setCopied] = useState(false)
  const [customRequirements, setCustomRequirements] = useState<string>('')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [employeesLoading, setEmployeesLoading] = useState(false)

  useEffect(() => {
    generateMessage()
  }, [tone])

  useEffect(() => {
    if (!job.company) return
    setEmployeesLoading(true)
    api.getCompanyEmployees(job.company)
      .then((result) => {
        if (result.success) setEmployees(result.employees)
      })
      .catch(() => {/* silently hide section on error */})
      .finally(() => setEmployeesLoading(false))
  }, [job.company])

  const generateMessage = async () => {
    setLoading(true)
    try {
      const result = await api.generateLinkedInMessage(job, profile, tone, customRequirements)
      if (result.success) {
        setMessage(result.message)
      }
    } catch (error) {
      console.error('Error generating message:', error)
      setMessage(getDefaultMessage())
    } finally {
      setLoading(false)
    }
  }

  const getDefaultMessage = () => {
    return `Hi [Name],

I hope this message finds you well! I noticed that ${job.company} is hiring for the ${job.title} position, and I'm very excited about this opportunity.

With my background in ${profile.experiences[0]?.title || 'software development'} and experience with ${profile.skills
      .slice(0, 3)
      .map((s) => s.name)
      .join(', ')}, I believe I would be a great fit for this role.

I would greatly appreciate it if you could refer me for this position or connect me with the hiring manager. I've attached my resume and would be happy to discuss how my skills align with the team's needs.

Thank you for considering my request!

Best regards,
${profile.name || 'Your Name'}`
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(message)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRegenerate = () => {
    generateMessage()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>LinkedIn Referral Message</h2>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="job-info">
          <h3>{job.title}</h3>
          <p>{job.company}</p>
        </div>

        <div className="tone-selector">
          <label>Message Tone:</label>
          <div className="tone-buttons">
            <button
              className={`tone-btn ${tone === 'professional' ? 'active' : ''}`}
              onClick={() => setTone('professional')}
            >
              Professional
            </button>
            <button
              className={`tone-btn ${tone === 'friendly' ? 'active' : ''}`}
              onClick={() => setTone('friendly')}
            >
              Friendly
            </button>
            <button
              className={`tone-btn ${tone === 'concise' ? 'active' : ''}`}
              onClick={() => setTone('concise')}
            >
              Concise
            </button>
          </div>
        </div>

        <div className="requirements-bar">
          <label className="requirements-label">
            Custom Instructions
            <span className="requirements-optional">optional</span>
          </label>
          <div className="requirements-input-row">
            <textarea
              className="requirements-textarea"
              value={customRequirements}
              onChange={(e) => setCustomRequirements(e.target.value)}
              placeholder="e.g. mention I'm a recent grad, keep it under 80 words, highlight my internship at Google…"
              rows={2}
            />
            <button
              className="btn-apply"
              onClick={generateMessage}
              disabled={loading}
            >
              Apply
            </button>
          </div>
        </div>

        <div className="message-container">
          {loading ? (
            <div className="loading-state">Generating personalized message...</div>
          ) : (
            <textarea
              className="message-textarea"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={12}
            />
          )}
        </div>

        <div className="modal-actions">
          <button className="btn-secondary" onClick={handleRegenerate} disabled={loading}>
            Regenerate
          </button>
          <button className="btn-primary" onClick={handleCopy}>
            {copied ? 'Copied!' : 'Copy Message'}
          </button>
        </div>

        {(employeesLoading || employees.length > 0) && (
          <div className="employee-section">
            <div className="employee-section-title">People at {job.company}</div>
            {employeesLoading ? (
              <div className="employee-loading">Loading...</div>
            ) : (
              <div className="employee-list">
                {employees.map((emp, i) => (
                  <a
                    key={i}
                    href={emp.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="employee-card"
                    title={`${emp.name} – ${emp.title}`}
                  >
                    {emp.avatar_url ? (
                      <img src={emp.avatar_url} alt={emp.name} className="employee-avatar" />
                    ) : (
                      <div className="employee-avatar-placeholder">
                        {emp.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div className="employee-name">{emp.name.split(' ')[0]}</div>
                    <div className="employee-title">{emp.title}</div>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
