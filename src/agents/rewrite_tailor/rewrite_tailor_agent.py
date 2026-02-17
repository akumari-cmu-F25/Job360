"""Rewrite & Tailor Agent - Customizes resume based on JD and instructions."""

import json
import logging
from typing import Dict, Any, Optional, List

from src.orchestrator.base_agent import BaseAgent
from src.config import config
from src.agents.profile_parser.profile_models import Profile, Experience, Project
from src.agents.job_understanding.jd_models import JobDescription
from .edit_plan import EditPlan, EditAction, EditActionType

logger = logging.getLogger(__name__)


class RewriteTailorAgent(BaseAgent):
    """Rewrites and tailors resume content based on JD and instructions."""
    
    async def process(
        self,
        input_data: Any,
        profile: Profile,
        jd: Optional[JobDescription] = None,
        instructions: Optional[Dict[str, Any]] = None,
        company_name: Optional[str] = None,
        job_role: Optional[str] = None,
        **kwargs
    ) -> Profile:
        """
        Process and customize resume.
        
        Args:
            input_data: Not used directly
            profile: Original profile to edit
            jd: Job description analysis
            instructions: Voice/text instructions
            company_name: Target company
            job_role: Target job role
        
        Returns:
            Edited Profile
        """
        # Store job_role for later use
        if job_role:
            if isinstance(instructions, dict):
                instructions['job_role'] = job_role
            elif instructions is None:
                instructions = {'job_role': job_role}
        logger.info(f"Creating edit plan... Profile has {len(profile.experiences)} experiences, {len(profile.projects)} projects")
        
        # First, identify ALL sections that need editing
        sections_to_edit = await self._identify_sections_to_edit(profile, jd, company_name, job_role)
        logger.info(f"Identified {len(sections_to_edit)} sections that need editing: {sections_to_edit}")
        
        # Create edit plan (but don't rely on it - we'll force comprehensive editing)
        edit_plan = await self._create_edit_plan(profile, jd, instructions, company_name, job_role)
        logger.info(f"Edit plan created with {len(edit_plan.actions)} actions")
        
        # FORCE comprehensive editing - don't rely on edit plan alone
        # Calculate minimum expected edits
        min_expected_edits = self._calculate_minimum_expected_edits(profile)
        logger.info(f"Minimum expected edits: {min_expected_edits}")
        
        # If edit plan is too small, log warning but proceed with forced editing
        if len(edit_plan.actions) < min_expected_edits * 0.5:
            logger.warning(f"Edit plan has only {len(edit_plan.actions)} actions, but expected at least {min_expected_edits}. Forcing comprehensive edits.")
        
        # Skills gap analysis is optional - skip if method doesn't exist yet
        # (This will be implemented in future enhancement)
        
        # Apply edits to ALL identified sections using enhanced strategies
        edited_profile = await self._apply_edits_comprehensive(
            profile, edit_plan, jd, instructions, company_name, job_role, sections_to_edit
        )
        
        # Evaluate if all sections were edited
        evaluation = await self._evaluate_edit_completeness(
            profile, edited_profile, sections_to_edit, jd
        )
        logger.info(f"Edit evaluation: {evaluation}")
        
        # Count actual changes made
        changes_count = len(edit_plan.actions)
        if jd:
            # Count bullets that were rewritten
            for exp in edited_profile.experiences:
                if exp.bullets:
                    changes_count += len(exp.bullets)
            for proj in edited_profile.projects:
                if proj.bullets:
                    changes_count += len(proj.bullets)
        
        logger.info(f"Applied {changes_count} total edits to resume across {len(sections_to_edit)} sections")
        
        return edited_profile
    
    async def _create_edit_plan(
        self,
        profile: Profile,
        jd: Optional[JobDescription],
        instructions: Optional[Dict[str, Any]],
        company_name: Optional[str],
        job_role: Optional[str]
    ) -> EditPlan:
        """Create a comprehensive edit plan for editing the resume."""
        
        # Build context for LLM
        profile_summary = self._summarize_profile(profile)
        jd_summary = self._summarize_jd(jd) if jd else "No job description provided"
        instructions_text = self._format_instructions(instructions, company_name, job_role)
        
        prompt = f"""Create a COMPREHENSIVE edit plan to tailor this resume for the target position. 
You MUST make extensive changes across ALL sections of the resume.

RESUME SUMMARY:
{profile_summary}

JOB DESCRIPTION:
{jd_summary}

INSTRUCTIONS:
{instructions_text}

Create a DETAILED and EXTENSIVE edit plan. You MUST:
1. Rewrite MULTIPLE bullets in EACH experience (at least 2-3 bullets per experience)
2. Update the professional summary to match the role
3. Add/update skills section with JD keywords
4. Update project descriptions with relevant keywords
5. Rewrite bullets in ALL relevant experiences, not just one
6. Incorporate JD keywords throughout the entire resume

Return as JSON with MANY actions (aim for 15-30 actions):
{{
    "summary": "Brief summary of the comprehensive customization strategy",
    "actions": [
        {{
            "action_type": "rewrite_bullet|add_keyword|remove_item|reorder|emphasize|deemphasize|update_summary|update_skills",
            "target": "experience_0_bullet_1 or project_2 or skill_5 or summary",
            "description": "What to change",
            "old_value": "Current text (if applicable)",
            "new_value": "New text (if applicable)",
            "reason": "Why this change improves ATS match",
            "priority": 0.9
        }}
    ],
    "keywords_to_add": ["keyword1", "keyword2", ...],
    "keywords_to_emphasize": ["keyword1", ...],
    "sections_to_prioritize": ["experience", "projects", "skills", "summary"],
    "estimated_ats_score_improvement": 0.5
}}

IMPORTANT: 
- Create actions for EVERY experience entry
- Create actions for ALL projects
- Update summary section
- Update skills section
- Make changes to at least 70% of all bullets
- Be aggressive in incorporating JD keywords
- Don't be conservative - make extensive changes

Return a comprehensive plan with many actions.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume writer specializing in ATS optimization. Create detailed, actionable edit plans. Always return valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            plan_data = json.loads(content)
            
            # Build EditPlan
            actions = []
            for action_data in plan_data.get("actions", []):
                try:
                    action_type = EditActionType(action_data["action_type"])
                except ValueError:
                    continue
                
                action = EditAction(
                    action_type=action_type,
                    target=action_data.get("target", ""),
                    description=action_data.get("description", ""),
                    old_value=action_data.get("old_value"),
                    new_value=action_data.get("new_value"),
                    reason=action_data.get("reason", ""),
                    priority=action_data.get("priority", 0.7)
                )
                actions.append(action)
            
            edit_plan = EditPlan(
                actions=actions,
                summary=plan_data.get("summary", ""),
                keywords_to_add=plan_data.get("keywords_to_add", []),
                keywords_to_emphasize=plan_data.get("keywords_to_emphasize", []),
                sections_to_prioritize=plan_data.get("sections_to_prioritize", []),
                estimated_ats_score_improvement=plan_data.get("estimated_ats_score_improvement", 0.2)
            )
            
            return edit_plan
            
        except Exception as e:
            logger.error(f"Failed to create edit plan: {e}")
            # Return minimal plan
            return EditPlan(
                actions=[],
                summary="Edit plan creation failed",
                estimated_ats_score_improvement=0.0
            )
    
    def _calculate_minimum_expected_edits(self, profile: Profile) -> int:
        """Calculate minimum number of edits that should be made."""
        min_edits = 0
        
        # Summary: at least 1 edit
        if profile.summary:
            min_edits += 1
        
        # Each experience: at least 2-3 bullets per experience
        for exp in profile.experiences:
            if exp.bullets:
                # Edit at least 70% of bullets, minimum 2 per experience
                min_edits += max(2, int(len(exp.bullets) * 0.7))
        
        # Each project: at least 1-2 edits per project
        for proj in profile.projects:
            if proj.bullets:
                min_edits += max(1, int(len(proj.bullets) * 0.7))
            if proj.description:
                min_edits += 1
        
        # Skills: at least 1 edit if JD provided
        if profile.skills:
            min_edits += 1
        
        return min_edits
    
    async def _identify_sections_to_edit(
        self,
        profile: Profile,
        jd: Optional[JobDescription],
        company_name: Optional[str],
        job_role: Optional[str]
    ) -> List[str]:
        """Identify ALL sections that need editing based on JD - AGGRESSIVE."""
        sections_to_edit = []
        
        # If no JD and no company/role, still identify sections for basic editing
        # Always edit if there's any target information
        
        # ALWAYS edit summary if it exists
        if profile.summary:
            sections_to_edit.append("summary")
        
        # ALWAYS edit ALL experiences
        if profile.experiences:
            sections_to_edit.append("experiences")
            # Check each experience - mark ALL for editing
            for i, exp in enumerate(profile.experiences):
                if exp.bullets:
                    sections_to_edit.append(f"experience_{i}_bullets")
                    # Mark each bullet individually for maximum coverage
                    for j in range(len(exp.bullets)):
                        sections_to_edit.append(f"experience_{i}_bullet_{j}")
                if exp.technologies:
                    sections_to_edit.append(f"experience_{i}_technologies")
        
        # ALWAYS edit ALL projects
        if profile.projects:
            sections_to_edit.append("projects")
            for i, proj in enumerate(profile.projects):
                if proj.bullets or proj.description:
                    sections_to_edit.append(f"project_{i}")
                    # Mark each project bullet
                    if proj.bullets:
                        for j in range(len(proj.bullets)):
                            sections_to_edit.append(f"project_{i}_bullet_{j}")
        
        # ALWAYS edit skills
        if profile.skills:
            sections_to_edit.append("skills")
        
        # Edit other sections
        if profile.certifications:
            sections_to_edit.append("certifications")
        
        if profile.awards:
            sections_to_edit.append("awards")
        
        if profile.other_sections:
            for section in profile.other_sections:
                if section.items:
                    sections_to_edit.append(f"other_section_{section.name}")
        
        logger.info(f"Identified {len(sections_to_edit)} sections/bullets to edit: {sections_to_edit[:10]}...")
        return sections_to_edit
    
    async def _apply_edits_comprehensive(
        self,
        profile: Profile,
        edit_plan: EditPlan,
        jd: Optional[JobDescription],
        instructions: Optional[Dict[str, Any]],
        company_name: Optional[str],
        job_role: Optional[str],
        sections_to_edit: List[str]
    ) -> Profile:
        """Apply edits comprehensively to ALL identified sections."""
        return await self._apply_edits(profile, edit_plan, jd, instructions, company_name, job_role)
    
    async def _apply_edits(
        self,
        profile: Profile,
        edit_plan: EditPlan,
        jd: Optional[JobDescription],
        instructions: Optional[Dict[str, Any]],
        company_name: Optional[str] = None,
        job_role: Optional[str] = None
    ) -> Profile:
        """Apply comprehensive edits to profile across ALL sections while preserving structure."""
        # Create deep copy to preserve original structure
        edited_profile = profile.model_copy(deep=True)
        
        # Preserve original section order and structure
        # Store original counts to ensure we don't lose sections
        original_exp_count = len(profile.experiences)
        original_proj_count = len(profile.projects)
        original_edu_count = len(profile.education)
        original_cert_count = len(profile.certifications)
        original_award_count = len(profile.awards)
        original_other_sections_count = len(profile.other_sections)
        
        # Apply each action from plan
        for action in edit_plan.actions:
            try:
                if action.action_type == EditActionType.REWRITE_BULLET:
                    self._rewrite_bullet(edited_profile, action)
                elif action.action_type == EditActionType.ADD_KEYWORD:
                    self._add_keyword(edited_profile, action)
                elif action.action_type == EditActionType.EMPHASIZE:
                    self._emphasize_item(edited_profile, action)
                elif action.action_type == EditActionType.DEEMPHASIZE:
                    self._deemphasize_item(edited_profile, action)
            except Exception as e:
                logger.warning(f"Failed to apply action {action.target}: {e}")
        
        # FORCE COMPREHENSIVE editing: Edit ALL sections systematically
        # This happens REGARDLESS of edit plan - we force edits on everything
        
        edit_count_before = self._count_edits_made(profile, edited_profile)
        logger.info(f"Edits before comprehensive editing: {edit_count_before}")
        
        # 1. Summary section - ALWAYS edit if exists (Strategy 4: Relevant Summary)
        if edited_profile.summary:
            logger.info("FORCING summary section edit with JD-optimized strategy...")
            if jd:
                # Use existing summary rewrite method
                new_summary = await self._rewrite_summary(
                    edited_profile.summary, jd, job_role
                )
                if new_summary and new_summary.strip() and new_summary.strip() != edited_profile.summary.strip():
                    edited_profile.summary = new_summary
                    logger.info("Summary rewritten with JD optimization")
                else:
                    logger.warning("Summary rewrite returned same or empty text")
            elif company_name or job_role:
                new_summary = await self._rewrite_summary_for_role(edited_profile.summary, company_name, job_role)
                if new_summary and new_summary != edited_profile.summary:
                    edited_profile.summary = new_summary
                    logger.info("Summary edited successfully")
        
        # 2. EXTENSIVE keyword incorporation across ALL experience sections - FORCE THIS
        if jd:
            logger.info("FORCING extensive JD keyword incorporation across ALL experiences...")
            await self._incorporate_jd_keywords_extensive(edited_profile, jd, edit_plan.keywords_to_add, instructions)
        elif company_name or job_role:
            logger.info(f"FORCING edits based on company/role across ALL experiences...")
            await self._incorporate_company_role_edits(edited_profile, company_name, job_role, instructions)
        else:
            # Even with no JD/role, still try to improve bullets
            logger.info("Making general improvements to experience bullets...")
            await self._improve_bullets_generally(edited_profile)
        
        # 3. Update ALL project descriptions and bullets - FORCE THIS
        if edited_profile.projects:
            logger.info(f"FORCING edits to {len(edited_profile.projects)} projects...")
            for proj_idx, proj in enumerate(edited_profile.projects):
                if proj.description:
                    logger.info(f"Rewriting project {proj_idx} description: {proj.name}")
                    if jd:
                        new_desc = await self._rewrite_project_description(proj.description, jd)
                        if new_desc:
                            proj.description = new_desc
                
                # FORCE rewrite of ALL project bullets
                if proj.bullets:
                    logger.info(f"FORCING rewrite of {len(proj.bullets)} bullets for project {proj.name}")
                    for i, bullet in enumerate(proj.bullets):
                        if jd:
                            keywords = jd.get_priority_skills(top_n=5)
                            new_bullet = await self._rewrite_bullet_async(bullet, keywords)
                        else:
                            # Even without JD, improve the bullet
                            new_bullet = await self._improve_bullet_generally(bullet)
                        if new_bullet:
                            proj.bullets[i] = new_bullet
        
        # 4. Update skills section - FORCE THIS
        if edited_profile.skills:
            logger.info("FORCING skills section update...")
            if jd:
                await self._update_skills_section(edited_profile, jd)
            # Even without JD, ensure skills are well-formatted
        
        # 5. Update other sections if needed
        if edited_profile.other_sections:
            logger.info(f"Updating {len(edited_profile.other_sections)} other sections...")
            for section in edited_profile.other_sections:
                if section.items and jd:
                    await self._update_other_section(edited_profile, section, jd)
        
        edit_count_after = self._count_edits_made(profile, edited_profile)
        logger.info(f"Edits after comprehensive editing: {edit_count_after} (added {edit_count_after - edit_count_before} edits)")
        
        # Ensure structure is preserved - verify section counts
        # Don't remove sections, only modify content
        if len(edited_profile.experiences) < original_exp_count:
            logger.warning(f"Experience count decreased from {original_exp_count} to {len(edited_profile.experiences)}")
        if len(edited_profile.projects) < original_proj_count:
            logger.warning(f"Project count decreased from {original_proj_count} to {len(edited_profile.projects)}")
        if len(edited_profile.education) < original_edu_count:
            logger.warning(f"Education count decreased from {original_edu_count} to {len(edited_profile.education)}")
        if len(edited_profile.certifications) < original_cert_count:
            logger.warning(f"Certification count decreased from {original_cert_count} to {len(edited_profile.certifications)}")
        if len(edited_profile.awards) < original_award_count:
            logger.warning(f"Award count decreased from {original_award_count} to {len(edited_profile.awards)}")
        if len(edited_profile.other_sections) < original_other_sections_count:
            logger.warning(f"Other sections count decreased from {original_other_sections_count} to {len(edited_profile.other_sections)}")
        
        return edited_profile
    
    async def _incorporate_company_role_edits(
        self,
        profile: Profile,
        company_name: Optional[str],
        job_role: Optional[str],
        instructions: Optional[Dict[str, Any]]
    ):
        """Make edits based on company/role even without JD."""
        # Extract keywords from job role
        role_keywords = []
        if job_role:
            # Simple keyword extraction from role
            role_words = job_role.lower().split()
            role_keywords = [w for w in role_words if len(w) > 4]  # Longer words are likely keywords
        
        # Rewrite ALL experience bullets
        for exp in profile.experiences:
            if exp.bullets:
                for i, bullet in enumerate(exp.bullets):
                    # Rewrite to emphasize role-relevant content
                    new_bullet = await self._rewrite_bullet_for_role(bullet, job_role, role_keywords)
                    if new_bullet:
                        exp.bullets[i] = new_bullet
        
        # Rewrite project bullets
        for proj in profile.projects:
            if proj.bullets:
                for i, bullet in enumerate(proj.bullets):
                    new_bullet = await self._rewrite_bullet_for_role(bullet, job_role, role_keywords)
                    if new_bullet:
                        proj.bullets[i] = new_bullet
    
    async def _rewrite_bullet_for_role(self, bullet: str, job_role: Optional[str], keywords: List[str]) -> Optional[str]:
        """Rewrite bullet to match job role."""
        if not job_role and not keywords:
            return None
        
        prompt = f"""Rewrite this resume bullet point to better match this job role: {job_role or 'target position'}

Original bullet: {bullet}
Keywords to emphasize: {', '.join(keywords) if keywords else 'role-relevant terms'}

Make it more relevant to the role while keeping it natural and professional.
Return only the rewritten bullet point.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Tailor bullets to job roles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to rewrite bullet for role: {e}")
            return None
    
    async def _rewrite_summary_for_role(self, summary: str, company_name: Optional[str], job_role: Optional[str]) -> str:
        """Rewrite summary for company/role."""
        prompt = f"""Rewrite this professional summary to match this position:

Current Summary:
{summary}

Target Role: {job_role or 'N/A'}
Target Company: {company_name or 'N/A'}

Make it more relevant to the role and company.
Return only the rewritten summary (2-3 sentences).
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to rewrite summary: {e}")
            return summary
    
    async def _rewrite_summary(self, summary: str, jd: JobDescription, job_role: Optional[str] = None) -> str:
        """Rewrite professional summary to match JD."""
        prompt = f"""Rewrite this professional summary to match the job description and role.

Current Summary:
{summary}

Job Description Keywords: {', '.join(jd.get_priority_skills(top_n=10))}
Emphasis Areas: {', '.join(jd.emphasis_areas[:5])}
Target Role: {job_role or jd.title or 'N/A'}

Rewrite the summary to:
1. Incorporate key JD keywords naturally
2. Align with the role's emphasis areas
3. Highlight relevant experience
4. Make it ATS-friendly
5. Keep it concise (2-3 sentences)

