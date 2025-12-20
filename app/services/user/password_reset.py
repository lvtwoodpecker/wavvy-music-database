from datetime import datetime, timedelta
import secrets
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.sqlalchemy_engine import engine
from app.models.User import User
from app.models.PasswordResetToken import PasswordResetToken

class PasswordResetService:
    def __init__(self, db_session_factory):
        self._db_session_factory = db_session_factory
        self._ensure_table()

    def _ensure_table(self):
        # Ensure table exists even if models were not imported before create_all
        try:
            PasswordResetToken.__table__.create(bind=engine, checkfirst=True)
        except Exception:
            # Best-effort; continue if table exists or create fails
            pass

    def request_reset(self, email: str) -> Optional[str]:
        session: Session = self._db_session_factory()
        try:
            user: Optional[User] = session.query(User).filter(User.email == email).first()
            if not user:
                return None
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            prt = PasswordResetToken(user_id=user.user_id, token=token, expires_at=expires_at, used=False)
            session.add(prt)
            session.commit()
            return token
        except IntegrityError:
            session.rollback()
            # In rare case token collision, retry with new token
            token = secrets.token_urlsafe(48)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            prt = PasswordResetToken(user_id=user.user_id, token=token, expires_at=expires_at, used=False)
            session.add(prt)
            session.commit()
            return token
        finally:
            session.close()

    def reset_with_token(self, token: str, new_password_hash: str) -> bool:
        session: Session = self._db_session_factory()
        try:
            prt: Optional[PasswordResetToken] = (
                session.query(PasswordResetToken)
                .filter(PasswordResetToken.token == token)
                .first()
            )
            if not prt or prt.used:
                return False
            if prt.expires_at and prt.expires_at < datetime.utcnow():
                return False
            user: Optional[User] = session.query(User).filter(User.user_id == prt.user_id).first()
            if not user:
                return False
            user.password_hash = new_password_hash
            prt.used = True
            session.add(user)
            session.add(prt)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def change_password(self, user_id: int, old_password: str, new_password_hash: str, verify_fn) -> bool:
        session: Session = self._db_session_factory()
        try:
            user: Optional[User] = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False
            if not verify_fn(old_password, user.password_hash):
                return False
            user.password_hash = new_password_hash
            session.add(user)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
