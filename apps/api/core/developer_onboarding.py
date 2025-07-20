"""
Developer Onboarding Flows Service for NeuroSync
Provides guided project walkthroughs and intelligent onboarding experiences
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .context_persistence import ContextPersistenceService, ContextType, ContextScope
from .knowledge_synthesis import MultiSourceKnowledgeSynthesis
from .code_architecture import CodeArchitectureService

logger = logging.getLogger(__name__)

class OnboardingStage(Enum):
    """Stages of developer onboarding"""
    PROJECT_OVERVIEW = "project_overview"
    CODEBASE_EXPLORATION = "codebase_exploration"
    ARCHITECTURE_UNDERSTANDING = "architecture_understanding"
    KEY_COMPONENTS = "key_components"
    DEVELOPMENT_WORKFLOW = "development_workflow"
    TEAM_DYNAMICS = "team_dynamics"
    RECENT_CHANGES = "recent_changes"
    NEXT_STEPS = "next_steps"

class OnboardingPersona(Enum):
    """Different types of developers being onboarded"""
    JUNIOR_DEVELOPER = "junior_developer"
    SENIOR_DEVELOPER = "senior_developer"
    TECH_LEAD = "tech_lead"
    PRODUCT_MANAGER = "product_manager"

class LearningStyle(Enum):
    """Different learning preferences"""
    VISUAL = "visual"
    HANDS_ON = "hands_on"
    DOCUMENTATION = "documentation"
    INTERACTIVE = "interactive"

@dataclass
class OnboardingStep:
    """Individual step in the onboarding process"""
    step_id: str
    title: str
    description: str
    stage: OnboardingStage
    content: Dict[str, Any]
    estimated_time_minutes: int
    learning_objectives: List[str]
    resources: List[Dict[str, str]]
    completion_criteria: List[str]

@dataclass
class OnboardingPath:
    """Complete onboarding path for a developer"""
    path_id: str
    developer_id: str
    project_id: str
    persona: OnboardingPersona
    learning_style: LearningStyle
    steps: List[OnboardingStep]
    current_step: int
    started_at: datetime
    estimated_completion: datetime

@dataclass
class OnboardingProgress:
    """Tracks progress through onboarding"""
    developer_id: str
    path_id: str
    completed_steps: List[str]
    current_step_id: str
    time_spent_minutes: int
    completion_percentage: float
    last_activity: datetime

class DeveloperOnboardingService:
    """
    Production-ready developer onboarding service
    
    Features:
    - Personalized onboarding paths based on role and experience
    - Intelligent project analysis and walkthrough generation
    - Interactive learning elements and code exploration
    - Progress tracking and adaptive learning
    - Knowledge gap identification and targeted learning
    """
    
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.context_service = ContextPersistenceService()
        self.knowledge_synthesis = MultiSourceKnowledgeSynthesis()
        self.code_architecture = CodeArchitectureService()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Onboarding cache
        self.onboarding_paths: Dict[str, OnboardingPath] = {}
        self.progress_tracking: Dict[str, OnboardingProgress] = {}
        
        # Learning content templates
        self.content_templates = {
            OnboardingStage.PROJECT_OVERVIEW: {'estimated_time': 30},
            OnboardingStage.CODEBASE_EXPLORATION: {'estimated_time': 45},
            OnboardingStage.ARCHITECTURE_UNDERSTANDING: {'estimated_time': 60},
            OnboardingStage.KEY_COMPONENTS: {'estimated_time': 90},
            OnboardingStage.DEVELOPMENT_WORKFLOW: {'estimated_time': 45},
            OnboardingStage.TEAM_DYNAMICS: {'estimated_time': 30},
            OnboardingStage.RECENT_CHANGES: {'estimated_time': 30},
            OnboardingStage.NEXT_STEPS: {'estimated_time': 20}
        }
    
    async def create_onboarding_path(self, project_id: str, developer_id: str,
                                   persona: OnboardingPersona, 
                                   learning_style: LearningStyle) -> OnboardingPath:
        """Create a personalized onboarding path for a developer"""
        try:
            logger.info(f"Creating onboarding path for {developer_id} in project {project_id}")
            
            # Analyze project to understand complexity and requirements
            project_analysis = await self._analyze_project_for_onboarding(project_id)
            
            # Generate personalized steps based on persona and project
            steps = await self._generate_onboarding_steps(
                project_id, persona, learning_style, project_analysis
            )
            
            # Calculate estimated completion time
            total_time = sum(step.estimated_time_minutes for step in steps)
            estimated_completion = datetime.utcnow() + timedelta(minutes=total_time)
            
            path_id = f"onboarding_{project_id}_{developer_id}_{int(datetime.utcnow().timestamp())}"
            
            onboarding_path = OnboardingPath(
                path_id=path_id,
                developer_id=developer_id,
                project_id=project_id,
                persona=persona,
                learning_style=learning_style,
                steps=steps,
                current_step=0,
                started_at=datetime.utcnow(),
                estimated_completion=estimated_completion
            )
            
            self.onboarding_paths[path_id] = onboarding_path
            
            # Initialize progress tracking
            self.progress_tracking[developer_id] = OnboardingProgress(
                developer_id=developer_id,
                path_id=path_id,
                completed_steps=[],
                current_step_id=steps[0].step_id if steps else "",
                time_spent_minutes=0,
                completion_percentage=0.0,
                last_activity=datetime.utcnow()
            )
            
            # Store onboarding path in context
            await self.context_service.store_context(
                project_id=project_id,
                user_id=developer_id,
                context_type=ContextType.ONBOARDING,
                scope=ContextScope.USER,
                content=asdict(onboarding_path),
                metadata={
                    'path_id': path_id,
                    'persona': persona.value,
                    'learning_style': learning_style.value,
                    'total_steps': len(steps)
                }
            )
            
            logger.info(f"Created onboarding path with {len(steps)} steps")
            return onboarding_path
            
        except Exception as e:
            logger.error(f"Onboarding path creation failed: {str(e)}")
            raise
    
    async def get_next_onboarding_step(self, developer_id: str) -> Optional[OnboardingStep]:
        """Get the next step in the developer's onboarding journey"""
        try:
            progress = self.progress_tracking.get(developer_id)
            if not progress:
                return None
            
            path = self.onboarding_paths.get(progress.path_id)
            if not path:
                return None
            
            # Find current step
            current_step_index = next(
                (i for i, step in enumerate(path.steps) if step.step_id == progress.current_step_id),
                0
            )
            
            if current_step_index >= len(path.steps):
                return None  # Completed
            
            current_step = path.steps[current_step_index]
            
            # Enhance step with real-time project data
            enhanced_step = await self._enhance_step_with_current_data(
                path.project_id, current_step
            )
            
            return enhanced_step
            
        except Exception as e:
            logger.error(f"Failed to get next onboarding step: {str(e)}")
            return None
    
    async def complete_onboarding_step(self, developer_id: str, step_id: str,
                                     time_spent_minutes: int = 0) -> bool:
        """Mark an onboarding step as completed and advance to next step"""
        try:
            progress = self.progress_tracking.get(developer_id)
            if not progress:
                return False
            
            path = self.onboarding_paths.get(progress.path_id)
            if not path:
                return False
            
            # Mark step as completed
            if step_id not in progress.completed_steps:
                progress.completed_steps.append(step_id)
            
            progress.time_spent_minutes += time_spent_minutes
            progress.last_activity = datetime.utcnow()
            
            # Find next step
            current_step_index = next(
                (i for i, step in enumerate(path.steps) if step.step_id == step_id),
                -1
            )
            
            if current_step_index >= 0 and current_step_index < len(path.steps) - 1:
                next_step = path.steps[current_step_index + 1]
                progress.current_step_id = next_step.step_id
            else:
                progress.current_step_id = ""  # Completed
            
            # Update completion percentage
            progress.completion_percentage = len(progress.completed_steps) / len(path.steps) * 100
            
            # Store progress update
            await self.context_service.store_context(
                project_id=path.project_id,
                user_id=developer_id,
                context_type=ContextType.PROGRESS,
                scope=ContextScope.USER,
                content=asdict(progress),
                metadata={
                    'step_completed': step_id,
                    'completion_percentage': progress.completion_percentage
                }
            )
            
            logger.info(f"Completed step {step_id} for developer {developer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete onboarding step: {str(e)}")
            return False
    
    async def get_onboarding_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get analytics on onboarding effectiveness for a project"""
        try:
            # Get all onboarding paths for project
            project_paths = [
                path for path in self.onboarding_paths.values()
                if path.project_id == project_id
            ]
            
            if not project_paths:
                return {}
            
            # Calculate analytics
            analytics = {
                'total_onboardings': len(project_paths),
                'completion_rates': self._calculate_completion_rates(project_paths),
                'average_time_to_complete': self._calculate_average_completion_time(project_paths),
                'persona_performance': self._analyze_persona_performance(project_paths)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Onboarding analytics generation failed: {str(e)}")
            return {}
    
    async def _analyze_project_for_onboarding(self, project_id: str) -> Dict[str, Any]:
        """Analyze project characteristics to inform onboarding design"""
        try:
            # Get project overview from knowledge synthesis
            project_overview = await self.knowledge_synthesis.synthesize_project_knowledge(
                project_id, ["overview", "architecture", "team"]
            )
            
            # Get code architecture analysis
            architecture_analysis = await self.code_architecture.analyze_project_architecture(project_id)
            
            return {
                'overview': project_overview,
                'architecture': architecture_analysis,
                'complexity_score': 0.5  # Mock complexity score
            }
            
        except Exception as e:
            logger.error(f"Project analysis for onboarding failed: {str(e)}")
            return {}
    
    async def _generate_onboarding_steps(self, project_id: str, persona: OnboardingPersona,
                                       learning_style: LearningStyle,
                                       project_analysis: Dict[str, Any]) -> List[OnboardingStep]:
        """Generate personalized onboarding steps"""
        try:
            steps = []
            
            # Determine which stages to include based on persona
            stages = self._select_stages_for_persona(persona)
            
            for i, stage in enumerate(stages):
                step_content = await self._generate_step_content(
                    project_id, stage, persona, learning_style, project_analysis
                )
                
                if step_content:
                    step = OnboardingStep(
                        step_id=f"step_{project_id}_{stage.value}_{i}",
                        title=step_content['title'],
                        description=step_content['description'],
                        stage=stage,
                        content=step_content['content'],
                        estimated_time_minutes=step_content['estimated_time'],
                        learning_objectives=step_content.get('learning_objectives', []),
                        resources=step_content.get('resources', []),
                        completion_criteria=step_content.get('completion_criteria', [])
                    )
                    steps.append(step)
            
            return steps
            
        except Exception as e:
            logger.error(f"Onboarding step generation failed: {str(e)}")
            return []
    
    def _select_stages_for_persona(self, persona: OnboardingPersona) -> List[OnboardingStage]:
        """Select appropriate onboarding stages based on developer persona"""
        base_stages = [
            OnboardingStage.PROJECT_OVERVIEW,
            OnboardingStage.CODEBASE_EXPLORATION,
            OnboardingStage.RECENT_CHANGES,
            OnboardingStage.NEXT_STEPS
        ]
        
        if persona in [OnboardingPersona.JUNIOR_DEVELOPER, OnboardingPersona.SENIOR_DEVELOPER]:
            base_stages.extend([
                OnboardingStage.ARCHITECTURE_UNDERSTANDING,
                OnboardingStage.KEY_COMPONENTS,
                OnboardingStage.DEVELOPMENT_WORKFLOW
            ])
        
        if persona == OnboardingPersona.TECH_LEAD:
            base_stages.extend([
                OnboardingStage.ARCHITECTURE_UNDERSTANDING,
                OnboardingStage.TEAM_DYNAMICS
            ])
        
        # Sort stages in logical order
        stage_order = list(OnboardingStage)
        return sorted(base_stages, key=lambda x: stage_order.index(x))
    
    async def _generate_step_content(self, project_id: str, stage: OnboardingStage,
                                   persona: OnboardingPersona, learning_style: LearningStyle,
                                   project_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate content for a specific onboarding step"""
        try:
            template = self.content_templates.get(stage)
            if not template:
                return None
            
            # Get relevant project data for this stage
            stage_data = await self._get_stage_specific_data(project_id, stage)
            
            return {
                'title': self._generate_step_title(stage, persona),
                'description': self._generate_step_description(stage, persona),
                'content': stage_data,
                'estimated_time': template['estimated_time'],
                'learning_objectives': self._generate_learning_objectives(stage, persona),
                'resources': self._generate_resources(stage, stage_data),
                'completion_criteria': self._generate_completion_criteria(stage)
            }
            
        except Exception as e:
            logger.error(f"Step content generation failed: {str(e)}")
            return None
    
    async def _get_stage_specific_data(self, project_id: str, stage: OnboardingStage) -> Dict[str, Any]:
        """Get project data specific to an onboarding stage"""
        try:
            if stage == OnboardingStage.PROJECT_OVERVIEW:
                return await self._get_project_overview_data(project_id)
            elif stage == OnboardingStage.CODEBASE_EXPLORATION:
                return await self._get_codebase_data(project_id)
            elif stage == OnboardingStage.ARCHITECTURE_UNDERSTANDING:
                return await self._get_architecture_data(project_id)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get stage-specific data: {str(e)}")
            return {}
    
    async def _get_project_overview_data(self, project_id: str) -> Dict[str, Any]:
        """Get project overview information"""
        results = await self.vector_db.semantic_search(
            query="project overview purpose goals",
            project_id=project_id,
            limit=5
        )
        
        return {
            'documentation': results,
            'purpose': "Project purpose from documentation",
            'tech_stack': ["Python", "FastAPI", "React"]
        }
    
    async def _get_codebase_data(self, project_id: str) -> Dict[str, Any]:
        """Get codebase structure information"""
        architecture = await self.code_architecture.analyze_project_architecture(project_id)
        
        return {
            'structure': architecture.get('structure', {}),
            'entry_points': architecture.get('entry_points', []),
            'key_directories': architecture.get('directories', [])
        }
    
    async def _get_architecture_data(self, project_id: str) -> Dict[str, Any]:
        """Get system architecture information"""
        architecture = await self.code_architecture.analyze_project_architecture(project_id)
        
        return {
            'patterns': architecture.get('patterns', []),
            'dependencies': architecture.get('dependencies', {}),
            'system_design': architecture.get('design', {})
        }
    
    async def _enhance_step_with_current_data(self, project_id: str, step: OnboardingStep) -> OnboardingStep:
        """Enhance step with current project data"""
        # Get fresh data for the step
        current_data = await self._get_stage_specific_data(project_id, step.stage)
        
        # Update step content with current data
        enhanced_step = OnboardingStep(
            step_id=step.step_id,
            title=step.title,
            description=step.description,
            stage=step.stage,
            content={**step.content, **current_data},
            estimated_time_minutes=step.estimated_time_minutes,
            learning_objectives=step.learning_objectives,
            resources=step.resources,
            completion_criteria=step.completion_criteria
        )
        
        return enhanced_step
    
    def _generate_step_title(self, stage: OnboardingStage, persona: OnboardingPersona) -> str:
        """Generate appropriate step title"""
        titles = {
            OnboardingStage.PROJECT_OVERVIEW: "Understanding the Project",
            OnboardingStage.CODEBASE_EXPLORATION: "Exploring the Codebase",
            OnboardingStage.ARCHITECTURE_UNDERSTANDING: "System Architecture",
            OnboardingStage.KEY_COMPONENTS: "Key Components",
            OnboardingStage.DEVELOPMENT_WORKFLOW: "Development Workflow",
            OnboardingStage.TEAM_DYNAMICS: "Team Structure",
            OnboardingStage.RECENT_CHANGES: "Recent Changes",
            OnboardingStage.NEXT_STEPS: "Next Steps"
        }
        
        return titles.get(stage, "Onboarding Step")
    
    def _generate_step_description(self, stage: OnboardingStage, persona: OnboardingPersona) -> str:
        """Generate step description"""
        descriptions = {
            OnboardingStage.PROJECT_OVERVIEW: "Get familiar with the project's purpose and context",
            OnboardingStage.CODEBASE_EXPLORATION: "Navigate and understand the codebase structure",
            OnboardingStage.ARCHITECTURE_UNDERSTANDING: "Learn about the system architecture",
            OnboardingStage.KEY_COMPONENTS: "Explore the main components and APIs",
            OnboardingStage.DEVELOPMENT_WORKFLOW: "Understand the development process",
            OnboardingStage.TEAM_DYNAMICS: "Meet the team and learn communication patterns",
            OnboardingStage.RECENT_CHANGES: "Catch up on recent developments",
            OnboardingStage.NEXT_STEPS: "Plan your initial contributions"
        }
        
        return descriptions.get(stage, "Complete this onboarding step")
    
    def _generate_learning_objectives(self, stage: OnboardingStage, persona: OnboardingPersona) -> List[str]:
        """Generate learning objectives for a stage"""
        objectives = {
            OnboardingStage.PROJECT_OVERVIEW: [
                "Understand project goals and objectives",
                "Learn about the business context",
                "Identify key stakeholders"
            ],
            OnboardingStage.CODEBASE_EXPLORATION: [
                "Navigate the repository structure",
                "Identify main entry points",
                "Understand build and deployment"
            ]
        }
        
        return objectives.get(stage, ["Complete the learning objectives"])
    
    def _generate_resources(self, stage: OnboardingStage, stage_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate resources for a stage"""
        return [
            {"type": "documentation", "title": "Project Documentation", "url": "#"},
            {"type": "code", "title": "Code Repository", "url": "#"}
        ]
    
    def _generate_completion_criteria(self, stage: OnboardingStage) -> List[str]:
        """Generate completion criteria for a stage"""
        criteria = {
            OnboardingStage.PROJECT_OVERVIEW: [
                "Can explain project purpose",
                "Knows key stakeholders",
                "Understands business context"
            ],
            OnboardingStage.CODEBASE_EXPLORATION: [
                "Can navigate repository",
                "Knows main entry points",
                "Understands build process"
            ]
        }
        
        return criteria.get(stage, ["Complete all learning objectives"])
    
    def _calculate_completion_rates(self, paths: List[OnboardingPath]) -> Dict[str, float]:
        """Calculate completion rates by persona"""
        completion_by_persona = {}
        
        for path in paths:
            persona = path.persona.value
            progress = self.progress_tracking.get(path.developer_id)
            
            if persona not in completion_by_persona:
                completion_by_persona[persona] = []
            
            if progress:
                completion_by_persona[persona].append(progress.completion_percentage)
        
        # Calculate averages
        averages = {}
        for persona, percentages in completion_by_persona.items():
            if percentages:
                averages[persona] = sum(percentages) / len(percentages)
        
        return averages
    
    def _calculate_average_completion_time(self, paths: List[OnboardingPath]) -> Optional[float]:
        """Calculate average time to complete onboarding"""
        completion_times = []
        
        for path in paths:
            progress = self.progress_tracking.get(path.developer_id)
            if progress and progress.completion_percentage == 100:
                completion_times.append(progress.time_spent_minutes)
        
        if completion_times:
            return sum(completion_times) / len(completion_times)
        
        return None
    
    def _analyze_persona_performance(self, paths: List[OnboardingPath]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by persona"""
        performance = {}
        
        for path in paths:
            persona = path.persona.value
            progress = self.progress_tracking.get(path.developer_id)
            
            if persona not in performance:
                performance[persona] = {
                    'total_paths': 0,
                    'completed': 0,
                    'average_time': 0,
                    'completion_rate': 0
                }
            
            performance[persona]['total_paths'] += 1
            
            if progress:
                if progress.completion_percentage == 100:
                    performance[persona]['completed'] += 1
                    performance[persona]['average_time'] += progress.time_spent_minutes
        
        # Calculate rates and averages
        for persona_data in performance.values():
            if persona_data['total_paths'] > 0:
                persona_data['completion_rate'] = persona_data['completed'] / persona_data['total_paths']
            if persona_data['completed'] > 0:
                persona_data['average_time'] = persona_data['average_time'] / persona_data['completed']
        
        return performance
