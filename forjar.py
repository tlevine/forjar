#! /usr/lib/python

import datetime
import pickle
import random
import string
import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, MetaData, Boolean, Date, Enum, Float, Numeric, PickleType, Text, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import _declarative_constructor

from sqlalchemy import func
from math import ceil

names = pickle.load(open('loaders/names.p', 'rb'))
sites = pickle.load(open('loaders/sites.p', 'rb'))
nouns = pickle.load(open('loaders/nouns.p', 'rb'))

# Periods
MICROSECOND = 1
SECOND = 1000000*MICROSECOND
MINUTE = 60*SECOND
HOUR = 60*MINUTE
DAY = 24*HOUR
WEEK = 7*DAY
MONTH = 30*DAY
YEAR = 365*DAY

date_index = {}

class Base(object):
    count = 0
    ntimes = 0
    def __init__(self, **kwargs):
        forgesession = kwargs.pop('forgesession')
        self.forge(session=forgesession, **kwargs)
        kwargs.pop('basetime')
        _declarative_constructor(self, **kwargs)
        self.__class__.count = self.__class__.count + 1
        forgesession.add(self)
        # commit every 100
        if not self.__class__.count % 100:
           forgesession.commit()

        self.post_forge(forgesession, **kwargs)

    def forge(self, session, **kwargs):
        pass

    def post_forge(self, session, **kwargs):
        pass



Base = declarative_base(cls=Base, constructor=None )

def gen_firstname():
    return random.choice(names['first'])

def gen_lastname():
    return random.choice(names['last'])

def gen_user_fullname(middle=False):
    if middle:
        return "%s %s. %s" % (gen_firstname(), random.choice(string.uppercase), gen_lastname())
    return "%s %s" % (gen_firstname(), gen_lastname())

def gen_email(name):
    return "%s@%s" % (name.split(' ')[0].lower(), random.choice(sites))

def get_noun():
    return random.choice(nouns)

def gen_random_text(low_length=1, high_length=10):
    return ' '.join([get_noun() for a in range(0, random.randint(low_length, high_length))])

def get_random_choice(cnt):
    return random.randrange(0, cnt)

def get_random(Table, session, basetime=None, after=None, choicefunc=get_random_choice):
    date = basetime
    query = session.query(Table)
    cnt = None
    if date is not None:
        if date_index.get(Table.__tablename__, {}).get(date):
            rand_id = random.randint(0, date_index[Table.__tablename__][date]) + 1
            return rand_id
        else:
            query = query.filter(Table.date < date)
            cnt = query.count()
            date_index[Table.__tablename__] = date_index.get(Table.__tablename__, {})
            date_index[Table.__tablename__][date] = cnt

    cnt = cnt or query.count() or 1
    rand_id = get_random_choice(cnt) + 1
    return rand_id

def get_last(Table):
    """return the latest"""
    return Base.count

class Forjaria:

    def __init__(self, start, stop, engine_url, resume = False):

        self.engine_url = engine_url
        self.engine = sqlalchemy.create_engine(engine_url)
        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.start = start
        self.stop = stop
        self.bases = []
        self.clockstart = None

        if not resume:
            self.drop_tables()
            self.create_tables()

    def forge_all(locs, verbose=True):
        # TODO XXX: Fix this function... it doesn't work
        bases = [l for k, l in locs if k != 'Base' and type(l) == type(Base)]
        for Base in bases:
            self.forge_base(Base)

        if verbose:
            self.print_results()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        # drop all tables in the database
        meta = MetaData(self.engine)
        meta.reflect()
        meta.drop_all()

    def print_results(self):
        print "finished in", (datetime.datetime.now() - self.clockstart)
        for Base in self.bases:
            print Base.__tablename__, self.count_base(Base)

    def count_base(self, Base):
        """Returns the # of rows for a Base Table given the Base."""
        return self.session.query(Base).count()

    def forge_base(self, Base, ntimes=None, period=None, variance=None):
        if not self.clockstart:
            self.clockstart = datetime.datetime.now()

        self.bases.append(Base)
        date_index[Base.__tablename__] = {}

        ntimes = ntimes or Base.ntimes
        period = period or Base.period
        variance = variance or Base.variance
        return self.forge(Base, ntimes, period, variance, Base)

    def forge(self, BBase, ntimes, period, variance, Base=None):

        # the variance can be a function
        var = variance
        if type(variance) == int:
            variance = lambda time, iter: var

        nt = ntimes
        if type(ntimes) == int:
            ntimes = lambda time, iter: nt

        iterations = int((self.stop-self.start).total_seconds()/(period/SECOND))
        start = self.start

        epoch = datetime.datetime.utcfromtimestamp(0)
        prevdate = self.session.query(func.max(BBase.date)).scalar()
        if prevdate == None:
            inclusive_time_cutoff = epoch
        else:
            prevdate_microseconds = int(1e6 * (prevdate - epoch).total_seconds())
            prevdate_milliseconds_ceil = period * ceil(prevdate_microseconds / period)
            inclusive_time_cutoff = datetime.datetime.utcfromtimestamp(prevdate_milliseconds_ceil / 1e6)

        for i, time in [(i, start + datetime.timedelta(microseconds=i*period)) for i in range(0, iterations)]:
            if time <= inclusive_time_cutoff:
                continue
            v = int(variance(i, time))
            t = int(ntimes(i, time)) + random.randint(-v, v)
            # print Base.__tablename__, i, 'of', iterations, '-', t
            dts = sorted([random.randint(0, period) for junk in range(0, t)])
            for dt in dts:
                date = time + datetime.timedelta(microseconds=dt)
                date_index[Base.__tablename__][time] = Base.count
                BBase(date=date, forgesession=self.session, basetime=time)

        self.session.commit()


def forjar_main(main, start=datetime.datetime.now() - datetime.timedelta(days=365), stop=datetime.datetime.now(), engine_url="sqlite:///forjar.db"):
    import optparse
    p = optparse.OptionParser()
    p.add_option('--engine_url', '-e', default=engine_url)
    p.add_option('--days', '-d', default=None)
    options, arguments = p.parse_args()
    if options.days is not None:
        stop = datetime.datetime.now()
        start = stop - datetime.timedelta(days=int(options.days))

    forjaria = Forjaria(start, stop, options.engine_url)
    main(forjaria)


