#!/usr/bin/python2.7
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
#from sqlalchemy import create_engine
from json import dumps
import logging as LOG
from structs import *

#db_connect = create_engine('sqlite:///chinook.db')

class LSAA(Resource):

    MSG_TYPES = { 1L: "HELLO",
              2L: "DBDESC",
              3L: "LSREQ",
              4L: "LSUPD",
              5L: "LSACK",
        	      }

    LSAV3_TYPES = { 8193: "ROUTER",             # links between routers in the area, 0X2001
              8194: "NETWORK",            # links between "networks" in the area, 0X2002
              8195: "INTER AREA PREFIX",
              8196: "INTER AREA ROUTER",
              16389: "EXTERNAL AS",   #0X4005

              8198: "GROUP MEMBER", #0X2006
              8199: "NSSA",
              8: "LINK LSA", #0X0008
              8201: "INTRA AREA PREFIX", #0X2009
              }
    G = G() #List of vertexcies representing routers

    #def get(self):
        #conn = db_connect.connect() # connect to database
        #query = conn.execute("select * from employees") # This line performs query and returns json result
        #return {'employees': [i[0] for i in query.cursor.fetchall()]} # Fetches first column that is Employee ID


    def _process_rtr_lsa(self, lsa, lsid, advrtr):
	LOG.info("Router LSA: lsid:%s, advrtr:%s" % (lsid, advrtr))
	LOG.info("Router LSA: %s\n\n" % lsa)

	

    def _process_link_lsa(self, lsa, lsid, advrtr):
	LOG.info("Link LSA: lsid:%s, advrtr:%s" % (lsid, advrtr))
	LOG.info("Link LSA: %s\n\n" % lsa)

    def _process_network_lsa(self, lsa, lsid, advrtr):
	LOG.info("Network LSA: lsid:%s, advrtr:%s" % (lsid, advrtr))
	LOG.info("Network LSA: %s\n\n"% lsa)

    def _process_intraareaprefix_lsa(self, lsa, lsid, advrtr):
	LOG.info("Intra Area Prefix LSA: lsid:%s, advrtr:%s" % (lsid, advrtr))
	LOG.info("Intra Area Prefix LSA: %s\n\n" % lsa)



    def post(self):
        req = request.json
	t = int(req['T'])
	if self.MSG_TYPES[t] == "LSUPD": 
		v = req['V']['V']
		lsas = v['LSAS']
		LOG.debug("Received LSUDP=%s" % v)
		for k in lsas:
			lsa = lsas[k]
			t = int(lsa['T'])
			lsid = int(lsa['H']['LSID'])
			advrtr = int(lsa['H']['ADVRTR'])

			if self.LSAV3_TYPES[t] == "ROUTER":
				self._process_rtr_lsa(lsa['V'], lsid, advrtr)
			elif self.LSAV3_TYPES[t] == "NETWORK":
				self._process_network_lsa(lsa['V'], lsid, advrtr)
			elif self.LSAV3_TYPES[t] == "LINK LSA":
				self._process_link_lsa(lsa['V'], lsid, advrtr)
			elif self.LSAV3_TYPES[t] == "INTRA AREA PREFIX":
				self._process_intraareaprefix_lsa(lsa['V'], lsid, advrtr)
			else:
				LOG.warn("Received Unknown LSA, type:%s, lsid:%s, advrtr:%s" % (t, lsid, advrtr))
	
        #query = conn.execute("insert into employees values(null,'{0}','{1}','{2}','{3}', \
        #                     '{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}', \
        #                     '{13}')".format(LastName,FirstName,Title,
        #                     ReportsTo, BirthDate, HireDate, Address,
        #                     City, State, Country, PostalCode, Phone, Fax,
        #                     Email))
        return {'status':'success'}

    
#api.add_resource(LSAA, '/lsa_put')


if __name__ == '__main__':
#     LOG.basicConfig(format='%(levelname)s:%(message)s', level=LOG.DEBUG)
#     app.run(host='0.0.0.0',port='5002')
	app = Flask(__name__)
	api = Api(app)
	api.add_resource(LSAA, '/lsa_put')
  	LOG.basicConfig(format='%(levelname)s:%(message)s', level=LOG.INFO)
	lsaa = LSAA()
     	app.run(host='0.0.0.0',port='5002')

