import random
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.crm import exceptions, models, schemas


class CRMService:
    """Service handling business logic for operators, sources, and lead distribution."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_operator(self, data: schemas.OperatorCreate) -> models.Operator:
        """Creates a new operator."""
        operator = models.Operator(**data.model_dump())
        self.session.add(operator)
        await self.session.commit()
        await self.session.refresh(operator)
        return operator

    async def get_operators(self) -> List[models.Operator]:
        """Retrieves all operators."""
        query = select(models.Operator)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_source(self, data: schemas.SourceCreate) -> models.Source:
        """Creates a new source (bot)."""
        source = models.Source(name=data.name)
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def configure_source_distribution(
            self, source_id: int, config: schemas.SourceConfigUpdate
    ):
        """Configures operators and weights for a specific source."""
        source = await self.session.get(models.Source, source_id)
        if not source:
            raise exceptions.SourceNotFound()

        # clear existing links
        query = select(models.SourceOperatorLink).where(
            models.SourceOperatorLink.source_id == source_id
        )
        existing = await self.session.execute(query)
        for link in existing.scalars():
            await self.session.delete(link)

        # add new links
        for item in config.operators:
            link = models.SourceOperatorLink(
                source_id=source_id,
                operator_id=item.operator_id,
                weight=item.weight,
            )
            self.session.add(link)

        await self.session.commit()

    async def _get_or_create_lead(self, identifier: str) -> models.Lead:
        """Finds an existing lead or creates a new one based on unique identifier."""
        query = select(models.Lead).where(models.Lead.identifier == identifier)
        result = await self.session.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            lead = models.Lead(identifier=identifier)
            self.session.add(lead)
            await self.session.flush()

        return lead

    async def _select_operator(self, source_id: int) -> Optional[models.Operator]:
        """
        Selects an operator based on weights, activity status, and load limits.

        Algorithm:
        1. Fetch all operators linked to the source.
        2. Filter active operators.
        3. Calculate current load (OPEN cases) for each candidate.
        4. Filter out operators who reached max_load.
        5. If candidates remain, pick one using weighted random selection.
        """
        # Fetch links with operator data
        stmt = (
            select(models.SourceOperatorLink)
            .options(selectinload(models.SourceOperatorLink.operator))
            .where(models.SourceOperatorLink.source_id == source_id)
        )
        result = await self.session.execute(stmt)
        links = result.scalars().all()

        candidates: List[Tuple[models.Operator, int]] = []

        for link in links:
            operator = link.operator
            if not operator.is_active:
                continue

            # Calculate current load
            # Note: For high-load systems, this should be a counter in Redis or denormalized field.
            # For this task, a count query is sufficient and reliable.
            load_query = select(func.count(models.Case.id)).where(
                models.Case.operator_id == operator.id,
                models.Case.status == models.CaseStatus.OPEN
            )
            load_res = await self.session.execute(load_query)
            current_load = load_res.scalar() or 0

            if current_load < operator.max_load:
                candidates.append((operator, link.weight))

        if not candidates:
            return None

        # Weighted random selection
        operators = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]

        selected = random.choices(population=operators, weights=weights, k=1)[0]
        return selected

    async def process_new_case(self, data: schemas.CaseCreate) -> models.Case:
        """
        Registers a new case from a lead, assigning an operator automatically.
        """
        # 1. Resolve Lead
        lead = await self._get_or_create_lead(data.lead_identifier)

        # 2. Select Operator
        operator = await self._select_operator(data.source_id)

        # 3. Create Case
        new_case = models.Case(
            lead_id=lead.id,
            source_id=data.source_id,
            operator_id=operator.id if operator else None,
            status=models.CaseStatus.OPEN
        )

        self.session.add(new_case)
        await self.session.commit()
        await self.session.refresh(new_case)

        return new_case

    async def get_all_cases(self) -> List[models.Case]:
        """Retrieves all cases with related entities loaded."""
        query = (
            select(models.Case)
            .options(selectinload(models.Case.lead))
            .order_by(models.Case.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())