Return only the rewritten summary.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Rewrite summaries to match job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to rewrite summary: {e}")
            return summary
    
    async def _rewrite_project_description(self, description: str, jd: JobDescription) -> str:
        """Rewrite project description with JD keywords."""
        relevant_keywords = jd.get_priority_skills(top_n=5)
        
        prompt = f"""Rewrite this project description to incorporate these keywords: {', '.join(relevant_keywords)}

Current Description:
{description}

Make it sound natural and professional. Keep the same meaning but incorporate keywords seamlessly.
Return only the rewritten description.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to rewrite project: {e}")
            return description
    
    def _rewrite_bullet(self, profile: Profile, action: EditAction):
        """Rewrite a specific bullet point."""
        # Parse target (e.g., "experience_0_bullet_1")
        parts = action.target.split("_")
        if len(parts) >= 3 and parts[0] == "experience":
            exp_idx = int(parts[1])
            if exp_idx < len(profile.experiences):
                exp = profile.experiences[exp_idx]
                if parts[2] == "bullet" and len(parts) >= 4:
                    bullet_idx = int(parts[3])
                    if bullet_idx < len(exp.bullets):
                        exp.bullets[bullet_idx] = action.new_value or action.description
    
    def _add_keyword(self, profile: Profile, action: EditAction):
        """Add keyword to appropriate section."""
        keyword = action.new_value or action.description
        # Add to relevant experience or project
        if profile.experiences:
            # Add to most recent experience
            profile.experiences[0].technologies.append(keyword)
    
    def _emphasize_item(self, profile: Profile, action: EditAction):
        """Emphasize an item (move up, make more prominent)."""
        # Could reorder experiences or bullets
        pass
    
    def _deemphasize_item(self, profile: Profile, action: EditAction):
        """De-emphasize an item."""
        # Could remove or shorten bullets
        pass
    
    async def _incorporate_jd_keywords_extensive(
        self,
        profile: Profile,
        jd: JobDescription,
        keywords_to_add: List[str],
        instructions: Optional[Dict[str, Any]] = None
    ):
        """EXTENSIVE keyword incorporation across ALL sections - ASYNC version."""
        all_keywords = jd.get_all_keywords() + keywords_to_add
        priority_keywords = jd.get_priority_skills(top_n=20)
        
        logger.info(f"Starting extensive keyword incorporation: {len(profile.experiences)} experiences, {len(profile.projects)} projects")
        
        # EXTENSIVE: Rewrite ALL experience bullets (not just matching ones) - FORCE THIS
        bullets_rewritten = 0
        for exp_idx, exp in enumerate(profile.experiences):
            if exp.bullets:
                logger.info(f"FORCING rewrite of {len(exp.bullets)} bullets for experience {exp_idx}: {exp.title} at {exp.company}")
                # Rewrite EVERY bullet to include JD keywords - NO EXCEPTIONS
                for i, bullet in enumerate(exp.bullets):
                    # Find relevant keywords
                    relevant_keywords = self._find_relevant_keywords(bullet, all_keywords + priority_keywords)
                    
                    # ALWAYS use keywords - if no direct match, use top priority keywords
                    if not relevant_keywords:
                        relevant_keywords = priority_keywords[:5]  # Use more keywords
                    
                    # Strategy 2: Tailored bullet points with gap analysis
                    original_bullet = bullet
                    new_bullet = None
                    
                    # Use bullet rewriting with keywords
                    if jd and relevant_keywords:
                        # Use JD keywords for rewriting
                        new_bullet = await self._rewrite_bullet_async(bullet, relevant_keywords)
                    elif relevant_keywords:
                        new_bullet = await self._rewrite_bullet_async(bullet, relevant_keywords)
                    else:
                        # Fallback to general improvement
                        new_bullet = await self._improve_bullet_generally(bullet)
                    
                    # Fallback if enhanced rewrite didn't work
                    if not new_bullet or not new_bullet.strip() or new_bullet.strip().lower() == original_bullet.strip().lower():
                        logger.debug(f"Enhanced rewrite didn't change bullet {i}, trying standard rewrite...")
                        if relevant_keywords:
                            new_bullet = await self._rewrite_bullet_async(bullet, relevant_keywords)
                    
                    # Final fallback
                    if not new_bullet or new_bullet.strip().lower() == original_bullet.strip().lower():
                        logger.debug(f"Standard rewrite didn't change bullet {i}, trying general improvement...")
                        new_bullet = await self._improve_bullet_generally(original_bullet)
                    
                    # Apply the change if we got something different
                    if new_bullet and new_bullet.strip() and new_bullet.strip().lower() != original_bullet.strip().lower():
                        exp.bullets[i] = new_bullet
                        bullets_rewritten += 1
                        logger.debug(f"Rewrote bullet {i} for {exp.title}")
                    else:
                        logger.warning(f"Could not rewrite bullet {i} for {exp.title} - all attempts failed")
        
        logger.info(f"Rewrote {bullets_rewritten} experience bullets total")
        
        # Continue with rest of experience editing
        for exp_idx, exp in enumerate(profile.experiences):
            # Add more bullets if JD has many requirements
            if exp.bullets and len(exp.bullets) < 5 and priority_keywords:
                # Add 1-2 new bullets with JD keywords
                new_bullet_text = await self._create_new_bullet_with_keywords_async(exp, priority_keywords[:5])
                if new_bullet_text:
                    exp.bullets.append(new_bullet_text)
                    logger.info(f"Added new bullet to {exp.title}")
            
            # Add ALL missing technologies from JD (not just 3)
            jd_techs = set([t.lower() for t in jd.technical_keywords])
            current_techs = set([t.lower() for t in exp.technologies])
            missing_techs = [t for t in jd.technical_keywords if t.lower() not in current_techs]
            if missing_techs:
                exp.technologies.extend(missing_techs[:5])
                logger.info(f"Added {len(missing_techs[:5])} technologies to {exp.title}")
        
        # Update ALL project descriptions - FORCE THIS
        proj_bullets_rewritten = 0
        for proj_idx, proj in enumerate(profile.projects):
            if proj.bullets:
                logger.info(f"FORCING rewrite of {len(proj.bullets)} bullets for project {proj_idx}: {proj.name}")
                # Rewrite ALL project bullets - NO EXCEPTIONS
                for i, bullet in enumerate(proj.bullets):
                    original_bullet = bullet
                    relevant_keywords = self._find_relevant_keywords(bullet, priority_keywords)
                    if not relevant_keywords:
                        relevant_keywords = priority_keywords[:5]  # Use more keywords
                    
                    new_bullet = await self._rewrite_bullet_async(bullet, relevant_keywords)
                    
                    # Fallback if rewrite didn't change
                    if not new_bullet or new_bullet.strip().lower() == original_bullet.strip().lower():
                        new_bullet = await self._improve_bullet_generally(original_bullet)
                    
                    if new_bullet and new_bullet.strip() and new_bullet.strip().lower() != original_bullet.strip().lower():
                        proj.bullets[i] = new_bullet
                        proj_bullets_rewritten += 1
                        logger.debug(f"✓ Rewrote project bullet {i} for {proj.name}")
        
        logger.info(f"Rewrote {proj_bullets_rewritten} project bullets total")
        
        # Add missing technologies to projects
        for proj in profile.projects:
            jd_techs = set([t.lower() for t in jd.technical_keywords])
            current_techs = set([t.lower() for t in proj.technologies])
            missing_techs = [t for t in jd.technical_keywords if t.lower() not in current_techs]
            if missing_techs:
                proj.technologies.extend(missing_techs[:3])
        
        # Add ALL missing skills from JD (not just 5)
        jd_skills = set([s.skill.lower() for s in jd.required_skills + jd.preferred_skills])
        current_skills = set([s.name.lower() for s in profile.skills])
        missing_skills = [s.skill for s in jd.required_skills + jd.preferred_skills 
                         if s.skill.lower() not in current_skills]
        if missing_skills:
            from src.agents.profile_parser.profile_models import Skill
            # Add up to 10 missing skills
            added = 0
            for skill_name in missing_skills[:10]:
                profile.skills.append(Skill(name=skill_name))
                added += 1
            logger.info(f"Added {added} missing skills")
        
        logger.info("Completed extensive keyword incorporation")
    
    async def _update_skills_section(self, profile: Profile, jd: JobDescription):
        """Update skills section with JD keywords."""
        jd_skills = set([s.skill.lower() for s in jd.required_skills + jd.preferred_skills])
        current_skills = set([s.name.lower() for s in profile.skills])
        missing_skills = [s.skill for s in jd.required_skills + jd.preferred_skills 
                         if s.skill.lower() not in current_skills]
        if missing_skills:
            from src.agents.profile_parser.profile_models import Skill
            added = 0
            for skill_name in missing_skills[:10]:
                profile.skills.append(Skill(name=skill_name))
                added += 1
            logger.info(f"Added {added} missing skills to skills section")
    
    async def _update_other_section(self, profile: Profile, section, jd: JobDescription):
        """Update other sections (leadership, etc.) with JD keywords."""
        # Update descriptions in other sections to include relevant keywords
        priority_keywords = jd.get_priority_skills(top_n=5)
        for item in section.items:
            if isinstance(item, dict) and item.get('description'):
                desc = item.get('description')
                if desc and priority_keywords:
                    # Rewrite description to include keywords
                    new_desc = await self._rewrite_bullet_async(desc, priority_keywords)
                    if new_desc:
                        item['description'] = new_desc
                        logger.debug(f"Updated {section.name} item description")
    
    async def _evaluate_edit_completeness(
        self,
        original_profile: Profile,
        edited_profile: Profile,
        sections_to_edit: List[str],
        jd: Optional[JobDescription]
    ) -> Dict[str, Any]:
        """Evaluate if all sections that needed editing were actually edited."""
        evaluation = {
            "sections_identified": len(sections_to_edit),
            "sections_edited": 0,
            "missing_edits": [],
            "edit_counts": {}
        }
        
        # Check each section
        for section in sections_to_edit:
            edited = False
            
            if section == "summary":
                if original_profile.summary != edited_profile.summary:
                    edited = True
                    evaluation["edit_counts"]["summary"] = 1
            
            elif section == "experiences":
                changes = 0
                if original_profile.experiences and edited_profile.experiences:
                    for orig_exp, new_exp in zip(original_profile.experiences, edited_profile.experiences):
                        if orig_exp.bullets and new_exp.bullets:
                            for orig_b, new_b in zip(orig_exp.bullets, new_exp.bullets):
                                if orig_b != new_b:
                                    changes += 1
                if changes > 0:
                    edited = True
                    evaluation["edit_counts"]["experiences"] = changes
            
            elif section.startswith("experience_"):
                # Individual experience
                try:
                    exp_idx = int(section.split("_")[1])
                    if exp_idx < len(original_profile.experiences) and exp_idx < len(edited_profile.experiences):
                        orig_exp = original_profile.experiences[exp_idx]
                        new_exp = edited_profile.experiences[exp_idx]
                        if orig_exp.bullets and new_exp.bullets:
                            changes = sum(1 for orig_b, new_b in zip(orig_exp.bullets, new_exp.bullets) if orig_b != new_b)
                            if changes > 0:
                                edited = True
                                evaluation["edit_counts"][section] = changes
                except (ValueError, IndexError):
                    pass
            
            elif section == "projects":
                changes = 0
                if original_profile.projects and edited_profile.projects:
                    for orig_proj, new_proj in zip(original_profile.projects, edited_profile.projects):
                        if orig_proj.bullets and new_proj.bullets:
                            for orig_b, new_b in zip(orig_proj.bullets, new_proj.bullets):
                                if orig_b != new_b:
                                    changes += 1
                        if orig_proj.description != new_proj.description:
                            changes += 1
                if changes > 0:
                    edited = True
                    evaluation["edit_counts"]["projects"] = changes
            
            elif section == "skills":
                if len(original_profile.skills) != len(edited_profile.skills):
                    edited = True
                    evaluation["edit_counts"]["skills"] = len(edited_profile.skills) - len(original_profile.skills)
            
            if edited:
                evaluation["sections_edited"] += 1
            else:
                evaluation["missing_edits"].append(section)
        
        evaluation["completeness_score"] = (
            evaluation["sections_edited"] / evaluation["sections_identified"]
            if evaluation["sections_identified"] > 0 else 0.0
        )
        
        logger.info(f"Edit completeness: {evaluation['sections_edited']}/{evaluation['sections_identified']} sections edited "
                   f"(score: {evaluation['completeness_score']:.2f})")
        
        if evaluation["missing_edits"]:
            logger.warning(f"Sections not edited: {evaluation['missing_edits']}")
        
        return evaluation
    
    def _count_edits_made(self, original: Profile, edited: Profile) -> int:
        """Count total number of edits made."""
        count = 0
        
        # Summary
        if original.summary != edited.summary:
            count += 1
        
        # Experiences
        if original.experiences and edited.experiences:
            for orig_exp, new_exp in zip(original.experiences, edited.experiences):
                if orig_exp.bullets and new_exp.bullets:
                    count += sum(1 for orig_b, new_b in zip(orig_exp.bullets, new_exp.bullets) if orig_b != new_b)
                # Check technologies
                if set(orig_exp.technologies) != set(new_exp.technologies):
                    count += len(set(new_exp.technologies) - set(orig_exp.technologies))
        
        # Projects
        if original.projects and edited.projects:
            for orig_proj, new_proj in zip(original.projects, edited.projects):
                if orig_proj.description != new_proj.description:
                    count += 1
                if orig_proj.bullets and new_proj.bullets:
                    count += sum(1 for orig_b, new_b in zip(orig_proj.bullets, new_proj.bullets) if orig_b != new_b)
        
        # Skills
        if len(original.skills) != len(edited.skills):
            count += abs(len(edited.skills) - len(original.skills))
        
        return count
    
    async def _improve_bullets_generally(self, profile: Profile):
        """Make general improvements to bullets even without JD."""
        for exp in profile.experiences:
            if exp.bullets:
                for i, bullet in enumerate(exp.bullets):
                    improved = await self._improve_bullet_generally(bullet)
                    if improved:
                        exp.bullets[i] = improved
    
    async def _improve_bullet_generally(self, bullet: str) -> Optional[str]:
        """Improve a bullet point generally (make it more impactful, add metrics if possible)."""
        prompt = f"""Improve this resume bullet point to be more impactful and professional:

