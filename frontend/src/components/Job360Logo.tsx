import './Job360Logo.css'

interface Job360LogoProps {
  size?: 'small' | 'medium' | 'large'
  showText?: boolean
  variant?: 'default' | 'header' | 'launch'
}

export default function Job360Logo({ 
  size = 'medium', 
  showText = true,
  variant = 'default'
}: Job360LogoProps) {
  const sizeMap = {
    small: { text: '0.875rem' },
    medium: { text: '1.25rem' },
    large: { text: '2rem' },
  }

  const dimensions = sizeMap[size]

  return (
    <div className={`job360-logo ${size} ${variant}`}>
      {showText && (
        <span className="logo-text" style={{ fontSize: dimensions.text }}>
          JOB 360
        </span>
      )}
    </div>
  )
}
