import { useState, useEffect } from 'react'
import './App.css'
import LeftPanel from './components/LeftPanel'
import RightPanel from './components/RightPanel'
import Dashboard from './components/Dashboard'
import LinkedInReferral from './components/LinkedInReferral'
import InterviewPrep from './components/InterviewPrep'
import LaunchPage from './components/LaunchPage'
import Job360Logo from './components/Job360Logo'
import { Profile, Job } from './types'

type View = 'launch' | 'editor' | 'dashboard'

function App() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [originalProfile, setOriginalProfile] = useState<Profile | null>(null)
  const [editedProfile, setEditedProfile] = useState<Profile | null>(null)
  const [jobQueue, setJobQueue] = useState<Job[]>([])
  const [currentJobIndex, setCurrentJobIndex] = useState<number>(-1)
  const [jobListings, setJobListings] = useState<Job[]>([])
  const [currentView, setCurrentView] = useState<View>('launch')
  const [selectedJobForLinkedIn, setSelectedJobForLinkedIn] = useState<Job | null>(null)
  const [selectedJobForPrep, setSelectedJobForPrep] = useState<Job | null>(null)
  const [initialCategory, setInitialCategory] = useState<string>('')

  const handleEditResume = (job: Job) => {
    const jobIndex = jobQueue.findIndex((j) => j.url === job.url)
    if (jobIndex >= 0) {
      // Reset job status to 'queued' so it can be re-processed
      const updatedQueue = [...jobQueue]
      updatedQueue[jobIndex] = { ...job, status: 'queued' }
      setJobQueue(updatedQueue)

      setCurrentJobIndex(jobIndex)
      if (job.edited_profile) {
        setEditedProfile(job.edited_profile)
      }
      setCurrentView('editor')
    }
  }

  const handleStartSearch = (uploadedProfile: Profile, category: string) => {
    setProfile(uploadedProfile)
    setOriginalProfile(uploadedProfile)
    setEditedProfile(uploadedProfile)
    setInitialCategory(category)
    setCurrentView('editor')
  }

  return (
    <div className="app-container">
      {currentView !== 'launch' && (
        <div className="app-header">
          <div
            className="app-title"
            onClick={() => setCurrentView('launch')}
            style={{ cursor: 'pointer' }}
          >
            <Job360Logo size="small" showText={true} variant="header" />
          </div>
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
      )}

      {currentView === 'launch' ? (
        <LaunchPage onStartSearch={handleStartSearch} existingProfile={profile} />
      ) : currentView === 'editor' ? (
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
            initialCategory={initialCategory}
            onInitialCategoryUsed={() => setInitialCategory('')}
          />
          <RightPanel
            profile={profile}
            originalProfile={originalProfile}
            currentJob={currentJobIndex >= 0 ? jobQueue[currentJobIndex] : null}
            jobQueue={jobQueue}
            onCurrentJobIndexChange={setCurrentJobIndex}
            onJobQueueChange={setJobQueue}
          />
        </div>
      ) : currentView === 'dashboard' ? (
        <Dashboard
          jobQueue={jobQueue}
          profile={profile}
          onEditResume={handleEditResume}
          onInterviewPrep={(job) => setSelectedJobForPrep(job)}
          onLinkedInReferral={(job) => setSelectedJobForLinkedIn(job)}
        />
      ) : null}

      {selectedJobForLinkedIn && profile && (
        <LinkedInReferral
          job={selectedJobForLinkedIn}
          profile={profile}
          onClose={() => setSelectedJobForLinkedIn(null)}
        />
      )}

      {selectedJobForPrep && (
        <InterviewPrep job={selectedJobForPrep} onClose={() => setSelectedJobForPrep(null)} />
      )}
    </div>
  )
}

export default App
