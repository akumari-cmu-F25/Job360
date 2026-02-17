"""Test script to verify rewrite agent makes extensive edits."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.profile_parser.profile_models import Profile, Experience, Education, Skill, Project
from src.agents.job_understanding.jd_models import JobDescription, RequiredSkill, PreferredSkill
from src.agents.rewrite_tailor import RewriteTailorAgent
from src.orchestrator.central_orchestrator import CentralOrchestrator
from src.config import config


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
        ]
    )
    return profile


def create_sample_jd():
    """Create a sample job description for testing."""
    jd = JobDescription(
        title="Senior Machine Learning Engineer",
        company="Google",
        location="Mountain View, CA",
        required_skills=[
            RequiredSkill(skill="Python", importance="high"),
            RequiredSkill(skill="PyTorch", importance="high"),
            RequiredSkill(skill="TensorFlow", importance="high"),
            RequiredSkill(skill="Distributed Systems", importance="high"),
            RequiredSkill(skill="AWS", importance="medium"),
            RequiredSkill(skill="Kubernetes", importance="medium"),
            RequiredSkill(skill="Docker", importance="medium")
        ],
        preferred_skills=[
            PreferredSkill(skill="LLMs", importance="high"),
            PreferredSkill(skill="LangChain", importance="medium"),
            PreferredSkill(skill="MLOps", importance="medium")
        ],
        technical_keywords=["Python", "PyTorch", "TensorFlow", "Distributed Systems", "AWS", "Kubernetes", "Docker", "LLMs", "LangChain", "MLOps"],
        ats_keywords=["machine learning", "deep learning", "neural networks", "model training", "distributed computing"],
        emphasis_areas=["distributed systems", "machine learning", "scalability"],
        responsibilities=[
            "Design and implement machine learning models",
            "Work with distributed systems",
            "Deploy models to production",
            "Collaborate with cross-functional teams"
        ]
    )
    return jd


async def test_rewrite_agent():
    """Test the rewrite agent to see if it makes extensive edits."""
    print("="*70)
    print("TESTING REWRITE AGENT - Comprehensive Edit Verification")
    print("="*70)
    
    # Create sample data
    profile = create_sample_profile()
    jd = create_sample_jd()
    
    print(f"\n📄 Original Profile:")
    print(f"   Name: {profile.name}")
    print(f"   Experiences: {len(profile.experiences)}")
    print(f"   Projects: {len(profile.projects)}")
    print(f"   Skills: {len(profile.skills)}")
    
    total_bullets = sum(len(exp.bullets) for exp in profile.experiences)
    total_proj_bullets = sum(len(proj.bullets) for proj in profile.projects)
    print(f"   Experience bullets: {total_bullets}")
    print(f"   Project bullets: {total_proj_bullets}")
    
    print(f"\n🎯 Target Job:")
    print(f"   Role: {jd.title}")
    print(f"   Company: {jd.company}")
    print(f"   Required Skills: {len(jd.required_skills)}")
    print(f"   Priority Keywords: {jd.get_priority_skills(top_n=10)}")
    
    # Initialize agent
    orchestrator = CentralOrchestrator()
    agent = RewriteTailorAgent(orchestrator)
    
    print(f"\n🔄 Starting comprehensive editing...")
    print("-" * 70)
    
    # Run the agent
    edited_profile = await agent.process(
        input_data=None,
        profile=profile,
        jd=jd,
        instructions=None,
        company_name="Google",
        job_role="Senior Machine Learning Engineer"
    )
    
    print("-" * 70)
    print(f"\n✅ Editing Complete!")
    
    # Compare results
    print(f"\n📊 EDIT SUMMARY:")
    print("="*70)
    
    # Summary changes
    if profile.summary != edited_profile.summary:
        print(f"✓ Summary: EDITED")
        print(f"  Original: {profile.summary[:100]}...")
        print(f"  Edited:   {edited_profile.summary[:100]}...")
    else:
        print(f"✗ Summary: NOT EDITED")
    
    # Experience changes
    exp_changes = 0
    for i, (orig_exp, new_exp) in enumerate(zip(profile.experiences, edited_profile.experiences)):
        if orig_exp.bullets and new_exp.bullets:
            bullet_changes = sum(1 for orig_b, new_b in zip(orig_exp.bullets, new_exp.bullets) if orig_b != new_b)
            exp_changes += bullet_changes
            if bullet_changes > 0:
                print(f"\n✓ Experience {i+1} ({orig_exp.title}): {bullet_changes}/{len(orig_exp.bullets)} bullets edited")
                for j, (orig_b, new_b) in enumerate(zip(orig_exp.bullets, new_exp.bullets)):
                    if orig_b != new_b:
                        print(f"  Bullet {j+1}:")
                        print(f"    Original: {orig_b[:80]}...")
                        print(f"    Edited:   {new_b[:80]}...")
            else:
                print(f"\n✗ Experience {i+1} ({orig_exp.title}): NO BULLETS EDITED")
        
        # Technology changes
        tech_added = set(new_exp.technologies) - set(orig_exp.technologies)
        if tech_added:
            print(f"  Technologies added: {list(tech_added)}")
    
    print(f"\n📈 Experience Bullet Changes: {exp_changes}/{total_bullets}")
    
    # Project changes
    proj_changes = 0
    for i, (orig_proj, new_proj) in enumerate(zip(profile.projects, edited_profile.projects)):
        if orig_proj.bullets and new_proj.bullets:
            bullet_changes = sum(1 for orig_b, new_b in zip(orig_proj.bullets, new_proj.bullets) if orig_b != new_b)
            proj_changes += bullet_changes
            if bullet_changes > 0:
                print(f"\n✓ Project {i+1} ({orig_proj.name}): {bullet_changes} bullets edited")
            else:
                print(f"\n✗ Project {i+1} ({orig_proj.name}): NO BULLETS EDITED")
        
        if orig_proj.description != new_proj.description:
            print(f"  Description edited")
    
    print(f"\n📈 Project Bullet Changes: {proj_changes}/{total_proj_bullets}")
    
    # Skills changes
    skills_added = len(edited_profile.skills) - len(profile.skills)
    if skills_added > 0:
        new_skills = [s.name for s in edited_profile.skills if s.name not in [s.name for s in profile.skills]]
        print(f"\n✓ Skills: {skills_added} skills added: {new_skills}")
    else:
        print(f"\n✗ Skills: NO SKILLS ADDED")
    
    # Overall statistics
    total_changes = exp_changes + proj_changes + (1 if profile.summary != edited_profile.summary else 0) + skills_added
    total_items = total_bullets + total_proj_bullets + 1 + len(profile.skills)
    change_percentage = (total_changes / total_items * 100) if total_items > 0 else 0
    
    print(f"\n" + "="*70)
    print(f"📊 OVERALL STATISTICS:")
    print(f"   Total Changes Made: {total_changes}")
    print(f"   Total Items: {total_items}")
    print(f"   Change Percentage: {change_percentage:.1f}%")
    
    if total_changes < total_bullets * 0.5:
        print(f"\n⚠️  WARNING: Only {total_changes} changes made, expected at least {int(total_bullets * 0.7)}")
        print(f"   The agent may not be making enough edits!")
    else:
        print(f"\n✅ SUCCESS: Agent made {total_changes} comprehensive edits!")
    
    print("="*70)
    
    return edited_profile, total_changes


if __name__ == "__main__":
    edited_profile, changes = asyncio.run(test_rewrite_agent())
    print(f"\nTest completed. Total changes: {changes}")
