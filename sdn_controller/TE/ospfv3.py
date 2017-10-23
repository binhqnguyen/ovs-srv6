#!/usr/bin/python2.7

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
