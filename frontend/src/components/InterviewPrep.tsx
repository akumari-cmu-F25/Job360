import { useState, useEffect } from 'react'
import { Job } from '../types'
import { api } from '../api/client'
import './InterviewPrep.css'

interface InterviewPrepProps {
  job: Job
  onClose: () => void
}

interface PrepPlan {
  leetcode_problems: Array<{
    title: string
    difficulty: 'Easy' | 'Medium' | 'Hard'
    topic: string
    url: string
    priority: 'High' | 'Medium' | 'Low'
  }>
  system_design_topics: Array<{
    title: string
    description: string
    resources: string[]
    estimatedTime: string
  }>
  behavioral_questions: string[]
  timeline: string
}

export default function InterviewPrep({ job, onClose }: InterviewPrepProps) {
  const [prepPlan, setPrepPlan] = useState<PrepPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'leetcode' | 'system-design' | 'behavioral'>(
    'leetcode'
  )

  useEffect(() => {
    generatePrepPlan()
  }, [])

  const generatePrepPlan = async () => {
    setLoading(true)
    try {
      const result = await api.generateInterviewPrep(job)
      if (result.success) {
        setPrepPlan(result.plan)
      }
    } catch (error) {
      console.error('Error generating prep plan:', error)
      setPrepPlan(getDefaultPrepPlan())
    } finally {
      setLoading(false)
    }
  }

  const getDefaultPrepPlan = (): PrepPlan => {
    return {
      leetcode_problems: [
        {
          title: 'Two Sum',
          difficulty: 'Easy',
          topic: 'Arrays & Hashing',
          url: 'https://leetcode.com/problems/two-sum/',
          priority: 'High',
        },
        {
          title: 'Valid Parentheses',
          difficulty: 'Easy',
          topic: 'Stack',
          url: 'https://leetcode.com/problems/valid-parentheses/',
          priority: 'High',
        },
        {
          title: 'Merge Two Sorted Lists',
          difficulty: 'Easy',
          topic: 'Linked List',
          url: 'https://leetcode.com/problems/merge-two-sorted-lists/',
          priority: 'Medium',
        },
        {
          title: 'Binary Search',
          difficulty: 'Easy',
          topic: 'Binary Search',
          url: 'https://leetcode.com/problems/binary-search/',
          priority: 'High',
        },
        {
          title: 'Best Time to Buy and Sell Stock',
          difficulty: 'Easy',
          topic: 'Arrays',
          url: 'https://leetcode.com/problems/best-time-to-buy-and-sell-stock/',
          priority: 'High',
        },
        {
          title: 'Valid Anagram',
          difficulty: 'Easy',
          topic: 'Hashing',
          url: 'https://leetcode.com/problems/valid-anagram/',
          priority: 'Medium',
        },
        {
          title: 'Longest Substring Without Repeating Characters',
          difficulty: 'Medium',
          topic: 'Sliding Window',
          url: 'https://leetcode.com/problems/longest-substring-without-repeating-characters/',
          priority: 'High',
        },
        {
          title: 'Container With Most Water',
          difficulty: 'Medium',
          topic: 'Two Pointers',
          url: 'https://leetcode.com/problems/container-with-most-water/',
          priority: 'Medium',
        },
        {
          title: 'Product of Array Except Self',
          difficulty: 'Medium',
          topic: 'Arrays',
          url: 'https://leetcode.com/problems/product-of-array-except-self/',
          priority: 'High',
        },
        {
          title: 'Maximum Subarray',
          difficulty: 'Medium',
          topic: 'Dynamic Programming',
          url: 'https://leetcode.com/problems/maximum-subarray/',
          priority: 'High',
        },
        {
          title: 'Coin Change',
          difficulty: 'Medium',
          topic: 'Dynamic Programming',
          url: 'https://leetcode.com/problems/coin-change/',
          priority: 'Medium',
        },
        {
          title: 'LRU Cache',
          difficulty: 'Medium',
          topic: 'Design',
          url: 'https://leetcode.com/problems/lru-cache/',
          priority: 'High',
        },
      ],
      system_design_topics: [
        {
          title: 'System Design Fundamentals',
          description: 'Understanding scalability, load balancing, caching, and database sharding',
          resources: [
            'System Design Primer (GitHub)',
            'Designing Data-Intensive Applications (Book)',
            'Grokking System Design Interview',
          ],
          estimatedTime: '2-3 weeks',
        },
        {
          title: 'Design URL Shortener',
          description:
            'Classic system design problem covering hashing, database design, and scaling',
          resources: [
            'System Design Interview - URL Shortener',
            'YouTube: System Design URL Shortener',
          ],
          estimatedTime: '3-4 hours',
        },
        {
          title: 'Design Social Media Feed',
          description: 'Learn about fan-out, caching strategies, and real-time updates',
          resources: ['Designing Instagram/Twitter Feed', 'System Design: News Feed'],
          estimatedTime: '4-5 hours',
        },
        {
          title: 'Design Rate Limiter',
          description: 'Understanding API rate limiting, token bucket, and distributed systems',
          resources: ['Rate Limiting Algorithms', 'System Design: API Rate Limiter'],
          estimatedTime: '2-3 hours',
        },
        {
          title: 'Design Distributed Cache',
          description: 'Learn about consistent hashing, cache eviction policies, and Redis',
          resources: ['Designing a Distributed Cache', 'Redis Documentation'],
          estimatedTime: '3-4 hours',
        },
      ],
      behavioral_questions: [
        'Tell me about a time you faced a challenging technical problem. How did you solve it?',
        'Describe a situation where you had to work with a difficult team member.',
        "Tell me about a project you're most proud of and why.",
        'How do you handle tight deadlines and pressure?',
        'Describe a time when you had to learn a new technology quickly.',
        'Tell me about a time you made a mistake. How did you handle it?',
        'How do you prioritize tasks when working on multiple projects?',
        'Describe a situation where you had to give constructive feedback to a colleague.',
        'Tell me about a time you disagreed with a technical decision. What did you do?',
        'How do you stay updated with new technologies and industry trends?',
      ],
      timeline: '4-6 weeks of focused preparation',
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return '#10b981'
      case 'Medium':
        return '#f59e0b'
      case 'Hard':
        return '#ef4444'
      default:
        return '#6b7280'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High':
        return '#ef4444'
      case 'Medium':
        return '#f59e0b'
      case 'Low':
        return '#10b981'
      default:
        return '#6b7280'
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content prep-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Interview Preparation Plan</h2>
            <p className="job-subtitle">
              {job.title} at {job.company}
            </p>
          </div>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {loading ? (
          <div className="loading-state">Generating personalized prep plan...</div>
        ) : prepPlan ? (
          <>
            <div className="prep-tabs">
              <button
                className={`prep-tab ${activeTab === 'leetcode' ? 'active' : ''}`}
                onClick={() => setActiveTab('leetcode')}
              >
                <span className="tab-icon">💻</span>
                LeetCode Problems
                <span className="tab-count">{prepPlan.leetcode_problems.length}</span>
              </button>
              <button
                className={`prep-tab ${activeTab === 'system-design' ? 'active' : ''}`}
                onClick={() => setActiveTab('system-design')}
              >
                <span className="tab-icon">🏗️</span>
                System Design
                <span className="tab-count">{prepPlan.system_design_topics.length}</span>
              </button>
              <button
                className={`prep-tab ${activeTab === 'behavioral' ? 'active' : ''}`}
                onClick={() => setActiveTab('behavioral')}
              >
                <span className="tab-icon">💬</span>
                Behavioral
                <span className="tab-count">{prepPlan.behavioral_questions.length}</span>
              </button>
            </div>

            <div className="prep-content">
              {activeTab === 'leetcode' && (
                <div className="leetcode-section">
                  <div className="section-header">
                    <h3>Recommended LeetCode Problems</h3>
                    <p className="section-description">
                      Focus on high-priority problems first. Practice consistently for best results.
                    </p>
                  </div>
                  <div className="problems-list">
                    {prepPlan.leetcode_problems.map((problem, index) => (
                      <div key={index} className="problem-card">
                        <div className="problem-header">
                          <div className="problem-info">
                            <h4>{problem.title}</h4>
                            <span className="problem-topic">{problem.topic}</span>
                          </div>
                          <div className="problem-badges">
                            <span
                              className="badge difficulty"
                              style={{ backgroundColor: getDifficultyColor(problem.difficulty) }}
                            >
                              {problem.difficulty}
                            </span>
                            <span
                              className="badge priority"
                              style={{ backgroundColor: getPriorityColor(problem.priority) }}
                            >
                              {problem.priority}
                            </span>
                          </div>
                        </div>
                        <a
                          href={problem.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="problem-link"
                        >
                          Solve on LeetCode →
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'system-design' && (
                <div className="system-design-section">
                  <div className="section-header">
                    <h3>System Design Topics</h3>
                    <p className="section-description">
                      Master these concepts and practice designing scalable systems.
                    </p>
                  </div>
                  <div className="topics-list">
                    {prepPlan.system_design_topics.map((topic, index) => (
                      <div key={index} className="topic-card">
                        <h4>{topic.title}</h4>
                        <p className="topic-description">{topic.description}</p>
                        <div className="topic-time">⏱️ {topic.estimatedTime}</div>
                        <div className="topic-resources">
                          <strong>Resources:</strong>
                          <ul>
                            {topic.resources.map((resource, idx) => (
                              <li key={idx}>{resource}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'behavioral' && (
                <div className="behavioral-section">
                  <div className="section-header">
                    <h3>Behavioral Interview Questions</h3>
                    <p className="section-description">
                      Prepare STAR (Situation, Task, Action, Result) responses for these questions.
                    </p>
                  </div>
                  <div className="questions-list">
                    {prepPlan.behavioral_questions.map((question, index) => (
                      <div key={index} className="question-card">
                        <div className="question-number">{index + 1}</div>
                        <div className="question-text">{question}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="prep-footer">
              <div className="timeline-info">
                <strong>Recommended Timeline:</strong> {prepPlan.timeline}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