Current bullet: {bullet}

Make it:
1. More specific with quantifiable metrics if possible
2. More action-oriented
3. More professional
4. More concise if needed

Return only the improved bullet point.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Improve bullet points to be more impactful."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=150
            )
            
            improved = response.choices[0].message.content.strip()
            # Only return if it's actually different
            if improved.lower() != bullet.lower():
                return improved
            return None
        except Exception as e:
            logger.warning(f"Failed to improve bullet: {e}")
            return None
    
    def _create_new_bullet_with_keywords(self, exp: Experience, keywords: List[str]) -> Optional[str]:
        """Create a new bullet point - synchronous wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._create_new_bullet_with_keywords_async(exp, keywords))
        except RuntimeError:
            return asyncio.run(self._create_new_bullet_with_keywords_async(exp, keywords))
    
    async def _create_new_bullet_with_keywords_async(self, exp: Experience, keywords: List[str]) -> Optional[str]:
        """Create a new bullet point incorporating JD keywords - ASYNC version."""
        prompt = f"""Create a new resume bullet point for this experience that incorporates these keywords: {', '.join(keywords[:5])}

Experience: {exp.title} at {exp.company}
Existing bullets: {', '.join(exp.bullets[:2])}

Create a new, impactful bullet point that:
1. Incorporates the keywords naturally
2. Shows quantifiable impact
3. Matches the job requirements
4. Sounds professional

