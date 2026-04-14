"""
AR Session Agent.
Automatically logs and analyzes AR try-on sessions.

Actions:
- Logs try-on sessions to database
- Tracks engagement metrics (duration, screenshots)
- Generates analytics insights
- Triggers follow-up actions based on engagement
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.jewelry import Jewelry, TryOnLog
from app.models.product import Product
from app.models.agent_audit import AgentAuditLog
from app.services.jewelry_service import JewelryService


class ARSessionAgent(AgentBase):
    """
    Agent that manages AR try-on session logging and analytics.

    Automatically logs sessions and generates engagement insights.
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)
        self.jewelry_service = JewelryService(db)

    def run(
        self,
        action: str,
        session_data: Optional[Dict[str, Any]] = None,
        product_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        """
        Execute AR session action.

        Args:
            action: Type of action (log_session, analyze_session, generate_insights)
            session_data: Data about the try-on session
            product_id: Product involved in try-on
            session_id: Session identifier

        Returns:
            AgentResult with actions taken
        """
        try:
            self.actions = []

            if action == "log_session":
                self._log_session(session_data, product_id)
            elif action == "analyze_session":
                self._analyze_session(session_id)
            elif action == "generate_insights":
                self._generate_insights(product_id)
            elif action == "batch_log":
                self._batch_log_sessions(session_data or [])
            else:
                return self._create_result(
                    success=False,
                    message=f"Unknown action: {action}",
                )

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"AR session action '{action}' completed",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message=f"AR session action '{action}' failed",
                error=str(e),
            )

    def decide(
        self,
        session_data: Dict[str, Any],
        engagement_threshold: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Decide what actions to take based on session engagement.

        Args:
            session_data: Session metrics
            engagement_threshold: Minimum duration for "engaged" classification

        Returns:
            Decision dict with engagement level and recommended actions
        """
        duration = session_data.get("duration_seconds", 0)
        has_screenshot = bool(session_data.get("screenshot_url"))

        # Classify engagement level
        if duration >= engagement_threshold * 2:
            engagement_level = "high"
        elif duration >= engagement_threshold:
            engagement_level = "medium"
        else:
            engagement_level = "low"

        # Determine recommended actions
        recommended_actions = []

        if engagement_level == "high":
            recommended_actions.append("flag_for_followup")
            recommended_actions.append("add_to_warm_leads")
        elif engagement_level == "medium":
            recommended_actions.append("track_for_analytics")
        else:
            recommended_actions.append("track_only")

        # Use Claude for nuanced decisions on high-engagement sessions
        if engagement_level == "high" and has_screenshot:
            situation = f"""
High-engagement AR session detected:
- Duration: {duration} seconds
- Has screenshot: Yes
- Product: {session_data.get('product_name', 'Unknown')}
- User: {session_data.get('user_id', 'Anonymous')}
"""
            decision = self.claude.generate_decision(
                situation=situation,
                options=[
                    "Send personalized follow-up email",
                    "Add to retargeting campaign",
                    "Offer virtual consultation",
                    "Standard follow-up sequence",
                ],
                criteria="Maximize conversion probability for highly engaged user",
            )

            recommended_actions.append(decision.get("selected_option", "Standard follow-up sequence"))

        return {
            "engagement_level": engagement_level,
            "duration_seconds": duration,
            "recommended_actions": recommended_actions,
            "has_screenshot": has_screenshot,
        }

    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """Execute actions based on decision (called within run methods)."""
        return self.actions

    def _log_session(
        self,
        session_data: Optional[Dict[str, Any]],
        product_id: Optional[UUID],
    ):
        """Log a single try-on session."""
        if not session_data:
            raise ValueError("session_data required")

        if not product_id:
            raise ValueError("product_id required")

        # Validate jewelry exists
        jewelry = self.db.get(Jewelry, product_id)
        if not jewelry:
            raise ValueError(f"Jewelry {product_id} not found")

        # Create try-on log
        tryon_log = TryOnLog(
            product_id=product_id,
            session_id=session_data.get("session_id", f"session_{datetime.utcnow().timestamp()}"),
            user_id=session_data.get("user_id"),
            screenshot_url=session_data.get("screenshot_url"),
            duration_seconds=session_data.get("duration_seconds", 0),
        )

        if not self.dry_run:
            self.db.add(tryon_log)
            self.db.flush()

        # Make engagement decision
        decision = self.decide(session_data)

        self._log_action(
            action_type="LOG_AR_SESSION",
            description=f"Logged AR session for {jewelry.name} - {decision['engagement_level']} engagement ({session_data.get('duration_seconds', 0)}s)",
            entity_type="tryon_log",
            entity_id=tryon_log.id if hasattr(tryon_log, 'id') else None,
            data={
                "product_id": str(product_id),
                "product_name": jewelry.name,
                "session_id": session_data.get("session_id"),
                "duration_seconds": session_data.get("duration_seconds", 0),
                "engagement_level": decision["engagement_level"],
                "user_id": session_data.get("user_id"),
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="LOG_AR_SESSION",
            description=f"AR session logged for {jewelry.name}",
            entity_type="tryon_log",
            entity_id=tryon_log.id if hasattr(tryon_log, 'id') else None,
            action_data={
                "engagement_level": decision["engagement_level"],
                "duration": session_data.get("duration_seconds", 0),
            },
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

    def _analyze_session(self, session_id: Optional[str]):
        """Analyze a specific try-on session."""
        if not session_id:
            raise ValueError("session_id required")

        # Get session logs
        logs = self.db.execute(
            select(TryOnLog).where(TryOnLog.session_id == session_id)
        ).scalars().all()

        if not logs:
            raise ValueError(f"No logs found for session {session_id}")

        # Calculate session metrics
        total_duration = sum(log.duration_seconds or 0 for log in logs)
        products_tried = len(set(log.product_id for log in logs))
        unique_users = len(set(log.user_id for log in logs if log.user_id))

        # Generate analysis
        analysis = {
            "session_id": session_id,
            "total_duration_seconds": total_duration,
            "products_tried": products_tried,
            "unique_users": unique_users,
            "avg_duration_per_product": total_duration / products_tried if products_tried > 0 else 0,
        }

        self._log_action(
            action_type="ANALYZE_AR_SESSION",
            description=f"Analyzed session {session_id}: {products_tried} products, {total_duration}s total",
            entity_type="session",
            data=analysis,
        )

    def _generate_insights(self, product_id: Optional[UUID] = None):
        """Generate AR try-on insights."""
        query = select(TryOnLog)
        if product_id:
            query = query.where(TryOnLog.product_id == product_id)

        logs = self.db.execute(query).scalars().all()

        if not logs:
            self.logger.info("No try-on logs found for insights")
            return

        # Calculate aggregate metrics
        total_sessions = len(logs)
        total_duration = sum(log.duration_seconds or 0 for log in logs)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0

        # Get unique users and sessions
        unique_users = len(set(log.user_id for log in logs if log.user_id))
        unique_sessions = len(set(log.session_id for log in logs))

        # Get products with screenshots
        sessions_with_screens = sum(1 for log in logs if log.screenshot_url)

        insights = {
            "total_tryons": total_sessions,
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "total_duration_seconds": total_duration,
            "average_duration_seconds": round(avg_duration, 2),
            "screenshot_rate": sessions_with_screens / total_sessions if total_sessions > 0 else 0,
        }

        self._log_action(
            action_type="GENERATE_AR_INSIGHTS",
            description=f"Generated insights: {total_sessions} try-ons, {avg_duration:.1f}s avg duration",
            entity_type="analytics",
            data=insights,
        )

    def _batch_log_sessions(self, sessions: List[Dict[str, Any]]):
        """Log multiple sessions in batch."""
        logged_count = 0

        for session_data in sessions:
            product_id = session_data.get("product_id")
            if product_id:
                # Convert string UUID to UUID if needed
                if isinstance(product_id, str):
                    from uuid import UUID as UUIDType
                    try:
                        product_id = UUIDType(product_id)
                    except ValueError:
                        continue

                try:
                    self._log_session(session_data, product_id)
                    logged_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to log session: {e}")

        self.logger.info(f"Batch logged {logged_count} sessions")

    def get_engagement_report(
        self,
        product_id: Optional[UUID] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get engagement report for AR try-ons."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = select(TryOnLog).where(TryOnLog.timestamp >= cutoff_date)
        if product_id:
            query = query.where(TryOnLog.product_id == product_id)

        logs = self.db.execute(query).scalars().all()

        if not logs:
            return {"message": "No data for period"}

        # Calculate engagement distribution
        high_engagement = sum(1 for log in logs if (log.duration_seconds or 0) >= 60)
        medium_engagement = sum(1 for log in logs if 30 <= (log.duration_seconds or 0) < 60)
        low_engagement = sum(1 for log in logs if (log.duration_seconds or 0) < 30)

        return {
            "period_days": days,
            "total_sessions": len(logs),
            "high_engagement": high_engagement,
            "medium_engagement": medium_engagement,
            "low_engagement": low_engagement,
            "engagement_rate": (high_engagement + medium_engagement) / len(logs) if logs else 0,
        }
