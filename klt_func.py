import os
import cv2
import pdb
import math
import pickle
import numpy as np
import glob as glob
from time import clock
from scipy.io import loadmat,savemat
from scipy.sparse import csr_matrix
from matplotlib import pyplot as plt

from DataPathclass import *
DataPathobj = DataPath(dataSource,VideoIndex)
from parameterClass import *
Parameterobj = parameter(dataSource,VideoIndex)


def readBuffer(startOffset, cap):
    for ii in range(startOffset):
        ret, frame = cap.read()
    return cap


"""thre's bug in cap.set, try loopy reading instead"""
def readVideo(cap,subSampRate):
    """when read video in a loop, every subSampRate frames"""
    status, frame = cap.read()  
    for ii in range(subSampRate-1):
        status_1, frameskip = cap.read()
    return status,frame


if __name__ == '__main__':
    frame_idx_bias = 0
    start_position = frame_idx_bias
    isVideo  = True
    if isVideo:
        dataPath = DataPathobj.video
    else:
        dataPath = DataPathobj.imagePath
    savePath = DataPathobj.kltpath
    useBlobCenter = Parameterobj.useSBS
    isVisualize   = False

    # -- utilities
    if isVisualize: 
        plt.figure(num=None)
    lk_params = Parameterobj.lk_params
    feature_params = Parameterobj.feature_params


    # previousLastFiles = sorted(glob.glob(savePath+'*klt_*'))
    previousLastFiles = sorted(glob.glob(savePath+'*.mat'))

    if len(previousLastFiles)>0:
        if len(previousLastFiles) >1:
            previousLastFile = previousLastFiles[-1]
        else: previousLastFile = previousLastFiles[0]
        
        lastTrj   = loadmat(previousLastFile)
        lastID    = np.max(lastTrj['trjID'][0])

        dicidx      = lastID+1 #counting from the last biggest global ID
        lastT       = lastTrj['Ttracks']
        lastT[lastT==np.max(lastT)] = np.nan
        tracksdic   = {}
        start       = {}
        end         = {}
        if len(lastTrj['lastPtsKey'])>0:
            for kk in range((lastTrj['lastPtsKey'][0]).shape[0]):
                key        = lastTrj['lastPtsKey'][0][kk]
                start[key] = np.nanmin(lastT[kk,:])
                if math.isnan(start[key]): 
                    print "key:",key, "kk:",kk
                    start.pop(key)
                    continue
                end[key]       = -1 #all alive trj
                tracksdic[key] = []
                tracksdic[key].append(tuple(lastTrj['lastPtsValue'][kk,:]))
    else:
        dicidx    = 0 # start from 0
        tracksdic = {} 
        start     = {}
        end       = {}

    
    if isVideo:
        video_src = dataPath
        cap       = cv2.VideoCapture(video_src)
        # if not cap.isOpened():
        #    raise Exception("video not opened!")

        # nframe = np.int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)) # nframe is calculated from the 'wrong' fps
        # fps    = int(np.round(cap.get(cv2.cv.CV_CAP_PROP_FPS))) 
        """hard code!!!!!!"""
        fps = 30 
        print 'fps',fps

        print 'reading buffer...'
        # cap.set( cv2.cv.CV_CAP_PROP_POS_FRAMES , max(0,start_position))
        cap = readBuffer(start_position, cap)
        status, frame = cap.read()
        nrows,ncols = frame.shape[:2]
        frameL        = np.zeros_like(frame[:,:,0]) #just initilize, will be set in the while loop
        if len(previousLastFiles)>0:
            frameLp = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  #set the previous to be the last frame in last truncation
        else:    
            frameLp = np.zeros_like(frameL)

    if not isVideo:  # -- get the full image list
        imagepath = dataPath
        imlist    = sorted(glob.glob(imagepath + '*.jpg'))
        nframe    = len(imlist)
        # -- read in first frame and set dimensions
        frame     = cv2.imread(imlist[max(0,start_position)])
        frameL    = np.zeros_like(frame[:,:,0]) #just initilize, will be set in the while loop
        if len(previousLastFiles)>0:
            frameLp = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  #set the previous to be the last frame in last truncation
        else:    
            frameLp = np.zeros_like(frameL)


    trunclen = Parameterobj.trunclen
    subSampRate = fps/Parameterobj.targetFPS
    """hard code!!!!!"""
    # subSampRate = 1


    # subSampRate = 1 # for people counter
    if len(previousLastFiles)>0:
        frame_idx = len(previousLastFiles)*trunclen*subSampRate
    else:
        frame_idx = (0 + frame_idx_bias)

    detect_interval = Parameterobj.klt_detect_interval
    if detect_interval < subSampRate:
        detect_interval = 1
    else:
        detect_interval = np.floor(detect_interval/subSampRate)


    subsample_frmIdx = np.int(np.floor(frame_idx/subSampRate))
    

    if useBlobCenter:
        blob_ind_sparse_matrices = sorted(glob.glob(DataPathobj.blobPath + 'blobLabel*.p'))
        blob_center_sparse_lists = sorted(glob.glob(DataPathobj.blobPath + 'blobCenter*.p'))

    # -- set mask, all ones = no mask
    if Parameterobj.useMask:
        # # if not Parameterobj.mask is None:
        # #     pass
        # # else:
        # plt.imshow(frame[:,:,::-1])
        # pdb.set_trace()
        # mask = np.zeros(frameL.shape, dtype=np.uint8)
        # # roi_corners = np.array([[(191,0),(343,626),(344,0),(190,629)]], dtype=np.int32)
        # # roi_corners = np.array([[(0,191), (629,190), (0,344),(626,343)]], dtype=np.int32)
        # # roi_corners = np.array([[(0,191), (629,190), (0,344)]])
        # roi_corners = np.array([[(191,0),(190,629),(344,0),(343,626)]]).reshape(-1, 2)
        # # ignore_mask_color = (255,)*frame.shape[2]
        # cv2.fillPoly(mask, roi_corners, (255,255))

        # # apply the mask
        # masked_image = cv2.bitwise_and(frameL, mask)
        # # save the result
        # cv2.imwrite(Parameterobj.dataSource+'_mask.jpg', mask)
        masktouse = 255*np.ones_like(frameL)
        mask1 = cv2.imread(glob.glob(DataPathobj.DataPath+'/*Mask.jpg')[0])
        masktouse[mask1[:,:,0]==0]=0

    else:
        masktouse = 255*np.ones_like(frameL)

    ## set is buggy
    # cap.set( cv2.cv.CV_CAP_PROP_POS_FRAMES , max(0,subsample_frmIdx*subSampRate))
    cap = readBuffer(max(0,subsample_frmIdx*subSampRate)-start_position, cap)    
    # while (frame_idx < nframe):
    while status:
        if useBlobCenter and ((subsample_frmIdx % trunclen) == 0):
            print "load foreground blob index matrix file....",subsample_frmIdx/trunclen
            blobIndLists       = []
            blobIndListfile    = blob_ind_sparse_matrices[subsample_frmIdx/trunclen]
            blobIndLists       = pickle.load( open( blobIndListfile, "rb" ) )
            
            blobCenterLists    = []
            blobCenterListfile = blob_center_sparse_lists[subsample_frmIdx/trunclen]
            blobCenterLists    = pickle.load( open( blobCenterListfile, "rb" ) )

        if not isVideo:
            frame[:,:,:] = cv2.imread(imlist[subsample_frmIdx*subSampRate])
        if isVideo:
            try:
                """set has bug"""
                # cap.set( cv2.cv.CV_CAP_PROP_POS_FRAMES , max(0,subsample_frmIdx*subSampRate))
                # status, frame[:,:,:] = cap.read()
                status,frame[:,:,:] = readVideo(cap,subSampRate)
            except:
                print "exception!!"
                print "directly save"    
                continue
        if useBlobCenter:
            BlobIndMatrixCurFrm = (blobIndLists[np.mod(subsample_frmIdx,min(len(blobIndLists),trunclen))]).todense()
            BlobCenterCurFrm    = blobCenterLists[np.mod(subsample_frmIdx,min(len(blobIndLists),trunclen))]
            if len(BlobCenterCurFrm)<1: #is empty
                BlobCenterCurFrm=[(0,0)]

        frameL[:,:] = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        frame_hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # cv2.imshow('hue',frame_hsv[:,:,0])
        # cv2.waitKey(0)

        ## histogram equalization, more contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        frameL_he = clahe.apply(frameL)
        frameL = frameL_he

        # for visulization
        vis = frame.copy()

        """Tracking"""
        if len(tracksdic) > 0:
            try:
                pnts_old = np.float32([tracksdic[i][-1][:2] for i in sorted(tracksdic.keys())]).reshape(-1, 1, 2)
            except: 
                pnts_old = np.float32([tracksdic[i][:2] for i in sorted(tracksdic.keys())]).reshape(-1, 1, 2)

            pnts_new, st, err  = cv2.calcOpticalFlowPyrLK(frameLp, frameL, 
                                                          pnts_old, None, 
                                                          **lk_params)
            pnts_oldr, st, err = cv2.calcOpticalFlowPyrLK(frameL, frameLp, 
                                                          pnts_new, None, 
                                                          **lk_params)
            dist = abs(pnts_old-pnts_oldr).reshape(-1, 2).max(-1)
            good = dist < 1

     
            for (x, y), good_flag, idx in zip(pnts_new.reshape(-1, 2), good, sorted(tracksdic.keys())):
                if not good_flag:
                    if end[idx]==-1:
                        end[idx] = (frame_idx-1)
                        if useBlobCenter:
                            # tracksdic[idx].append((-100,-100,frame_idx,np.nan,0,np.nan,np.nan))
                            tracksdic[idx].append((np.nan,np.nan,frame_idx,np.nan,0,np.nan,np.nan))
                        else:
                            tracksdic[idx].append((np.nan,np.nan,frame_idx,np.nan))
                    else:
                        pass ## already dead, already has end[idx]
                else:
                    if (not np.isnan(x)) and (not np.isnan(y)): 
                        if end[idx]>0:
                            pdb.set_trace()
                        x = min(x,frameLp.shape[1]-1)  ## why?? klt will find points outside the bdry???
                        y = min(y,frameLp.shape[0]-1)
                        x = max(x,0)  ## why?? klt will find points outside the bdry???
                        y = max(y,0)

                        # if x>frameLp.shape[1] or y>frameLp.shape[0]:
                        #     print x, y
                        # hue = frame_hsv[y,x,0]
                        """use a median of the 3*3 window"""
                        hue = np.nanmedian(frame_hsv[max(0,y-1):min(y+2,nrows),max(0,x-1):min(x+2,ncols),0])
                        if np.isnan(hue):
                            hue = frame_hsv[y,x,0]
                        """try median of the intensity"""
                        # hue = np.median(frameL[max(0,y-1):min(y+2,nrows),max(0,x-1):min(x+2,ncols)])

                        if useBlobCenter:
                            blobInd    = BlobIndMatrixCurFrm[y,x]
                            if blobInd!=0:
                                blobCenter = BlobCenterCurFrm[blobInd-1]
                                tracksdic[idx].append((x,y,frame_idx,hue,np.int8(blobInd),blobCenter[1],blobCenter[0]))
                            else:
                                # tracksdic[idx].append((x,y,frame_idx,hue,0,np.NaN,np.NaN))
                                tracksdic[idx].append((x,y,frame_idx,hue,0,x,y))

                        else:
                            tracksdic[idx].append((x,y,frame_idx,hue))
                        
                        """mask out this point, avoid duplicating"""
                        cv2.circle(vis, (x, y), 3, (0, 0, 255), -1)

                        if isVisualize:    
                            # cv2.line(vis, (int(tracksdic[idx][-2][0]),int(tracksdic[idx][-2][1])), (int(tracksdic[idx][-1][0]),int(tracksdic[idx][-1][1])), (0, 255, 0), 2)
                            # cv2.line(vis, (int(tracksdic[idx][-2][0]),int(tracksdic[idx][-2][1])), (x,y), (0, 255, 0), 1)
                            for vvv in range(len(tracksdic[idx])-1,1,-1):
                                cv2.line(vis, (int(tracksdic[idx][vvv][0]),int(tracksdic[idx][vvv][1])), (int(tracksdic[idx][vvv-1][0]),int(tracksdic[idx][vvv-1][1])), (0, 255, 0), 1)
                    else:
                        """stop appending nans after this point is already lost."""
                        pass




        """Detecting new points"""
        if subsample_frmIdx % detect_interval == 0: 

            # GGD: this is (I *think*) eliminating redundant non-moving points
            # mask = masktouse
            masktouse[:,:] = 255
            mask = masktouse

            for x, y in [tracksdic[tr][-1][:2] for tr in tracksdic.keys()]:
                if not np.isnan(x):
                    cv2.circle(mask, (np.int32(x), np.int32(y)), 5, 0, -1)    

            corners = cv2.goodFeaturesToTrack(frameL,mask=mask,**feature_params)

            if corners is not None:
                for x, y in np.float32(corners).reshape(-1, 2):
                    # create new dic item using new dicidx since these are new points:
                    tracksdic[dicidx] = [] 
                    start[dicidx]     = frame_idx
                    end[dicidx]       = -1
                    hue = np.median(frame_hsv[max(0,y-1):min(y+2,nrows),max(0,x-1):min(x+2,ncols),0])
                    if np.isnan(hue):
                        hue = frame_hsv[y,x,0]

                    if useBlobCenter:
                        blobInd = BlobIndMatrixCurFrm[y,x]                    
                        if blobInd!=0:
                            blobCenter = BlobCenterCurFrm[blobInd-1]
                            tracksdic[dicidx].append((x,y,frame_idx,hue,np.int8(blobInd),blobCenter[1],blobCenter[0]))
                        else:
                            # tracksdic[dicidx].append((x,y,frame_idx,hue,0,np.NaN,np.NaN))
                            tracksdic[dicidx].append((x,y,frame_idx,hue,0,x,y))
                    else:
                        tracksdic[dicidx].append((x,y,frame_idx,hue))
                    dicidx += 1

        print('{0} - {1}'.format(subsample_frmIdx*subSampRate,len(tracksdic)))

        if isVisualize:
            # cv2.imshow('klt', vis)
            # cv2.waitKey(5)    
            plt.imshow(vis[:,:,::-1])
            plt.pause(0.00001)
    
        # switch previous frame
        frameLp[:,:] = frameL[:,:]
        subsample_frmIdx   += 1
        frame_idx = subsample_frmIdx*subSampRate

        # dump trajectories to file
        # trunclen = min(trunclen,frame_idx - frame_idx/trunclen*600) #the very last truncation length may be less than original trunclen 
        # if  ((frame_idx>0) & (subsample_frmIdx % trunclen == 0)) or (frame_idx==nframe):
        if  ((frame_idx>0) & (subsample_frmIdx % trunclen == 0)) or (not status):
            print "saving===!!!"   
            # print('{0} - {1}'.format(frame_idx,len(tracksdic)))         
            Xtracks = np.zeros([len(tracksdic),trunclen])
            Ytracks = np.zeros([len(tracksdic),trunclen])
            Huetracks = np.zeros([len(tracksdic),trunclen])
            # initialize T track using numbers that will never appear in reality
            # "won't-appear" fillers": frame_idx+3*trunclen
            # this way, we won't lose the REAL 0's, i.e. starts from 0 frame, when filtering in the trj_filter.py
            Ttracks = np.ones([len(tracksdic),trunclen])*(frame_idx+3*trunclen)
            if useBlobCenter:
                BlobIndtracks = np.zeros([len(tracksdic),trunclen]) #blob index starts from 1
                BlobCenterX   = np.zeros([len(tracksdic),trunclen]) 
                BlobCenterY   = np.zeros([len(tracksdic),trunclen]) 
            # set first frame in this chunk
            
            if subsample_frmIdx%trunclen==0:
                offset  = subsample_frmIdx - trunclen
            else:  ## the last truncation is less than trunclen frames
                offset  = subsample_frmIdx - subsample_frmIdx%trunclen

            # loop through the current trajectories list
            for ii, trjidx in enumerate(tracksdic.keys()):

                # set the starting and ending frame index
                st_ind = start[trjidx]
                en_ind = end[trjidx]

                # if en_ind is -1, then the traj is still alive,
                # otherwise, the trajectory is dead (but still in the
                # tracks dictionary, otherwise it would have been
                # removed).
                if en_ind==-1: #not yet finished, save whole row
                    ttrack = np.array(tracksdic[trjidx]).T
                else: #already ended within this truncation
                    ttrack = np.array(tracksdic[trjidx][:-1]).T # don't save nans 

                # if st_ind is -1, then the track existed in the previous
                # truncation and all points except the last one of the
                # previous truncation were removed, so only save from the
                # second point.
                # if st_ind=='fromPre':
                if st_ind/subSampRate<offset:
                    # print "trj point is from previous truncation!"
                    st_ind = offset*subSampRate
                    ttrack = ttrack[:,1:] #because the first point is the last point from pre trunc, already saved

                # put trajectory into matrix
                tstart, tstop = (st_ind-start_position)/subSampRate-offset, (en_ind-start_position)/subSampRate-offset+1

                if en_ind==-1:
                    Xtracks[ii,:][tstart:tstart+len(ttrack[0,:])]   = ttrack[0,:]
                    Ytracks[ii,:][tstart:tstart+len(ttrack[1,:])]   = ttrack[1,:]
                    Ttracks[ii,:][tstart:tstart+len(ttrack[2,:])]   = ttrack[2,:]
                    Huetracks[ii,:][tstart:tstart+len(ttrack[3,:])] = ttrack[3,:]
                    if useBlobCenter:
                        BlobIndtracks[ii,:][tstart:] = ttrack[4,:]
                        BlobCenterX[ii,:][tstart:]   = ttrack[5,:]
                        BlobCenterY[ii,:][tstart:]   = ttrack[6,:] 

                else:
                    Xtracks[ii,:][tstart:tstop]   = ttrack[0,:]
                    Ytracks[ii,:][tstart:tstop]   = ttrack[1,:]
                    Ttracks[ii,:][tstart:tstop]   = ttrack[2,:]
                    Huetracks[ii,:][tstart:tstop] = ttrack[3,:]
                    if useBlobCenter:
                        BlobIndtracks[ii,:][tstart:tstop] = ttrack[4,:]
                        BlobCenterX[ii,:][tstart:tstop]   = ttrack[5,:]
                        BlobCenterY[ii,:][tstart:tstop]   = ttrack[6,:]

            # put tracks into sparse matrix
            trk ={}
            # Ttracks = Ttracks+frame_idx_bias # use the actual frame index as the key, to save data
            trk['xtracks']   = csr_matrix(Xtracks)
            trk['ytracks']   = csr_matrix(Ytracks)
            trk['Ttracks']   = Ttracks
            trk['Huetracks'] = csr_matrix(Huetracks)
            trk['trjID'] = tracksdic.keys()
            if useBlobCenter:
                trk['fg_blob_index']    = csr_matrix(BlobIndtracks)
                trk['fg_blob_center_X'] = csr_matrix(BlobCenterX)
                trk['fg_blob_center_Y'] = csr_matrix(BlobCenterY)
            # for dead tracks, remove them.  for alive tracks, remove all
            # points except the last one (in order to track into the next
            # frame).
            deadtrj   = np.array(end.keys())[np.array(end.values())>=0]# ==0 is for the case when the tracks ends at 0 frame
            for i in sorted(tracksdic.keys()):   
                if i in deadtrj:
                    tracksdic.pop(i)
                else:
                    tracksdic[i] = [tracksdic[i][-1]]#save the last one

            if len(tracksdic)>0:
                trk['lastPtsValue'] = np.array(tracksdic.values())[:,0,:]
                trk['lastPtsKey']   = np.array(tracksdic.keys())
            else: ##all points are dead in this trunk
                trk['lastPtsValue'] = np.array([])
                trk['lastPtsKey']   = np.array([])

            # savename = os.path.join(savePath,'simp_blob_klt_'+str(np.int(np.ceil(subsample_frmIdx/float(trunclen)))).zfill(3))
            savename = os.path.join(savePath,str(np.int(np.ceil(subsample_frmIdx/float(trunclen)))).zfill(3))
            savemat(savename,trk)













