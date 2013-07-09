import datetime
import random
import unittest

import nose.tools as n

from forjar import Base, Forjaria, DAY
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, MetaData, Boolean, Date, Enum, Float, Numeric, PickleType, Text, Time

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

class TestForjaria(unittest.TestCase):

    def test_not_resume(self):
        'The database should be cleared when resume is False.'
        start = datetime.datetime(2013, 5, 1)

        stop1  = datetime.datetime(2013, 7, 1)
        forjaria = Forjaria(start, stop1, 'sqlite:////tmp/test_forjar.db', resume = False)
        forjaria.forge_base(Trip)

        trip1 = forjaria.session.query(Trip).get(1)
        trip1.hours = 9001
        forjaria.session.add(trip1)
        forjaria.session.commit()

        stop2  = datetime.datetime(2013, 9, 1)
        forjaria = Forjaria(start, stop2, 'sqlite:////tmp/test_forjar.db', resume = False)
        forjaria.forge_base(Trip)

        n.assert_not_equal(forjaria.session.query(Trip).get(1).hours, 9001)

    def test_resume(self):
        'The database should not be cleared when resume is True.'
        start = datetime.datetime(2013, 5, 1)

        stop1  = datetime.datetime(2013, 7, 1)
        forjaria = Forjaria(start, stop1, 'sqlite:////tmp/test_forjar.db', resume = False)
        forjaria.forge_base(Trip)

        trip1 = forjaria.session.query(Trip).get(1)
        trip1.hours = 9001
        forjaria.session.add(trip1)
        forjaria.session.commit()

        stop2  = datetime.datetime(2013, 9, 1)
        forjaria = Forjaria(start, stop2, 'sqlite:////tmp/test_forjar.db', resume = True)
        forjaria.forge_base(Trip)

        n.assert_equal(forjaria.session.query(Trip).get(1).hours, 9001)

    def test_skip_on_resume(self):
        'On a resume, the previous dates should be skipped.'
        start = datetime.datetime(2013, 5, 1)

        stop1  = datetime.datetime(2013, 7, 1)
        stop2  = datetime.datetime(2013, 9, 1)

        forjaria = Forjaria(start, stop1, 'sqlite:////tmp/test_forjar.db', resume = False)
        forjaria.forge_base(Trip)
        forjaria.session.commit()

        forjaria = Forjaria(start, stop2, 'sqlite:////tmp/test_forjar.db', resume = True)
        forjaria.forge_base(Trip)
        c1 = forjaria.count_base(Trip)
        forjaria.session.commit()

        forjaria = Forjaria(start, stop2, 'sqlite:////tmp/test_forjar.db', resume = False)
        forjaria.forge_base(Trip)
        c2 = forjaria.count_base(Trip)
        forjaria.session.commit()

        n.assert_equal(c1, c2)
