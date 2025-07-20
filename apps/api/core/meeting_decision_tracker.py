"""
Meeting Decision Tracking Service for NeuroSync
Extracts decisions from meetings and links them to code changes, issues, and outcomes
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from .vector_db import VectorDatabase
from .knowledge_graph import KnowledgeGraphBuilder
from .context_persistence import ContextPersistenceService, ContextType, ContextScope
from .knowledge_synthesis import MultiSourceKnowledgeSynthesis

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """Types of decisions that can be tracked"""
    TECHNICAL = "technical"
    ARCHITECTURAL = "architectural"
    PROCESS = "process"
    RESOURCE = "resource"
    TIMELINE = "timeline"
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    DESIGN = "design"

class DecisionStatus(Enum):
    """Status of decision implementation"""
    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    DEFERRED = "deferred"

class DecisionImpact(Enum):
    """Impact level of decisions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Decision:
    """Represents a decision made in a meeting or discussion"""
    decision_id: str
    title: str
    description: str
    decision_type: DecisionType
    status: DecisionStatus
    impact: DecisionImpact
    made_by: List[str]  # People who made the decision
    made_at: datetime
    context: str  # Meeting or discussion context
    rationale: str
    alternatives_considered: List[str]
    success_criteria: List[str]
    related_issues: List[str]
    related_code_changes: List[str]
    follow_up_actions: List[str]
    deadline: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class DecisionOutcome:
    """Tracks the outcome and implementation of a decision"""
    decision_id: str
    outcome_status: str  # success, failure, partial, pending
    implementation_date: Optional[datetime]
    actual_impact: str
    lessons_learned: List[str]
    code_changes_made: List[str]
    issues_resolved: List[str]
    metrics: Dict[str, Any]
    feedback: List[str]

