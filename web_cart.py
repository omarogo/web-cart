from app import app, db
from app.models import Users, Markets, Buys

import sqlalchemy as sa
import sqlalchemy.orm as so

@app.shell_context_processor
def make_shell_context():
    return {"sa": sa, "so": so, "db": db, "Users": Users, "Buys": Buys, "Markets": Markets}