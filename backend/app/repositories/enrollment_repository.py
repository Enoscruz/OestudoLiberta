"""Acesso a dados de matrículas (acesso do aluno a um curso)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import EnrollmentStatus
from app.models.commerce import Enrollment
from app.models.content import Course


def list_active_by_user(db: Session, user_id: int) -> list[Enrollment]:
    """Lista as matrículas ativas de um aluno, da mais recente para a mais antiga."""
    stmt = (
        select(Enrollment)
        .options(joinedload(Enrollment.course).joinedload(Course.category))
        .where(
            Enrollment.user_id == user_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(Enrollment.granted_at.desc())
    )
    return list(db.execute(stmt).unique().scalars())


def get_active(db: Session, user_id: int, course_id: int) -> Enrollment | None:
    """Busca a matrícula ativa de um aluno em um curso."""
    stmt = select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
        Enrollment.status == EnrollmentStatus.ACTIVE,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_any(db: Session, user_id: int, course_id: int) -> Enrollment | None:
    """Busca a matrícula de um aluno em um curso, qualquer que seja a situação."""
    stmt = select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def create(db: Session, *, user_id: int, course_id: int, purchase_id: int) -> Enrollment:
    """Concede acesso de um aluno a um curso."""
    enrollment = Enrollment(
        user_id=user_id, course_id=course_id, purchase_id=purchase_id
    )
    db.add(enrollment)
    return enrollment
