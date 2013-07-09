import nose.tools as n
import forjar
import unittest

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    boat_id = Column(Integer, ForeignKey("boats.id"), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    start = Column(DateTime, default=datetime.datetime.utcnow)
    hours = Column(Integer, default=2)

    def forge(self, session, date=None, basetime=None):
        self.start = date + datetime.timedelta(days=random.randint(2, 20))
        self.hours = random.randint(2, 12)
        self.user_id = get_random(User, session, basetime=basetime)
        self.boat_id = get_random(Boat, session, basetime=basetime)

    period = DAY
    @classmethod
    def ntimes(self, i, time):
        return 1*pow(1.006, i)

    variance = ntimes

class TestBase(unittest.TestCase):
    def setUp(self):
        start = datetime.datetime(2013, 7, 1)
        end = datetime.datetime.(2013, 7, 3)
        self.forjaria = forjar.Forjaria(start, stop, 'sqlite:///tmp/test_forjar.db')

    def test_forge_next(self):
        'TestBase.forge_next should ordinarily forge i rows.'
        self.forjaria.forge_next(Trip, i = 100)
        self.forjaria.session.commit()
        n.assert_equal(Trip.__count__, 100)

    def test_forge_last(self):
        'TestBase.forge_next should stop forging at the end.'
        self.forjaria.forge_next(Trip, i = 100)
        self.forjaria.session.commit()
        self.forjaria.forge_next(Trip, i = 100)
        self.forjaria.session.commit()
        print Trip.__count__
        assert False
        # n.assert_equal(Trip.__count__, 100)

        for i, time in [(i, start + datetime.timedelta(microseconds=i*period)) for i in range(0, iterations)]:
