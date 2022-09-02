import sqlalchemy

class Database:
    def __init__(self, DATABASE_FILE):
        return
        self.engine = sqlalchemy.create_engine("sqlite:///" + DATABASE_FILE)
        self.metadata = sqlalchemy.MetaData()
        self.create_tables()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        return
        Base.metadata.create_all(self.engine)
