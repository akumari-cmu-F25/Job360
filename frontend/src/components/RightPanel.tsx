import { Profile, Job } from '../types'
import { api } from '../api/client'
import './RightPanel.css'

interface RightPanelProps {
  profile: Profile | null
  originalProfile: Profile | null
  currentJob: Job | null
}

export default function RightPanel({
  profile,
  originalProfile,
  currentJob,
}: RightPanelProps) {
  const handleDownload = async () => {
    if (!profile) return
    
    try {
      const result = await api.exportResume(profile)
      // Convert hex to blob and download
      const hex = result.file
      const bytes = new Uint8Array(hex.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16)))
      const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const filename = currentJob 
        ? `resume_${currentJob.company?.replace(/\s+/g, '_')}_${Date.now()}.docx`
        : `resume_${Date.now()}.docx`
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading resume:', error)
    }
  }

  if (!profile) {
    return (
      <div className="right-panel">
        <div className="resume-preview">
          <div className="empty-state">
            <div>Upload resume to view</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="right-panel">
      <div className="section-title">Resume Preview</div>
      
      {currentJob && (
        <div className={`current-job-info ${currentJob.status === 'processing' ? 'processing' : currentJob.status === 'completed' ? 'completed' : ''}`}>
          {currentJob.status === 'processing' ? 'Processing' : currentJob.status === 'completed' ? 'Completed' : 'Ready'}: {currentJob.title} at {currentJob.company}
        </div>
      )}

      <div className="resume-preview">
        <ResumeContent profile={profile} originalProfile={originalProfile} />
      </div>

      {currentJob && currentJob.status === 'completed' && (
        <div className="action-buttons">
          <button onClick={handleDownload} className="download-button">
            Download
          </button>
        </div>
      )}
    </div>
  )
}

function ResumeContent({ profile, originalProfile }: { profile: Profile; originalProfile: Profile | null }) {
  const isChanged = (field: string, value: any) => {
    if (!originalProfile) return false
    return (originalProfile as any)[field] !== value
  }
  
  const isBulletChanged = (expIndex: number, bulletIndex: number, bullet: string) => {
    if (!originalProfile || !originalProfile.experiences || expIndex >= originalProfile.experiences.length) {
      return false
    }
    const origExp = originalProfile.experiences[expIndex]
    if (!origExp.bullets || bulletIndex >= origExp.bullets.length) {
      return true // New bullet
    }
    return origExp.bullets[bulletIndex] !== bullet
  }

  return (
    <div className="resume-content">
      {/* Header */}
      <div className="resume-header">
        <h1>{profile.name || 'Your Name'}</h1>
        <div className="contact-info">
          {profile.email && <span>{profile.email}</span>}
          {profile.phone && <span> • {profile.phone}</span>}
          {profile.location && <span> • {profile.location}</span>}
        </div>
      </div>

      {/* Summary */}
      {profile.summary && (
        <div className="resume-section">
          <h2>Professional Summary</h2>
          <p className={isChanged('summary', profile.summary) ? 'edit-highlight' : ''}>
            {profile.summary}
          </p>
        </div>
      )}

      {/* Experience */}
      {profile.experiences && profile.experiences.length > 0 && (
        <div className="resume-section">
          <h2>Experience</h2>
          {profile.experiences.map((exp, i) => (
            <div key={i} className="experience-item">
              <div className="experience-header">
                <strong>{exp.title}</strong>
                <span>{exp.start_date || ''} - {exp.end_date || 'Present'}</span>
              </div>
              <div className="experience-company">{exp.company}{exp.location && `, ${exp.location}`}</div>
              {exp.bullets && (
                <ul>
                  {exp.bullets.map((bullet, j) => {
                    const changed = isBulletChanged(i, j, bullet)
                    return (
                      <li key={j} className={changed ? 'edit-highlight' : ''}>
                        {bullet}
                      </li>
                    )
                  })}
                </ul>
              )}
              {exp.technologies && exp.technologies.length > 0 && (
                <div className="technologies">
                  <strong>Technologies:</strong> {exp.technologies.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Education */}
      {profile.education && profile.education.length > 0 && (
        <div className="resume-section">
          <h2>Education</h2>
          {profile.education.map((edu, i) => (
            <div key={i} className="education-item">
              <strong>{edu.degree}{edu.field_of_study && ` in ${edu.field_of_study}`}</strong>
              <div>{edu.institution}{edu.location && `, ${edu.location}`}</div>
            </div>
          ))}
        </div>
      )}

      {/* Skills */}
      {profile.skills && profile.skills.length > 0 && (
        <div className="resume-section">
          <h2>Skills</h2>
          <div className="skills-list">
            {profile.skills.map((skill, i) => {
              const isNew = originalProfile 
                ? !originalProfile.skills?.some(s => s.name.toLowerCase() === skill.name.toLowerCase())
                : false
              return (
                <span key={i} className={`skill-item ${isNew ? 'edit-highlight' : ''}`}>
                  {skill.name}
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* Projects */}
      {profile.projects && profile.projects.length > 0 && (
        <div className="resume-section">
          <h2>Projects</h2>
          {profile.projects.map((proj, i) => {
            const origProj = originalProfile?.projects?.[i]
            const descChanged = origProj?.description !== proj.description
            return (
              <div key={i} className="project-item">
                <strong>{proj.name}</strong>
                {proj.description && (
                  <div className={descChanged ? 'edit-highlight' : ''}>{proj.description}</div>
                )}
                {proj.bullets && (
                  <ul>
                    {proj.bullets.map((bullet, j) => {
                      const bulletChanged = !origProj?.bullets?.[j] || origProj.bullets[j] !== bullet
                      return (
                        <li key={j} className={bulletChanged ? 'edit-highlight' : ''}>{bullet}</li>
                      )
                    })}
                  </ul>
                )}
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="technologies">
                    Technologies: {proj.technologies.join(', ')}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
