from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    A common DeclarativeBase subclass for all SQLAlchemy models to inherit.
    Why: All mapping schemas will compile attributes onto this metadata object automatically.
    """
    pass
