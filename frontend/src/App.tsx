import { useState } from 'react'
import './App.css'
import LeftPanel from './components/LeftPanel'
import RightPanel from './components/RightPanel'
import { Profile, Job } from './types'

function App() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [originalProfile, setOriginalProfile] = useState<Profile | null>(null)
  const [editedProfile, setEditedProfile] = useState<Profile | null>(null)
  const [jobQueue, setJobQueue] = useState<Job[]>([])
  const [currentJobIndex, setCurrentJobIndex] = useState<number>(-1)
  const [jobListings, setJobListings] = useState<Job[]>([])

  return (
    <div className="app-container">
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
  )
}

export default App