Return only the new bullet point.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Create impactful bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to create new bullet: {e}")
            return None
    
    async def _rewrite_summary(self, summary: str, jd: JobDescription, job_role: Optional[str] = None) -> str:
        """Rewrite professional summary to match JD - comprehensive."""
        if not jd:
            return summary
        
        priority_skills = jd.get_priority_skills(top_n=10)
        emphasis = jd.emphasis_areas[:5]
        
        prompt = f"""Completely rewrite this professional summary to match the job description.

Current Summary:
{summary}

Target Role: {job_role or jd.title or 'N/A'}
Required Skills: {', '.join(priority_skills[:8])}
Emphasis Areas: {', '.join(emphasis)}
Company: {jd.company or 'N/A'}

Rewrite the summary to:
1. Incorporate key JD skills and keywords naturally
2. Align with the role's emphasis areas
3. Highlight relevant experience for this specific role
4. Make it highly ATS-friendly
5. Keep it concise (2-3 sentences, max 150 words)
6. Be specific about how experience matches the role

Return only the rewritten summary.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Rewrite summaries to perfectly match job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to rewrite summary: {e}")
            return summary
    
    def _find_relevant_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find keywords relevant to the text - more aggressive matching."""
        text_lower = text.lower()
        relevant = []
        
        # More aggressive matching - check for partial matches
        for keyword in keywords[:15]:  # Check more keywords
            keyword_lower = keyword.lower()
            # Direct match
            if keyword_lower in text_lower:
                relevant.append(keyword)
            # Partial word match
            elif any(word in text_lower for word in keyword_lower.split() if len(word) > 3):
                relevant.append(keyword)
            # Semantic similarity (simple check)
            elif any(word in keyword_lower for word in text_lower.split() if len(word) > 4):
                relevant.append(keyword)
        
        # Return up to 5 keywords (more aggressive)
        return relevant[:5] if relevant else []
    
    def _rewrite_with_keywords(self, bullet: str, keywords: List[str]) -> Optional[str]:
        """Rewrite bullet to naturally include keywords - synchronous version (for backwards compat)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._rewrite_bullet_async(bullet, keywords))
        except RuntimeError:
            # If no event loop, create one
            return asyncio.run(self._rewrite_bullet_async(bullet, keywords))
    
    async def _rewrite_bullet_async(self, bullet: str, keywords: List[str]) -> Optional[str]:
        """Rewrite bullet to naturally include keywords - ASYNC version."""
        if not keywords:
            return None
        
        # Use more keywords (up to 5)
        keywords_to_use = keywords[:5]
        
        prompt = f"""Rewrite this resume bullet point to naturally incorporate these keywords: {', '.join(keywords_to_use)}

