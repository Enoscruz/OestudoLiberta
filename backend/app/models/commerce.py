"""Modelos comerciais: compra, pagamento e liberação de acesso."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EnrollmentStatus, Gateway, PaymentStatus, PurchaseStatus
from app.models.base import Base, CreatedAtMixin, IdMixin, enum_type

if TYPE_CHECKING:
    from app.models.content import Course
    from app.models.user import User


class Purchase(IdMixin, CreatedAtMixin, Base):
    """Compra de um curso realizada por um aluno.

    Cada compra se refere a **um** curso (modelo de pagamento por curso): é este
    vínculo que permite liberar o acesso quando o pagamento é aprovado.
    """

    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0.00")
    )
    status: Mapped[PurchaseStatus] = mapped_column(
        enum_type(PurchaseStatus, "purchase_status", 20),
        nullable=False,
        server_default=PurchaseStatus.PENDING.value,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="purchases")
    course: Mapped[Course] = relationship(back_populates="purchases")
    payments: Mapped[list[Payment]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="purchase")

    def __repr__(self) -> str:
        return f"<Purchase {self.id} - {self.status}>"


class Payment(IdMixin, CreatedAtMixin, Base):
    """Pagamento associado a uma compra."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        UniqueConstraint(
            "gateway",
            "external_payment_id",
            name="uq_payments_gateway_external_payment_id",
        ),
    )

    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gateway: Mapped[Gateway] = mapped_column(
        enum_type(Gateway, "payment_gateway", 30),
        nullable=False,
        server_default=Gateway.MERCADO_PAGO.value,
    )
    external_payment_id: Mapped[str | None] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0.00")
    )
    status: Mapped[PaymentStatus] = mapped_column(
        enum_type(PaymentStatus, "payment_status", 20),
        nullable=False,
        server_default=PaymentStatus.PENDING.value,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    purchase: Mapped[Purchase] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment {self.id} - {self.status}>"


class Enrollment(IdMixin, Base):
    """Direito de acesso de um aluno a um curso (criado após o pagamento)."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_id_course_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        enum_type(EnrollmentStatus, "enrollment_status", 20),
        nullable=False,
        server_default=EnrollmentStatus.ACTIVE.value,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="enrollments")
    course: Mapped[Course] = relationship(back_populates="enrollments")
    purchase: Mapped[Purchase] = relationship(back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment user={self.user_id} course={self.course_id}>"
