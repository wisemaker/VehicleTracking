# after raw klt 
# filtering
import os
import math
import pdb,glob
import numpy as np
from scipy.io import loadmat,savemat
from scipy.sparse import csr_matrix
import matplotlib.pyplot as plt
from DataPathclass import *
DataPathobj = DataPath(VideoIndex)
from parameterClass import *
Parameterobj = parameter(dataSource,VideoIndex)


def trj_filter(x, y, t, xspeed, yspeed, blob_index, mask, Numsample , fps, minspdth = 15): # DoT fps 23 Johnson 30

    transth  = 100*fps   #transition time (red light time) 100 seconds
    mask_re       = []
    x_re          = []
    y_re          = []
    t_re          = []
    xspd          = []
    yspd          = []

    speed = np.abs(xspeed)+np.abs(yspeed)
    print "minimum speed threshold set to be: ",minspdth
    # lenfile = open('length.txt', 'wb')
    # spdfile = open('./tempFigs/maxspeed.txt', 'wb')
    # stoptimefile = open('stoptime.txt', 'wb')
    for i in range(Numsample):
        if sum(x[i,:]!=0)>4:  # new jay st  # chk if trj is long enough
        # if sum(x[i,:]!=0)>50:  # canal
            # spdfile.write(str(i)+' '+str(max(speed[i,:][x[i,1:]!=0][1:-1]))+'\n')
            # lenfile.write(str(i)+' '+str(sum(x[i,:]!=0))+'\n')
            # pdb.set_trace()
            try:
                # spdfile.write(str(i)+' '+str(max(speed[i,:][x[i,1:]!=0][1:-1]))+'\n')
                # print "speed:", max(speed[i,:][x[i,1:]!=0][1:-1])
                if max(speed[i,:][x[i,1:]!=0][1:-1])>minspdth: # check if it is a moving point
                    if sum(speed[i,:][x[i,1:]!=0][1:-1] < 3) < transth:  # check if it is a stationary point
                        mask_re.append(mask[i]) # ID 
                        x_re.append(x[i,:])
                        y_re.append(y[i,:])
                        t_re.append(t[i,:]) 
                        xspd.append(xspeed[i,:])
                        yspd.append(yspeed[i,:])
            except:
                pass
    # spdfile.close()
    # stoptimefile.close()
    x_re = np.array(x_re)
    y_re = np.array(y_re)
    t_re = np.array(t_re)
    xspd = np.array(xspd)
    yspd = np.array(yspd)
    return mask_re, x_re, y_re, t_re, xspd, yspd

def FindAllNanRow(aa):
    index = range(aa.shape[0])
    allNanRowInd = np.array(index)[np.isnan(aa).all(axis = 1)]
    return allNanRowInd

def prepare_input_data():
    ## fps for DoT Canal is 23
    ## Jay & Johnson is 30
    # subSampRate = 6 # since 30 fps may be too large, subsample the images back to 5 FPS
    matfilepath = DataPathobj.kltpath
    savePath = DataPathobj.filteredKltPath
    useBlobCenter = False
    fps = Parameterobj.fps
    matfiles       = sorted(glob.glob(ParameterObj.kltpath + 'klt_*.mat'))
    start_position = 0 #already processed 10 files
    matfiles       = matfiles[start_position:]
    return matfiles,savePath,useBlobCenter,fps



if __name__ == '__main__':
# def filtering_main_function(fps,dataSource = 'DoT'):
    matfiles,savePath,useBlobCenter,fps = prepare_input_data()
    for matidx,matfile in enumerate(matfiles):
        print "Processing truncation...", str(matidx+1)
        ptstrj = loadmat(matfile)
        # mask = ptstrj['mask'][0] 
        mask = ptstrj['trjID'][0]
        x    = csr_matrix(ptstrj['xtracks'], shape=ptstrj['xtracks'].shape).toarray()
        y    = csr_matrix(ptstrj['ytracks'], shape=ptstrj['ytracks'].shape).toarray()
        t    = csr_matrix(ptstrj['Ttracks'], shape=ptstrj['Ttracks'].shape).toarray()

        if len(t)>0: 
            t[t==np.max(t)]=np.nan
        
        Numsample = ptstrj['xtracks'].shape[0]
        trunclen  = ptstrj['xtracks'].shape[1]
        color     = np.array([np.random.randint(0,255) for _ in range(3*int(Numsample))]).reshape(Numsample,3)

        startPt = np.zeros((Numsample,1))
        endPt   = np.zeros((Numsample,1))

        for tt in range(Numsample):
            if len(t)>0:
                startPt[tt] =  np.mod( np.nanmin(t[tt,:]), trunclen) #ignore all nans
                endPt[tt]   =  np.mod( np.nanmax(t[tt,:]), trunclen) 
            else:
                startPt[tt] =  np.min(np.where(x[tt,:]!=0))
                endPt[tt]   =  np.max(np.where(x[tt,:]!=0))


        # xspeed = np.diff(x)*((x!=0)[:,1:])  # wrong!
        # yspeed = np.diff(y)*((y!=0)[:,1:])
        
        xspeed = np.diff(x) 
        yspeed = np.diff(y)

        for ii in range(Numsample):
            if math.isnan(startPt[ii]) or math.isnan(endPt[ii]):
                xspeed[ii, :] = 0 # discard
                yspeed[ii, :] = 0 
            else:
                xspeed[ii, int(max(startPt[ii]-1,0))]      = 0 
                xspeed[ii, int(min(endPt[ii],trunclen-2))] = 0 
                yspeed[ii, int(max(startPt[ii]-1,0))]      = 0 
                yspeed[ii, int(min(endPt[ii],trunclen-2))] = 0 
        
        
        
        print "Num of original samples is " , Numsample
        minspdth = 10
        mask_re, x_re, y_re, t_re, xspd,yspd = trj_filter(x, y, t, xspeed, yspeed, blob_index, mask, Numsample , fps = fps, minspdth = minspdth)
        # delete all nan rows 
        if x_re!=[]:
            allnanInd = FindAllNanRow(t_re)
            if allnanInd != []:
                print "delete all nan rows!!"
                print allnanInd
                del mask_re[allnanInd]
                del x_re[allnanInd]
                del y_re[allnanInd]
                del t_re[allnanInd]
                del blob_index_re[allnanInd]
                del xspd[allnanInd]
                del yspd[allnanInd]
        else:
            pass 
        NumGoodsample = len(x_re)
        print "Num of Good samples is" , NumGoodsample
        # result            = {}
        # result['trjID']   = mask_re
        # result['xtracks'] = x_re       
        # result['ytracks'] = y_re
        # result['Ttracks'] = t_re
        # result['xspd']    = xspd
        # result['yspd']    = yspd

        ptstrj['trjID']   = mask_re
        ptstrj['xtracks'] = x_re       
        ptstrj['ytracks'] = y_re
        ptstrj['Ttracks'] = t_re
        ptstrj['xspd']    = xspd
        ptstrj['yspd']    = yspd

        if smooth:
            savename = os.path.join(savePath,'smooth_len4minSpd'+str(minspdth)+'_'+str(matidx+1).zfill(3)+'.mat')
        else:
            savename = os.path.join(savePath,'len4minSpd'+str(minspdth)+'_'+str(matidx+1).zfill(3))
        # savemat(savename,result)
        savemat(savename,ptstrj)



