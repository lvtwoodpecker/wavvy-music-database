from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.sqlalchemy_engine import Base

class Advertiser(Base):
    __tablename__ = "Advertiser"
    __table_args__ = {"schema": "public"}

    advertiser_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("public.User.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    user = relationship("User", back_populates="advertiser_profile")