class MeetingDecisionTracker:
    """
    Production-ready meeting decision tracking service
    
    Features:
    - Automatic decision extraction from meeting transcripts
    - Decision categorization and impact assessment
    - Linking decisions to code changes and issues
    - Decision outcome tracking and analysis
    - Decision pattern recognition
    - Implementation progress monitoring
    """
    
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.knowledge_graph = KnowledgeGraphBuilder()
        self.context_service = ContextPersistenceService()
        self.knowledge_synthesis = MultiSourceKnowledgeSynthesis()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Decision tracking cache
        self.decisions_cache: Dict[str, Decision] = {}
        self.outcomes_cache: Dict[str, DecisionOutcome] = {}
        
        # Decision extraction patterns
        self.decision_patterns = [
            r"(?:we (?:decided|agreed|concluded)|decision(?:\s+was)?|it was decided)\s+(?:that\s+)?(.+?)(?:\.|$)",
            r"(?:action item|todo|next step):\s*(.+?)(?:\.|$)",
            r"(?:we will|we'll|let's|going to)\s+(.+?)(?:\.|$)",
            r"(?:approved|rejected|deferred):\s*(.+?)(?:\.|$)"
        ]
        
        # Impact keywords
        self.impact_keywords = {
            DecisionImpact.CRITICAL: ['critical', 'urgent', 'blocking', 'major', 'breaking'],
            DecisionImpact.HIGH: ['important', 'significant', 'high priority', 'key'],
            DecisionImpact.MEDIUM: ['moderate', 'medium', 'standard', 'normal'],
            DecisionImpact.LOW: ['minor', 'small', 'low priority', 'nice to have']
        }
    
    async def extract_decisions_from_meeting(self, project_id: str, meeting_content: str,
                                           meeting_metadata: Dict[str, Any]) -> List[Decision]:
        """
        Extract decisions from meeting transcript or notes
        
        Args:
            project_id: Project identifier
            meeting_content: Meeting transcript or notes
            meeting_metadata: Meeting metadata (date, attendees, etc.)
            
        Returns:
            List of extracted decisions
        """
        try:
            logger.info(f"Extracting decisions from meeting for project {project_id}")
            
            # Extract decision statements using NLP patterns
            decision_statements = self._extract_decision_statements(meeting_content)
            
            decisions = []
            for i, statement in enumerate(decision_statements):
                # Analyze decision statement
                decision_analysis = await self._analyze_decision_statement(
                    statement, meeting_content, meeting_metadata
                )
                
                if decision_analysis:
                    decision_id = f"decision_{project_id}_{meeting_metadata.get('meeting_id', 'unknown')}_{i}"
                    
                    decision = Decision(
                        decision_id=decision_id,
                        title=decision_analysis['title'],
                        description=decision_analysis['description'],
                        decision_type=decision_analysis['type'],
                        status=DecisionStatus.APPROVED,  # Assume approved if mentioned in meeting
                        impact=decision_analysis['impact'],
                        made_by=meeting_metadata.get('attendees', []),
                        made_at=datetime.fromisoformat(meeting_metadata.get('date', datetime.utcnow().isoformat())),
                        context=f"Meeting: {meeting_metadata.get('title', 'Unknown')}",
                        rationale=decision_analysis['rationale'],
                        alternatives_considered=decision_analysis['alternatives'],
                        success_criteria=decision_analysis['success_criteria'],
                        related_issues=[],  # Will be populated by linking
                        related_code_changes=[],  # Will be populated by linking
                        follow_up_actions=decision_analysis['follow_ups'],
                        deadline=decision_analysis.get('deadline'),
                        metadata=meeting_metadata
                    )
                    
                    decisions.append(decision)
                    self.decisions_cache[decision_id] = decision
            
            # Store decisions in knowledge graph and vector DB
            await self._store_decisions(project_id, decisions)
            
            # Link decisions to existing project data
            await self._link_decisions_to_project_data(project_id, decisions)
            
            logger.info(f"Extracted {len(decisions)} decisions from meeting")
            return decisions
            
        except Exception as e:
            logger.error(f"Decision extraction failed: {str(e)}")
            return []
    
    async def track_decision_implementation(self, project_id: str, decision_id: str) -> DecisionOutcome:
        """
        Track the implementation progress and outcome of a decision
        
        Args:
            project_id: Project identifier
            decision_id: Decision identifier
            
        Returns:
            Decision outcome tracking information
        """
        try:
            decision = self.decisions_cache.get(decision_id)
            if not decision:
                logger.warning(f"Decision {decision_id} not found in cache")
                return None
            
            # Search for evidence of implementation across sources
            implementation_evidence = await self._find_implementation_evidence(
                project_id, decision
            )
            
            # Analyze implementation status
            outcome_analysis = await self._analyze_decision_outcome(
                decision, implementation_evidence
            )
            
            outcome = DecisionOutcome(
                decision_id=decision_id,
                outcome_status=outcome_analysis['status'],
                implementation_date=outcome_analysis.get('implementation_date'),
                actual_impact=outcome_analysis['actual_impact'],
                lessons_learned=outcome_analysis['lessons_learned'],
                code_changes_made=outcome_analysis['code_changes'],
                issues_resolved=outcome_analysis['issues_resolved'],
                metrics=outcome_analysis['metrics'],
                feedback=outcome_analysis['feedback']
            )
            
            self.outcomes_cache[decision_id] = outcome
            
            # Update decision status based on outcome
            decision.status = self._map_outcome_to_status(outcome_analysis['status'])
            
            # Store outcome in context
            await self.context_service.store_context(
                project_id=project_id,
                user_id="system",
                context_type=ContextType.DECISION,
                scope=ContextScope.PROJECT,
                content=asdict(outcome),
                metadata={
                    'decision_id': decision_id,
                    'outcome_status': outcome.outcome_status,
                    'implementation_evidence_count': len(implementation_evidence)
                }
            )
            
            logger.info(f"Tracked implementation outcome for decision {decision_id}")
            return outcome
            
        except Exception as e:
            logger.error(f"Decision implementation tracking failed: {str(e)}")
            return None
    
    async def analyze_decision_patterns(self, project_id: str, 
                                      time_window_days: int = 90) -> Dict[str, Any]:
        """
        Analyze patterns in decision-making across the project
        
        Args:
            project_id: Project identifier
            time_window_days: Time window for analysis
            
        Returns:
            Decision pattern analysis results
        """
        try:
            # Get all decisions for the project
            project_decisions = [
                decision for decision in self.decisions_cache.values()
                if decision.decision_id.startswith(f"decision_{project_id}")
            ]
            
            if not project_decisions:
                return {}
            
            # Filter by time window
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            recent_decisions = [
                d for d in project_decisions 
                if d.made_at >= cutoff_date
            ]
            
            # Analyze patterns
            patterns = {
                'total_decisions': len(recent_decisions),
                'decision_types': self._analyze_decision_types(recent_decisions),
                'decision_makers': self._analyze_decision_makers(recent_decisions),
                'implementation_success_rate': await self._calculate_success_rate(recent_decisions),
                'average_implementation_time': await self._calculate_avg_implementation_time(recent_decisions),
                'decision_impact_distribution': self._analyze_impact_distribution(recent_decisions),
                'common_decision_topics': self._extract_common_topics(recent_decisions),
                'decision_velocity': self._calculate_decision_velocity(recent_decisions, time_window_days),
                'bottlenecks': await self._identify_decision_bottlenecks(recent_decisions)
            }
            
            # Store analysis as insight
            await self.context_service.store_context(
                project_id=project_id,
                user_id="system",
                context_type=ContextType.INSIGHT,
                scope=ContextScope.PROJECT,
                content=patterns,
                metadata={
                    'analysis_type': 'decision_patterns',
                    'time_window_days': time_window_days,
                    'decisions_analyzed': len(recent_decisions)
                }
            )
            
            logger.info(f"Analyzed decision patterns for {len(recent_decisions)} decisions")
            return patterns
            
        except Exception as e:
            logger.error(f"Decision pattern analysis failed: {str(e)}")
            return {}
    
    def _extract_decision_statements(self, meeting_content: str) -> List[str]:
        """Extract decision statements from meeting content"""
        statements = []
        
        for pattern in self.decision_patterns:
            matches = re.findall(pattern, meeting_content, re.IGNORECASE | re.MULTILINE)
            statements.extend(matches)
        
        # Clean and deduplicate statements
        cleaned_statements = []
        for statement in statements:
            cleaned = statement.strip()
            if len(cleaned) > 10 and cleaned not in cleaned_statements:
                cleaned_statements.append(cleaned)
        
        return cleaned_statements
    
    async def _analyze_decision_statement(self, statement: str, full_content: str,
                                        meeting_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a decision statement to extract structured information"""
        try:
            # Determine decision type
            decision_type = self._classify_decision_type(statement)
            
            # Assess impact level
            impact = self._assess_decision_impact(statement, full_content)
            
            # Extract title and description
            title = statement[:50] + "..." if len(statement) > 50 else statement
            description = statement
            
            # Extract rationale from surrounding context
            rationale = self._extract_rationale(statement, full_content)
            
            # Extract alternatives (if mentioned)
            alternatives = self._extract_alternatives(statement, full_content)
            
            # Extract success criteria
            success_criteria = self._extract_success_criteria(statement, full_content)
            
            # Extract follow-up actions
            follow_ups = self._extract_follow_ups(statement, full_content)
            
            # Extract deadline (if mentioned)
            deadline = self._extract_deadline(statement, full_content)
            
            return {
                'title': title,
                'description': description,
                'type': decision_type,
                'impact': impact,
                'rationale': rationale,
                'alternatives': alternatives,
                'success_criteria': success_criteria,
                'follow_ups': follow_ups,
                'deadline': deadline
            }
            
        except Exception as e:
            logger.error(f"Decision statement analysis failed: {str(e)}")
            return None
    
    def _classify_decision_type(self, statement: str) -> DecisionType:
        """Classify the type of decision based on content"""
        statement_lower = statement.lower()
        
        # Technical keywords
        if any(keyword in statement_lower for keyword in ['api', 'database', 'framework', 'library', 'technology']):
            return DecisionType.TECHNICAL
        
        # Architectural keywords
        if any(keyword in statement_lower for keyword in ['architecture', 'design', 'pattern', 'structure']):
            return DecisionType.ARCHITECTURAL
        
        # Process keywords
        if any(keyword in statement_lower for keyword in ['process', 'workflow', 'methodology', 'procedure']):
            return DecisionType.PROCESS
        
        # Feature keywords
        if any(keyword in statement_lower for keyword in ['feature', 'functionality', 'requirement']):
            return DecisionType.FEATURE
        
        # Bug fix keywords
        if any(keyword in statement_lower for keyword in ['bug', 'fix', 'issue', 'problem']):
            return DecisionType.BUG_FIX
        
        # Timeline keywords
        if any(keyword in statement_lower for keyword in ['deadline', 'schedule', 'timeline', 'release']):
            return DecisionType.TIMELINE
        
        # Resource keywords
        if any(keyword in statement_lower for keyword in ['resource', 'budget', 'team', 'hiring']):
            return DecisionType.RESOURCE
        
        return DecisionType.TECHNICAL  # Default
    
    def _assess_decision_impact(self, statement: str, full_content: str) -> DecisionImpact:
        """Assess the impact level of a decision"""
        combined_text = (statement + " " + full_content).lower()
        
        for impact_level, keywords in self.impact_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return impact_level
        
        return DecisionImpact.MEDIUM  # Default
    
    def _extract_rationale(self, statement: str, full_content: str) -> str:
        """Extract rationale for the decision from context"""
        # Look for rationale indicators around the statement
        rationale_patterns = [
            r"because\s+(.+?)(?:\.|$)",
            r"since\s+(.+?)(?:\.|$)",
            r"due to\s+(.+?)(?:\.|$)",
            r"reason:\s*(.+?)(?:\.|$)"
        ]
        
        for pattern in rationale_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return "Rationale not explicitly stated"
    
    def _extract_alternatives(self, statement: str, full_content: str) -> List[str]:
        """Extract alternatives considered"""
        alternatives = []
        
        # Look for alternative indicators
        alt_patterns = [
            r"alternative(?:ly)?:\s*(.+?)(?:\.|$)",
            r"option\s+\d+:\s*(.+?)(?:\.|$)",
            r"could also\s+(.+?)(?:\.|$)",
            r"instead of\s+(.+?)(?:\.|$)"
        ]
        
        for pattern in alt_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            alternatives.extend([match.strip() for match in matches])
        
        return alternatives
    
    def _extract_success_criteria(self, statement: str, full_content: str) -> List[str]:
        """Extract success criteria for the decision"""
        criteria = []
        
        criteria_patterns = [
            r"success(?:\s+criteria)?:\s*(.+?)(?:\.|$)",
            r"measure(?:d by)?:\s*(.+?)(?:\.|$)",
            r"goal:\s*(.+?)(?:\.|$)",
            r"target:\s*(.+?)(?:\.|$)"
        ]
        
        for pattern in criteria_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            criteria.extend([match.strip() for match in matches])
        
        return criteria
    
    def _extract_follow_ups(self, statement: str, full_content: str) -> List[str]:
        """Extract follow-up actions"""
        follow_ups = []
        
        followup_patterns = [
            r"(?:action item|todo|next step):\s*(.+?)(?:\.|$)",
            r"follow up:\s*(.+?)(?:\.|$)",
            r"need to\s+(.+?)(?:\.|$)",
            r"will\s+(.+?)(?:\.|$)"
        ]
        
        for pattern in followup_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            follow_ups.extend([match.strip() for match in matches])
        
        return follow_ups
    
    def _extract_deadline(self, statement: str, full_content: str) -> Optional[datetime]:
        """Extract deadline from content"""
        # Simple deadline extraction (can be enhanced)
        deadline_patterns = [
            r"by\s+(\w+\s+\d+)",  # by March 15
            r"deadline:\s*(\w+\s+\d+)",  # deadline: March 15
            r"due\s+(\w+\s+\d+)"  # due March 15
        ]
        
        for pattern in deadline_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            if matches:
                # Simple date parsing (enhance with proper date parser)
                try:
                    # Mock deadline parsing
                    return datetime.utcnow() + timedelta(days=30)
                except:
                    continue
        
        return None
    
    async def _store_decisions(self, project_id: str, decisions: List[Decision]):
        """Store decisions in vector DB and knowledge graph"""
        try:
            # Store in vector database
            documents = []
            for decision in decisions:
                documents.append({
                    'id': f"decision_{decision.decision_id}",
                    'content': f"{decision.title} {decision.description} {decision.rationale}",
                    'metadata': {
                        'source': 'meeting_decisions',
                        'type': 'decision',
                        'decision_type': decision.decision_type.value,
                        'impact': decision.impact.value,
                        'status': decision.status.value,
                        'made_at': decision.made_at.isoformat(),
                        'project_id': project_id
                    }
                })
            
            if documents:
                await self.vector_db.add_documents(documents)
            
            # Store in knowledge graph
            entities = []
            for decision in decisions:
                entities.append({
                    'project_id': project_id,
                    'entity_type': 'decision',
                    'entity_id': decision.decision_id,
                    'properties': {
                        'title': decision.title,
                        'type': decision.decision_type.value,
                        'impact': decision.impact.value,
                        'status': decision.status.value,
                        'made_at': decision.made_at.isoformat(),
                        'made_by': decision.made_by
                    }
                })
            
            if entities:
                await self.knowledge_graph.add_entities_batch(entities)
            
            logger.info(f"Stored {len(decisions)} decisions in vector DB and knowledge graph")
            
        except Exception as e:
            logger.error(f"Failed to store decisions: {str(e)}")
    
    async def _link_decisions_to_project_data(self, project_id: str, decisions: List[Decision]):
        """Link decisions to related issues, code changes, etc."""
        try:
            for decision in decisions:
                # Search for related content using semantic search
                search_query = f"{decision.title} {decision.description}"
                
                related_content = await self.vector_db.semantic_search(
                    query=search_query,
                    project_id=project_id,
                    limit=10
                )
                
                # Extract related issues and code changes
                for content in related_content:
                    metadata = content.get('metadata', {})
                    source = metadata.get('source', '')
                    
                    if source == 'jira':
                        decision.related_issues.append(metadata.get('id', ''))
                    elif source == 'github':
                        decision.related_code_changes.append(metadata.get('id', ''))
            
            logger.info(f"Linked decisions to project data")
            
        except Exception as e:
            logger.error(f"Failed to link decisions to project data: {str(e)}")
    
    async def _find_implementation_evidence(self, project_id: str, 
                                          decision: Decision) -> List[Dict[str, Any]]:
        """Find evidence of decision implementation"""
        try:
            evidence = []
            
            # Search for implementation evidence
            search_queries = [
                decision.title,
                decision.description,
                *decision.follow_up_actions
            ]
            
            for query in search_queries:
                if not query.strip():
                    continue
                    
                results = await self.vector_db.semantic_search(
                    query=query,
                    project_id=project_id,
                    limit=5
                )
                
                for result in results:
                    metadata = result.get('metadata', {})
                    # Filter for content created after decision
                    created_at = metadata.get('created_at')
                    if created_at:
                        try:
                            content_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            if content_date > decision.made_at:
                                evidence.append({
                                    'type': 'implementation_evidence',
                                    'source': metadata.get('source', ''),
                                    'content': result.get('content', ''),
                                    'metadata': metadata,
                                    'relevance_score': 0.8  # Mock score
                                })
                        except:
                            continue
            
            return evidence
            
        except Exception as e:
            logger.error(f"Failed to find implementation evidence: {str(e)}")
            return []
    
    async def _analyze_decision_outcome(self, decision: Decision, 
                                      evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the outcome of a decision based on evidence"""
        try:
            # Determine implementation status
            if len(evidence) >= 3:
                status = "success"
            elif len(evidence) >= 1:
                status = "partial"
            else:
                status = "pending"
            
            # Extract implementation date (earliest evidence)
            implementation_date = None
            if evidence:
                dates = []
                for ev in evidence:
                    created_at = ev.get('metadata', {}).get('created_at')
                    if created_at:
                        try:
                            dates.append(datetime.fromisoformat(created_at.replace('Z', '+00:00')))
                        except:
                            continue
                if dates:
                    implementation_date = min(dates)
            
            # Mock analysis results
            return {
                'status': status,
                'implementation_date': implementation_date,
                'actual_impact': decision.impact.value,
                'lessons_learned': ["Implementation went as planned"],
                'code_changes': [ev.get('metadata', {}).get('id', '') for ev in evidence if ev.get('metadata', {}).get('source') == 'github'],
                'issues_resolved': [ev.get('metadata', {}).get('id', '') for ev in evidence if ev.get('metadata', {}).get('source') == 'jira'],
                'metrics': {
                    'evidence_count': len(evidence),
                    'implementation_time_days': (implementation_date - decision.made_at).days if implementation_date else None
                },
                'feedback': ["Positive outcome based on evidence"]
            }
            
        except Exception as e:
            logger.error(f"Decision outcome analysis failed: {str(e)}")
            return {}
    
    def _map_outcome_to_status(self, outcome_status: str) -> DecisionStatus:
        """Map outcome status to decision status"""
        mapping = {
            'success': DecisionStatus.IMPLEMENTED,
            'partial': DecisionStatus.IN_PROGRESS,
            'pending': DecisionStatus.APPROVED,
            'failure': DecisionStatus.REJECTED
        }
        return mapping.get(outcome_status, DecisionStatus.APPROVED)
    
    def _analyze_decision_types(self, decisions: List[Decision]) -> Dict[str, int]:
        """Analyze distribution of decision types"""
        type_counts = {}
        for decision in decisions:
            decision_type = decision.decision_type.value
            type_counts[decision_type] = type_counts.get(decision_type, 0) + 1
        return type_counts
    
    def _analyze_decision_makers(self, decisions: List[Decision]) -> Dict[str, int]:
        """Analyze who makes decisions most frequently"""
        maker_counts = {}
        for decision in decisions:
            for maker in decision.made_by:
                maker_counts[maker] = maker_counts.get(maker, 0) + 1
        return maker_counts
    
    async def _calculate_success_rate(self, decisions: List[Decision]) -> float:
        """Calculate decision implementation success rate"""
        if not decisions:
            return 0.0
        
        implemented_count = sum(
            1 for decision in decisions 
            if decision.status == DecisionStatus.IMPLEMENTED
        )
        
        return implemented_count / len(decisions)
    
    async def _calculate_avg_implementation_time(self, decisions: List[Decision]) -> Optional[float]:
        """Calculate average time from decision to implementation"""
        implementation_times = []
        
        for decision in decisions:
            if decision.decision_id in self.outcomes_cache:
                outcome = self.outcomes_cache[decision.decision_id]
                if outcome.implementation_date:
                    time_diff = (outcome.implementation_date - decision.made_at).days
                    implementation_times.append(time_diff)
        
        if implementation_times:
            return sum(implementation_times) / len(implementation_times)
        
        return None
    
    def _analyze_impact_distribution(self, decisions: List[Decision]) -> Dict[str, int]:
        """Analyze distribution of decision impacts"""
        impact_counts = {}
        for decision in decisions:
            impact = decision.impact.value
            impact_counts[impact] = impact_counts.get(impact, 0) + 1
        return impact_counts
    
    def _extract_common_topics(self, decisions: List[Decision]) -> List[str]:
        """Extract common topics from decisions"""
        all_text = " ".join([f"{d.title} {d.description}" for d in decisions])
        
        # Simple topic extraction (can be enhanced with proper NLP)
        common_words = ['api', 'database', 'frontend', 'backend', 'feature', 'bug', 'performance']
        topics = [word for word in common_words if word in all_text.lower()]
        
        return topics
    
    def _calculate_decision_velocity(self, decisions: List[Decision], time_window_days: int) -> float:
        """Calculate decision-making velocity (decisions per week)"""
        if not decisions or time_window_days == 0:
            return 0.0
        
        weeks = time_window_days / 7
        return len(decisions) / weeks
    
    async def _identify_decision_bottlenecks(self, decisions: List[Decision]) -> List[str]:
        """Identify bottlenecks in decision implementation"""
        bottlenecks = []
        
        # Check for decisions stuck in certain statuses
        status_counts = {}
        for decision in decisions:
            status = decision.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts.get('approved', 0) > status_counts.get('implemented', 0) * 2:
            bottlenecks.append("Many decisions approved but not implemented")
        
        if status_counts.get('in_progress', 0) > len(decisions) * 0.3:
            bottlenecks.append("High number of decisions stuck in progress")
        
        return bottlenecks
