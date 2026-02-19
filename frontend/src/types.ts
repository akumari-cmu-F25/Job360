export interface Profile {
  name?: string
  email?: string
  phone?: string
  location?: string
  summary?: string
  experiences: Experience[]
  education: Education[]
  skills: Skill[]
  projects: Project[]
  certifications?: any[]
  awards?: any[]
  publications?: any[]
  languages?: any[]
  other_sections?: any[]
}

export interface Experience {
  title: string
  company: string
  location?: string
  start_date?: string
  end_date?: string
  bullets: string[]
  technologies: string[]
}

export interface Education {
  degree: string
  field_of_study?: string
  institution: string
  location?: string
  graduation_date?: string
  gpa?: string
}

export interface Skill {
  name: string
}

export interface Project {
  name: string
  description?: string
  bullets: string[]
  technologies: string[]
}

export interface Job {
  id?: string
  title: string
  company: string
  location?: string
  url?: string
  description?: string
  posted_date?: string
  source?: string
  status?: 'queued' | 'processing' | 'completed' | 'error'
  edited_profile?: Profile
  accepted?: boolean
}