Original bullet: {bullet}

IMPORTANT:
- Incorporate ALL the keywords naturally
- Make it sound professional and impactful
- Add quantifiable metrics if possible
- Keep the core meaning but enhance it with keywords
- Make it ATS-friendly

Return only the rewritten bullet point.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Aggressively incorporate keywords while keeping it natural."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Slightly higher for more variation
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to rewrite bullet: {e}")
            return None
    
    def _summarize_profile(self, profile: Profile) -> str:
        """Create summary of profile for LLM."""
        summary = f"Name: {profile.name}\n"
        summary += f"Experiences: {len(profile.experiences)}\n"
        for i, exp in enumerate(profile.experiences[:3]):
            summary += f"  {i+1}. {exp.title} at {exp.company}\n"
            summary += f"     Technologies: {', '.join(exp.technologies[:5])}\n"
        summary += f"Skills: {', '.join([s.name for s in profile.skills[:10]])}\n"
        return summary
    
    def _summarize_jd(self, jd: JobDescription) -> str:
        """Create summary of JD for LLM."""
        summary = f"Title: {jd.title}\n"
        summary += f"Company: {jd.company}\n"
        summary += f"Required Skills: {', '.join([s.skill for s in jd.required_skills[:10]])}\n"
        summary += f"ATS Keywords: {', '.join(jd.ats_keywords[:15])}\n"
        summary += f"Emphasis Areas: {', '.join(jd.emphasis_areas)}\n"
        return summary
    
    def _format_instructions(
        self,
        instructions: Optional[Dict[str, Any]],
        company_name: Optional[str],
        job_role: Optional[str]
    ) -> str:
        """Format instructions for LLM - supports cumulative instructions."""
        text = ""
        if company_name:
            text += f"Target Company: {company_name}\n"
        if job_role:
            text += f"Target Role: {job_role}\n"
        
        if instructions:
            # Handle both single instruction dict and list of instructions
            if isinstance(instructions, list):
                # Cumulative instructions - combine all
                text += "User Instructions (cumulative, apply all):\n"
                for i, inst in enumerate(instructions, 1):
                    intent = inst.get('intent', inst.get('transcription', ''))
                    text += f"  {i}. {intent}\n"
                    constraints = inst.get('constraints', [])
                    if constraints:
                        text += f"     Constraints: {', '.join(constraints)}\n"
            else:
                # Single instruction
                text += f"User Instructions: {instructions.get('intent', '')}\n"
                constraints = instructions.get('constraints', [])
                if constraints:
                    text += f"Constraints: {', '.join(constraints)}\n"
        
        return text or "No specific instructions"
    
    async def customize_resume(
        self,
        profile: Profile,
        jd: Optional[JobDescription] = None,
        instructions: Optional[Dict[str, Any]] = None,
        company_name: Optional[str] = None,
        job_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method to customize resume."""
        result = await self.execute(
            profile,
            profile=profile,
            jd=jd,
            instructions=instructions,
            company_name=company_name,
            job_role=job_role,
            input_type="resume_customization",
            output_type="structured_data",
            task_description="Customize resume based on JD and instructions"
        )
        
        if result["success"]:
            return {
                "edited_profile": result["output"],
                "success": True
            }
        else:
            return {
                "edited_profile": None,
                "success": False,
                "error": result.get("error")
            }
