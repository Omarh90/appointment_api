import pytest
from datetime import datetime
from appointment_api import *

class TestMainCode:

    #def __init__(self, _input= (38.614407, -92.276468), expected= None):
    #
    #    self.input = _input
    #    self.expected = expected

    def test_mainnoerrors(self, input_=(38.614407, -92.276468)):

        smoketest=False

        try:
            self.actual = main(input_)
            self.type = type(self.actual)
            smoketest=True

        finally:
            assert smoketest
            
    def test_mainreturnsjson(self, input_=(38.614407, -92.276468)):

        isjson=False
        self.actual = main(input_)
            
        try:
            isjson=json.loads(self.actual)
            isjson = bool(isjson)
        finally:
            assert isjson
        #TODO: Integration testing for Main function


class TestRevGeoCode:

    def test_revgeocode(self, input_=[(38.614407, -92.276468),
                                      (37.727104, -88.919200)],
                              expected = [65109, 62959]):

        self.lat1 = input_[0][0]
        self.long1 = input_[0][1]
        self.lat2 = input_[1][0]
        self.long2 = input_[1][1]

        self.expected1 = expected[0]
        self.expected2 = expected[1]
        

        self.actual1 = revgeocode(self.lat1, self.long1)
        self.actual2 = revgeocode(self.lat2, self.long2)

        assert self.expected1 == self.actual1 and \
               self.expected2 == self.actual2

class TestNextAppt:

    def test_nextappt(self, input_ =['g1PlQR'],
                 expected=None):
        
        # Next appointment return based on actual live data. Changes with time."
        # From github example:
        #     1596118800000 = 10/15/2020 7:20 AM
        #    Testing that appointment is within 4 weeks of now: e.g.  < now + 2419200
        self.input = input_
        self.expected = expected
        self.expected_upperbound = datetime.now().timestamp()*1000 + 2419200000 #four weeks out in ms        
        self.actual = nextappt(input_)

        # If expected value is not provided, use upperbound test.
        assert all(self.expected_upperbound > appt_time for appt_time in self.actual.values()) and\
               (self.expected == self.actual or not self.expected)
                   
"""
    # Slightly-informally cramming tests into same module as code
    test_revgeocode = TestRevGeoCode()
    test_nextappt = TestNextAppt()
    test_main = TestMainCode()

    testresult = {'reverse geocode API unit test': test_revgeocode.test_revgeocode(),
                   'next appointment unit test': test_nextappt.test_nextappt(),
                   'smoke test': test_main.test_mainnoerrors(),
                   'returns json test': test_main.test_mainreturnsjson()}
    print("All {} tests passed! Including: {}".format(len(testresult), ", ".join(testresult.keys())))

"""
