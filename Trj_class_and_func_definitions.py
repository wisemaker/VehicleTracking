import numpy as np
import pdb
from scipy.interpolate import interp1d

class TrjObj():
    def __init__(self,vcxtrj,vcytrj,vctime,subSampRate):
        self.Trj_with_ID     = [] # [ID,x,y]
        self.Trj_with_ID_frm = [] # [ID,frm,x,y]
        self.xTrj   = vcxtrj  #x
        self.yTrj   = vcytrj  #y
        self.frame  = vctime #current frm number
        self.vel    = [] 
        self.pos    = [] 
        self.status = 1   # 1: alive  2: dead
        self.globalID = sorted(vctime.keys())
        self.Xdir     = {} # Xdirections 0 or 1
        self.Ydir     = {} # Ydirections 0 or 1
        self.bad_IDs1 = [] # too short
        self.bad_IDs2 = [] # bad IDs with different length time and x,y
        self.bad_IDs3 = [] # inconsistent Y directions
        self.bad_IDs4 = [] # X direction 

        fps = 5
        """initialize with mintime and maxtime"""
        # for key, val in vctime.iteritems():
        #     if (len(val)==0) or (val[1]-val[0]+1 < fps*1):
        #         self.bad_IDs1.append(key)

        """initialize with time range"""
        for key, val in vctime.iteritems():
            if len(val) < fps*1:
                self.bad_IDs1.append(key)


        for key, value in vcxtrj.iteritems():
            x_location = vcxtrj[key]
            y_location = vcytrj[key]
            """initialize with mintime and maxtime"""
            # if len(vctime[key])==2:
            #     curfrm = range(vctime[key][0],vctime[key][1]+subSampRate,subSampRate)
            #     if np.size(curfrm)!= np.size(value):
            #         print "error!==============================="
            #         print('vctime size : {0}, vcxtrj size : {1}').format(np.size(curfrm),np.size(value))
            #         pdb.set_trace()
            #         self.bad_IDs2.append(key)
            #     else:
            #         for ii in range(np.size(value)):                   
            #             self.Trj_with_ID.append([key,x_location[ii],y_location[ii]])
            #             self.Trj_with_ID_frm.append([key,curfrm[ii],x_location[ii],y_location[ii]])
            """initialize with time range"""
            if len(vctime[key])!= len(x_location):
                print "error!==============================="
                print('vctime size : {0}, vcxtrj size : {1}').format(len(vctime[key]),len(x_location))
                pdb.set_trace()
                self.bad_IDs2.append(key)
            else:
                for ii in range(np.size(value)):                   
                    self.Trj_with_ID.append([key,x_location[ii],y_location[ii]])
                    self.Trj_with_ID_frm.append([key,vctime[key][ii],x_location[ii],y_location[ii]])





        for key in vctime.iterkeys():
            # if abs(((np.asarray(self.yTrj[key][1:])-np.asarray(self.yTrj[key][:-1]))>=-1).sum() - (np.size(self.yTrj[key])-1))<=5:
            if ((np.asarray(self.yTrj[key][1:])-np.asarray(self.yTrj[key][:-1]))>=0).sum()/float((np.size(self.yTrj[key])-1))>=0.70:
                self.Ydir[key] = 1
            # elif abs(((np.asarray(self.yTrj[key][1:])-np.asarray(self.yTrj[key][:-1]))<=1).sum() - (np.size(self.yTrj[key])-1))<=5:
            elif ((np.asarray(self.yTrj[key][1:])-np.asarray(self.yTrj[key][:-1]))<=0).sum()/float((np.size(self.yTrj[key])-1))>=0.70:  #more than 70% 
                self.Ydir[key] = 0
            
            else: 
                self.Ydir[key] = 999
                self.bad_IDs3.append(key)

            # if abs( ((np.asarray(self.xTrj[key][1:])-np.asarray(self.xTrj[key][:-1])) >=-1).sum()-(np.size(self.xTrj[key])-1))<=5:
            if ((np.asarray(self.xTrj[key][1:])-np.asarray(self.xTrj[key][:-1]))>=0).sum()/float((np.size(self.xTrj[key])-1))>=0.70:
            	self.Xdir[key] = 1
            elif ((np.asarray(self.xTrj[key][1:])-np.asarray(self.xTrj[key][:-1]))<=0).sum()/float((np.size(self.xTrj[key])-1))>=0.70:  #more than 70% 
            	self.Xdir[key] = 0	 
            else: 
                self.Xdir[key] = 999
                self.bad_IDs4.append(key)

        # can also set threshold on the trj, e.g. delta_y <=0.8  
        self.bad_IDs = self.bad_IDs1 + self.bad_IDs2 +self.bad_IDs3 +self.bad_IDs4



# =========================extract a vehicle object from the trajectory object
class VehicleObj():
    def __init__(self, TrjObj,ID):
        self.VehicleID = ID
        self.xTrj      = TrjObj.xTrj[ID] # x
        self.yTrj      = TrjObj.yTrj[ID] # y
        self.frame     = TrjObj.frame[ID]   #current frm number
        self.vel       = [] 
        self.pos       = [] 
        self.status    = 1   # 1: alive  2: dead
        self.Xdir      = TrjObj.Xdir[ID]
        self.Ydir      = TrjObj.Ydir[ID]

        fullFrameLen = self.frame[-1]-self.frame[0]+1
        if fullFrameLen>len(self.frame):
            """interpolate gt vector to full time resolution"""
            # interpolationMethod = 'cubic'
            interpolationMethod = 'linear'
            fx = interp1d(self.frame,self.xTrj, kind=interpolationMethod)
            fy = interp1d(self.frame,self.yTrj, kind=interpolationMethod)
            self.fullxTrj  = fx(range(self.frame[0],self.frame[-1]+1,1))
            self.fullyTrj  = fy(range(self.frame[0],self.frame[-1]+1,1))
            self.fullframe = range(self.frame[0],self.frame[-1]+1,1)

        else:
            self.fullxTrj = self.xTrj
            self.fullyTrj = self.yTrj
            self.fullframe = self.frame























