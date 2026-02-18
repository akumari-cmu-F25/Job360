import { useState, useEffect } from 'react'
import { Job, Profile } from '../types'
import { api } from '../api/client'
import './LinkedInReferral.css'

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

  useEffect(() => {
    generateMessage()
  }, [tone])

  const generateMessage = async () => {
    setLoading(true)
    try {
      const result = await api.generateLinkedInMessage(job, profile, tone)
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
      </div>
    </div>
  )
}
