"""Test script to verify rewrite agent logic - checks if it identifies all sections."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.profile_parser.profile_models import Profile, Experience, Education, Skill, Project


def create_sample_profile():
    """Create a sample profile for testing."""
    profile = Profile(
        name="Saloni Kumar",
        email="saloni@example.com",
        phone="+1-234-567-8900",
        location="San Francisco, CA",
        summary="Experienced software engineer with expertise in machine learning and distributed systems.",
        experiences=[
            Experience(
                title="Software Engineer",
                company="Tech Corp",
                location="San Francisco, CA",
                start_date="2022-01",
                end_date="Present",
                bullets=[
                    "Developed machine learning models for recommendation systems",
                    "Worked on distributed systems architecture",
                    "Collaborated with cross-functional teams",
                    "Improved system performance by 30%"
                ],
                technologies=["Python", "TensorFlow", "AWS", "Docker"]
            ),
            Experience(
                title="Intern",
                company="Startup Inc",
                location="Palo Alto, CA",
                start_date="2021-06",
                end_date="2021-12",
                bullets=[
                    "Built web applications using React",
                    "Implemented REST APIs",
                    "Participated in code reviews"
                ],
                technologies=["JavaScript", "React", "Node.js"]
            )
        ],
        education=[
            Education(
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                institution="UC Berkeley",
                location="Berkeley, CA",
                graduation_date="2022"
            )
        ],
        skills=[
            Skill(name="Python"),
            Skill(name="JavaScript"),
            Skill(name="Machine Learning")
        ],
        projects=[
            Project(
                name="ML Recommendation System",
                description="Built a recommendation system using collaborative filtering",
                bullets=[
                    "Implemented matrix factorization algorithm",
                    "Achieved 85% accuracy"
                ],
                technologies=["Python", "PyTorch", "NumPy"]
            )
        ],
        other_sections=[
            {
                "name": "Leadership",
                "items": [
                    {
                        "title": "President",
                        "organization": "Student Council",
                        "date": "2021-2022",
                        "description": "Led team of 10 members"
                    }
                ]
            }
        ]
    )
    return profile


def test_section_identification():
    """Test if section identification logic works correctly."""
    print("="*70)
    print("TESTING SECTION IDENTIFICATION LOGIC")
    print("="*70)
    
    profile = create_sample_profile()
    
    # Simulate the _identify_sections_to_edit logic
    sections_to_edit = []
    
    # Summary
    if profile.summary:
        sections_to_edit.append("summary")
    
    # Experiences
    if profile.experiences:
        sections_to_edit.append("experiences")
        for i, exp in enumerate(profile.experiences):
            if exp.bullets:
                sections_to_edit.append(f"experience_{i}_bullets")
                for j in range(len(exp.bullets)):
                    sections_to_edit.append(f"experience_{i}_bullet_{j}")
            if exp.technologies:
                sections_to_edit.append(f"experience_{i}_technologies")
    
    # Projects
    if profile.projects:
        sections_to_edit.append("projects")
        for i, proj in enumerate(profile.projects):
            if proj.bullets or proj.description:
                sections_to_edit.append(f"project_{i}")
                if proj.bullets:
                    for j in range(len(proj.bullets)):
                        sections_to_edit.append(f"project_{i}_bullet_{j}")
    
    # Skills
    if profile.skills:
        sections_to_edit.append("skills")
    
    # Other sections
    if hasattr(profile, 'other_sections') and profile.other_sections:
        for section in profile.other_sections:
            if isinstance(section, dict) and section.get('items'):
                sections_to_edit.append(f"other_section_{section.get('name')}")
    
    print(f"\n📄 Profile Structure:")
    print(f"   Experiences: {len(profile.experiences)}")
    print(f"   Projects: {len(profile.projects)}")
    print(f"   Skills: {len(profile.skills)}")
    
    total_bullets = sum(len(exp.bullets) for exp in profile.experiences)
    total_proj_bullets = sum(len(proj.bullets) for proj in profile.projects)
    print(f"   Experience bullets: {total_bullets}")
    print(f"   Project bullets: {total_proj_bullets}")
    
    print(f"\n🎯 Sections Identified for Editing:")
    print(f"   Total sections/bullets: {len(sections_to_edit)}")
    print(f"   Sections: {sections_to_edit[:20]}...")
    
    # Calculate minimum expected edits
    min_edits = 0
    if profile.summary:
        min_edits += 1
    for exp in profile.experiences:
        if exp.bullets:
            min_edits += max(2, int(len(exp.bullets) * 0.7))
    for proj in profile.projects:
        if proj.bullets:
            min_edits += max(1, int(len(proj.bullets) * 0.7))
        if proj.description:
            min_edits += 1
    if profile.skills:
        min_edits += 1
    
    print(f"\n📊 Minimum Expected Edits: {min_edits}")
    print(f"   (Based on 70% of bullets + summary + skills)")
    
    # Expected breakdown
    print(f"\n📋 Expected Edit Breakdown:")
    print(f"   Summary: 1 edit")
    print(f"   Experience 1: {max(2, int(len(profile.experiences[0].bullets) * 0.7))} bullets")
    print(f"   Experience 2: {max(2, int(len(profile.experiences[1].bullets) * 0.7))} bullets")
    print(f"   Project 1: {max(1, int(len(profile.projects[0].bullets) * 0.7))} bullets + description")
    print(f"   Skills: 1 edit")
    print(f"   Total minimum: {min_edits} edits")
    
    print(f"\n✅ Section identification test complete!")
    print(f"   The agent should make at least {min_edits} edits")
    print("="*70)
    
    return sections_to_edit, min_edits


if __name__ == "__main__":
    sections, min_edits = test_section_identification()
    print(f"\n✓ Identified {len(sections)} sections/bullets for editing")
    print(f"✓ Minimum expected edits: {min_edits}")
