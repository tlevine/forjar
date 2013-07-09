import datetime
import random
import unittest

import nose.tools as n

from forjar import Base, Column, Forjaria, Integer, ForeignKey, DateTime, DAY

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    start = Column(DateTime, default=datetime.datetime.utcnow)
    hours = Column(Integer, default=2)

    def forge(self, session, date=None, basetime=None):
        self.start = date + datetime.timedelta(days=random.randint(2, 20))
        self.hours = random.randint(2, 12)

    period = DAY
    ntimes = 1
    variance = 0

class TestBase(unittest.TestCase):
    def setUp(self):
        start = datetime.datetime(2013, 5, 1)
        stop  = datetime.datetime(2013, 7, 1)
        self.forjaria = Forjaria(start, stop, 'sqlite:////tmp/test_forjar.db', commit_every = 50)

    def test_forge_next(self):
        'TestBase.forge_next should ordinarily forge i iterations.'
        self.forjaria.forge_next(Trip)
        self.forjaria.session.commit()
        n.assert_equal(self.forjaria.i, 50)
        n.assert_equal(self.forjaria.count_base(Trip), 50)

    def test_forge_last(self):
        'TestBase.forge_next should stop forging at the end.'
        self.forjaria.forge_next(Trip)
        self.forjaria.session.commit()
        self.forjaria.forge_next(Trip)
        self.forjaria.session.commit()
        n.assert_equal(self.forjaria.i, 61)
        n.assert_equal(self.forjaria.count_base(Trip), 61)

    def test_no_commit(self):
        'TestBase.forge_next should not commit.'
        self.forjaria.forge_next(Trip)
        self.forjaria.session.rollback()
        n.assert_equal(self.forjaria.i, 0)
        n.assert_equal(self.forjaria.count_base(Trip), 0)
