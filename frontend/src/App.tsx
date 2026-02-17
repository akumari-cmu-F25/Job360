import { useState, useEffect } from 'react'
import './App.css'
import LeftPanel from './components/LeftPanel'
import RightPanel from './components/RightPanel'
import Dashboard from './components/Dashboard'
import LinkedInReferral from './components/LinkedInReferral'
import InterviewPrep from './components/InterviewPrep'
import { Profile, Job } from './types'

type View = 'editor' | 'dashboard'

function App() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [originalProfile, setOriginalProfile] = useState<Profile | null>(null)
  const [editedProfile, setEditedProfile] = useState<Profile | null>(null)
  const [jobQueue, setJobQueue] = useState<Job[]>([])
  const [currentJobIndex, setCurrentJobIndex] = useState<number>(-1)
  const [jobListings, setJobListings] = useState<Job[]>([])
  const [currentView, setCurrentView] = useState<View>('dashboard')
  const [selectedJobForLinkedIn, setSelectedJobForLinkedIn] = useState<Job | null>(null)
  const [selectedJobForPrep, setSelectedJobForPrep] = useState<Job | null>(null)

  // Load sample resume and jobs on mount
  useEffect(() => {
    const loadSampleData = async () => {
      try {
        // Load sample resume
        const response = await fetch('/sample_resume.json')
        const resumeData = await response.json()
        const sampleProfile: Profile = resumeData
        
        setProfile(sampleProfile)
        setOriginalProfile(sampleProfile)
        setEditedProfile(sampleProfile)

        // Add sample jobs
        const sampleJobs: Job[] = [
          {
            title: 'Senior Software Engineer',
            company: 'Google',
            location: 'Mountain View, CA',
            url: 'https://careers.google.com/jobs/',
            status: 'queued',
            description: 'We are looking for a Senior Software Engineer to join our Cloud Infrastructure team...'
          },
          {
            title: 'Full Stack Engineer',
            company: 'Meta',
            location: 'Menlo Park, CA',
            url: 'https://www.metacareers.com/jobs/',
            status: 'queued',
            description: 'Join our team building next-generation social experiences...'
          },
          {
            title: 'Machine Learning Engineer',
            company: 'OpenAI',
            location: 'San Francisco, CA',
            url: 'https://openai.com/careers/',
            status: 'completed',
            description: 'Work on cutting-edge AI systems and large language models...'
          },
          {
            title: 'Software Development Engineer',
            company: 'Amazon',
            location: 'Seattle, WA',
            url: 'https://www.amazon.jobs/',
            status: 'queued',
            description: 'Build scalable distributed systems for millions of customers...'
          }
        ]
        
        setJobQueue(sampleJobs)
      } catch (error) {
        console.error('Error loading sample data:', error)
      }
    }

    loadSampleData()
  }, [])

  const handleEditResume = (job: Job) => {
    const jobIndex = jobQueue.findIndex(j => j.url === job.url)
    if (jobIndex >= 0) {
      setCurrentJobIndex(jobIndex)
      if (job.edited_profile) {
        setEditedProfile(job.edited_profile)
      }
      setCurrentView('editor')
    }
  }

  return (
    <div className="app-container">
      <div className="app-header">
        <h1 className="app-title">Job360</h1>
        <div className="view-toggle">
          <button
            className={`view-btn ${currentView === 'editor' ? 'active' : ''}`}
            onClick={() => setCurrentView('editor')}
          >
            Resume Editor
          </button>
          <button
            className={`view-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            Dashboard
          </button>
        </div>
      </div>

      {currentView === 'editor' ? (
        <div className="editor-view">
          <LeftPanel
            profile={profile}
            originalProfile={originalProfile}
            onProfileUploaded={(p) => {
              setProfile(p)
              setOriginalProfile(p)
              setEditedProfile(p)
            }}
            jobListings={jobListings}
            onJobListingsChange={setJobListings}
            jobQueue={jobQueue}
            onJobQueueChange={setJobQueue}
            currentJobIndex={currentJobIndex}
            onCurrentJobIndexChange={setCurrentJobIndex}
            onResumeEdited={setEditedProfile}
          />
          <RightPanel
            profile={editedProfile || profile}
            originalProfile={originalProfile}
            currentJob={currentJobIndex >= 0 ? jobQueue[currentJobIndex] : null}
          />
        </div>
      ) : (
        <Dashboard
          jobQueue={jobQueue}
          profile={profile}
          onEditResume={handleEditResume}
          onInterviewPrep={(job) => setSelectedJobForPrep(job)}
          onLinkedInReferral={(job) => setSelectedJobForLinkedIn(job)}
        />
      )}

      {selectedJobForLinkedIn && profile && (
        <LinkedInReferral
          job={selectedJobForLinkedIn}
          profile={profile}
          onClose={() => setSelectedJobForLinkedIn(null)}
        />
      )}

      {selectedJobForPrep && (
        <InterviewPrep
          job={selectedJobForPrep}
          onClose={() => setSelectedJobForPrep(null)}
        />
      )}
    </div>
  )
}

export default App
