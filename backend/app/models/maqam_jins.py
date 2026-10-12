from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class MaqamJins(Base):
    """
    Ordered breakdown of every jins a maqam is built from.

    `Maqam.root_jins_id` / `Maqam.branch_jins_id` (kept as-is, still used by
    the existing Maqamat browsing UI) only have room for two ajnas, but real
    maqamat can overlap three or more ajnas at different scale degrees (e.g.
    Saba: Jins Saba at degree 1, Jins Hijaz at degree 3, Jins 'Ajam/Nikriz
    at degree 6), and several maqamat document two valid alternatives at the
    same degree ("Jins Nahawand OR Jins Hijaz on the 5th degree"). This
    table is the extensible source the Maqam Explorer reads for its full
    ajnas breakdown; it doesn't replace the two columns above.
    """

    __tablename__ = "maqam_ajnas"

    id = Column(Integer, primary_key=True, index=True)

    maqam_id = Column(Integer, ForeignKey("maqamat.id"), nullable=False, index=True)
    jins_id = Column(Integer, ForeignKey("ajnas.id"), nullable=False)

    # 1-based scale degree of the maqam where this jins begins.
    start_degree = Column(Integer, nullable=False)

    # When a source documents multiple valid ajnas at the same degree
    # ("either Jins 'Ajam or Jins Nikriz"), the better-corroborated one is
    # True; alternatives are still recorded (not dropped) with False.
    is_primary_alternative = Column(Boolean, nullable=False, default=True)

    # e.g. "Documented alternative to Jins Nikriz at this degree (maqamworld.com)."
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    maqam = relationship("Maqam", back_populates="ajnas_breakdown")
    jins = relationship("Jins")
