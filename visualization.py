from scipy.io import loadmat,savemat
import cv2,pdb
import glob as glob
from scipy.sparse import csr_matrix
import csv
import cPickle as pickle
import pprint
import numpy as np
import matplotlib.pyplot as plt

def Virctr(x,y):
    '''
    calculate virtual center, and remove out lier
    '''    
    if len(x)<3:
        vcx = np.mean(x)
        vcy = np.mean(y)
    else:
        mx = np.mean(x)
        my = np.mean(y)
        sx = np.std(x)
        sy = np.std(y)
        idx = ((x-mx)<2*sx)&((y-my)<2*sy)
        vcx = np.mean(x[idx])
        vcy = np.mean(y[idx])
    return vcx,vcy




if __name__ == '__main__':

    # video_src = '/home/andyc/Videos/video0222.mp4'
    # video_src = '../VideoData/video0222.mp4'

    trunclen = 600

    # inifilename = 'HR'
    # lrsl = './mat/20150222_Mat/finalresult/'+inifilename
    # matfiles = sorted(glob('./mat/20150222_Mat/'+inifilename+'*.mat'))[0:55]
    # lrsl = '../DoT/5Ave@42St-96.81/finalresult/5Ave@42St-96.81_2015-06-16_16h04min40s686ms/result' 
    # matfiles = sorted(glob('../DoT/5Ave@42St-96.81/mat/5Ave@42St-96.81_2015-06-16_16h04min40s686ms/'+'*.mat'))

    lrsl = '../DoT/CanalSt@BaxterSt-96.106/finalresult/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/priorssc5030' 
    # lrsl = './tempFigs/roi2/ssc_with_Adj_CC_result' 

    """ use original klt x and y"""
    # matfiles = sorted(glob('../DoT/CanalSt@BaxterSt-96.106/mat/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/'+'*.mat'))
    """ use x_re and y_re from trj_cluster adj"""
    matfiles = sorted(glob.glob('../DoT/CanalSt@BaxterSt-96.106/adj/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/len50' +'*.mat'))
    # matfiles = sorted(glob('./tempFigs/roi2/len4' +'*.mat'))


    # mask is the trajectory index
    # for final result mat1, there are 1645 trjs
    mask = loadmat(lrsl)['mask'][0] # labeled trjs' indexes
    labels = loadmat(lrsl)['label'][0]

    # times = pickle.load( open( "./mat/20150222_Mat/finalresult/HRTtracks.p", "rb" ) )


    trunkTrjFile = loadmat(matfiles[-1]) ##the last one, to get the max index number
    # IDintrunklast = trunkTrjFile['idxtable'][0]  #last trunk (3rd mat) has 3603 trjs #use original
    IDintrunklast = trunkTrjFile['mask'][0] # 26 trjs 
    mlabels = np.ones(max(IDintrunklast)+1)*-1  #initial to be -1
 

    #build PtsInCurFrm trj labels (-1 : not interest PtsInCurFrm)
    for idx,ID in enumerate(mask):  # i=mask[idx], the content
        mlabels[int(ID)] = labels[int(idx)]
    # mlabels(trjID) = label for this trj

    vcxtrj = {} ##dictionary
    vcytrj = {}

    vctime = {}
    vctime2 = {}

    for i in np.unique(mlabels):  ## there are several PtsInCurFrm contributing to one label i
        vcxtrj[i]=[] # find a virtual center for each label i
        vcytrj[i]=[]
        vctime[i]=[]

        vctime2[i] = [] 

    # cam = cv2.VideoCapture(video_src)
    # nrows = cam.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    # ncols = cam.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
    # framenum  = int(cam.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
    # framerate = int (cam.get(cv2.cv.CV_CAP_PROP_FPS))

    # image_listing = sorted(glob('../VideoData/20150220/*.jpg'))
    # image_listing = sorted(glob('../DoT/5Ave@42St-96.81/5Ave@42St-96.81_2015-06-16_16h04min40s686ms/*.jpg'))
    image_listing = sorted(glob.glob('../DoT/CanalSt@BaxterSt-96.106/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/*.jpg'))
    # image_listing = sorted(glob('./tempFigs/roi2/*.jpg'))


    firstfrm=cv2.imread(image_listing[0])
    nrows = int(np.size(firstfrm,0))
    ncols = int(np.size(firstfrm,1))
    framenum = int(len(image_listing))
    framerate = 5
    notconnectedLabel= []

    frame_idx = 0


    # fig = plt.figure(1,figsize=[10,12])
    fig = plt.figure(1)
    axL = plt.subplot(1,1,1)
    frame = np.zeros([nrows,ncols,3]).astype('uint8')
    im = plt.imshow(np.zeros([nrows,ncols,3]))
    plt.axis('off')
    # # adjust the plot limits
    # cut = 1
    # xmax= cut*ncols
    # ymax= cut*nrows
    # plt.xlim(0,xmax)
    # plt.ylim(0,ymax)
        
    color = np.array([np.random.randint(0,255) \
                   for _ in range(3*int(max(labels)))])\
                   .reshape(int(max(labels)),3)

    # cam.set(cv2.cv.CV_CAP_PROP_POS_FRAMES,frame_idx)





    framenum = 1801 # for testing
    while (frame_idx < framenum):
        # pdb.set_trace()
        print ("frame_idx" , frame_idx)
        if (frame_idx % trunclen == 0):
            print "load file!!-------------------------------------"
            print frame_idx
            
            """ use original klt x and y"""
            # trunkTrjFile = loadmat(matfiles[frame_idx//trunclen])
            # xtrj = csr_matrix(trunkTrjFile['xtracks'], shape=trunkTrjFile['xtracks'].shape).toarray()
            # ytrj = csr_matrix(trunkTrjFile['ytracks'], shape=trunkTrjFile['ytracks'].shape).toarray()
            # IDintrunk = trunkTrjFile['idxtable'][0]
            # Nsample = trunkTrjFile['xtracks'].shape[0]
            # fnum   = trunkTrjFile['xtracks'].shape[1]

            """ use x_re and y_re"""
            trunkTrjFile = loadmat(matfiles[frame_idx//trunclen])
            xtrj = csr_matrix(trunkTrjFile['x_re'], shape=trunkTrjFile['x_re'].shape).toarray()
            ytrj = csr_matrix(trunkTrjFile['y_re'], shape=trunkTrjFile['y_re'].shape).toarray()
            IDintrunk = trunkTrjFile['mask'][0]
            Nsample = trunkTrjFile['x_re'].shape[0] # num of trjs in this trunk
            fnum   = trunkTrjFile['x_re'].shape[1] # 600

            ttrj = csr_matrix(trunkTrjFile['Ttracks'], shape=trunkTrjFile['Ttracks'].shape).toarray()


            trk = np.zeros([Nsample,fnum,3])
            startT = np.ones([Nsample,1])*-999
            endT = np.ones([Nsample,1])*-999

        

            for i in range(Nsample):  # for the ith sample
                trk[i,:,0] = xtrj[i,:]
                trk[i,:,1] = ytrj[i,:]
                trk[i,:,2] = ttrj[i,:]

                ## get the time T (where the pt appears and disappears)
                havePt  = np.array(np.where(xtrj[i,:]>0))[0]
                if len(havePt)!=0:
                    startT[i] = int ( min(havePt)+(frame_idx/trunclen*trunclen) )
                    endT[i]   = int ( max(havePt)+(frame_idx/trunclen*trunclen) )
                    # only for check, can delete ttrj
                    if startT[i]!=np.min(ttrj[i,havePt]) or endT[i]!=np.max(ttrj[i,havePt]):
                        print "wrong time===========!!!, want to delete this trj?"
                        pdb.set_trace()
                        
                        
       

            # just need to compute vctime once for each trunk ============================
            labinT = list(set(mlabels[IDintrunk])) # label in this trunk
            for k in np.unique(labinT):
                if k !=-1:          
                    t1list=startT[mlabels[IDintrunk]==k]  # consider all IDs in the trunk, not only alive in curFrm
                    t2list=endT[mlabels[IDintrunk]==k]
                    

                    t1 = t1list[t1list!=-999]
                    t2 = t2list[t2list!=-999]

                    if len(t1)*len(t2)!=0:
                        startfrm=min(t1[t1!=-999]) # earliest appering time in this trj group
                        endfrm=max(t2[t2!=-999])   # latest disappering time in this trj group
                    else:
                        pdb.set_trace()
                        print "!!!!error!!!!!!there are no trjs in class", str(k)
                        startfrm=-888
                        endfrm=-888

                    if not vctime[k]:
                        vctime[k] =  [int(startfrm),int(endfrm)]
                    else:
                        lastendfrm = vctime[k][-1]
                        laststartfrm = vctime[k][-2]
                        if int(startfrm) == lastendfrm+1:
                            vctime[k] = [laststartfrm, int(endfrm)]
                        else:
                            print k
                            print "========same class trjs not overlapping, disconnected==============!"
                            notconnectedLabel.append(k)
                            vctime[k].append(int(startfrm))
                            vctime[k].append(int(endfrm))
                            pdb.set_trace() 
                        # if not vctime[k]:
                        #     vctime[k].append([int(startfrm),int(endfrm)])
                        # else: 
                        #     print "*********************************"
                        #     print vctime[k]
                        #     print [int(startfrm),int(endfrm)]
                        #     pdb.set_trace()


        # execute for each frame, for vcxtrj, vcytry, and plot
        # compute virtual center every frame

        # ret, frame[:] = cam.read()
        tmpName= image_listing[frame_idx]
        frame=cv2.imread(tmpName)


        
        # current frame index is: (frame_idx%trunclen)
        PtsInCurFrm = trk[:,:,0][:,frame_idx%trunclen]!=0 # in True or False, PtsInCurFrm appear in this frame,i.e. X!=0
        IDinCurFrm = IDintrunk[PtsInCurFrm] #select IDs in this frame

        labinf = list(set(mlabels[IDinCurFrm])) # label in current frame
        dots = []
        for k in np.unique(labinf):
            line_exist = 0 ## CG
            if k !=-1:
                x = trk[:,:,0].T[frame_idx%trunclen][((mlabels==k)[IDintrunk])&PtsInCurFrm]
                y = trk[:,:,1].T[frame_idx%trunclen][((mlabels==k)[IDintrunk])&PtsInCurFrm]
                vx,vy = Virctr(x,y) # find virtual center
                
                vcxtrj[k].append(vx) 
                vcytrj[k].append(vy)

                # t1list=startT[((mlabels==k)[IDintrunk])&PtsInCurFrm]
                # t2list=endT[((mlabels==k)[IDintrunk])&PtsInCurFrm]

                # t1list=startT[(mlabels==k)[IDintrunk]]  # consider all IDs in the trunk, not only alive in curFrm
                # t2list=endT[(mlabels==k)[IDintrunk]]
                

                # t1 = t1list[t1list!=-999]
                # t2 = t2list[t2list!=-999]

                # if len(t1)*len(t2)!=0:
                #     startfrm=min(t1[t1!=-999])
                #     endfrm=max(t2[t2!=-999])
                # else:
                #     pdb.set_trace()
                #     startfrm=-888
                #     endfrm=-888

                # if not vctime[k]:
                #     vctime[k].append([int(startfrm),int(endfrm)])
                # else: 
                #     pdb.set_trace()






                # tempxyIDs = np.where(mlabels==k)
                # xyIDs = []

                # for xxyyiidd in np.array(tempxyIDs)[0]: 
                #     if xxyyiidd in IDinCurFrm:
                #         xyIDs.append(xxyyiidd)
                # xyIDfalse = np.where((mlabels[IDintrunk]==k) & PtsInCurFrm) 

                # vctime 222222 
                # t11 = [] 
                
                # for xyid in array(xyIDs):
                #     if xyid in times.keys():                
                #         t11 = t11 + times[xyid]
                #     else:
                #         print "=============here======"
                #         print xyid
                #         print frame_idx
                #         pdb.set_trace()
                #         t11 = t11+ [-888]

                # mint11 = min(array(t11))
                # maxt11 = max(array(t11))
                # vctime2[k] = [int(mint11), int(maxt11)]



                # lines = axL.plot(vcxtrj[k],vcytrj[k],color = (0,1,0),linewidth=2)
                lines = axL.plot(vcxtrj[k],vcytrj[k],color = (color[k-1].T)/255.,linewidth=2)
                line_exist = 1

                #dots.append(axL.scatter(vx, vy, s=50, color=(color[k-1].T)/255.,edgecolor='black')) 
                # dots.append(axL.scatter(x, y, s=50, color=(color[k-1].T)/255.,edgecolor='none')) 
                # dots.append(axL.scatter(x, y, s=50, color=(1,0,0),edgecolor='none'))
        im.set_data(frame[:,:,::-1])
        
        fig.canvas.draw()
        plt.draw()
        # plt.pause(0.00001) 
        # pdb.set_trace()

        # name = './canalResult/'+str(frame_idx).zfill(6)+'.jpg'
        
        # cv2.imwrite(name, frame)
        # extent = axL.get_tightbbox(fig.canvas.renderer).transformed(fig.dpi_scale_trans.inverted())
        # plt.savefig(name,bbox_inches=extent) ##save figure
        # plt.savefig(name) ##save figure

        # pdb.set_trace()







        while line_exist :
            try:
                axL.lines.pop(0)
            except:
                line_exist = 0
        

        for i in dots:
            i.remove()

        
        plt.show()
        frame_idx = frame_idx+1
        # end of while loop



    for kkk in notconnectedLabel:
        # print vctime[kkk]
        if np.size(vcxtrj[kkk])==vctime[kkk][1]-vctime[kkk][0]+1:
            print "disconnected will satisfy this, right????"
            vctime[kkk] = [vctime[kkk][0], vctime[kkk][1]]
        pdb.set_trace()






    # for keyID, frmrange in vctime.iteritems():
    #     # pdb.set_trace()
    #     # print vctime[keyID]
    #     # print vctime2[keyID]
    #     if vctime2[keyID]:
    #         print vctime2[keyID][1]-vctime2[keyID][0] 
    #         print vctime[keyID][1]-vctime[keyID][0] 
    #         print size(vcxtrj[keyID])
    #         pdb.set_trace()
    #     else:
    #         print size(vctime2[keyID])
    #     # print vctime[keyID] == vctime2[keyID]
    #     print "=========="



    # save the tracks


    # savename = './mat/'+'vcxtrj'  ## mat not working??
    # savemat(savename,vcxtrj)

    # savename = './mat/'+'vcytrj.mat'
    # savemat(savename,vcytrj)



    '''
    writer = csv.writer(open('./mat/20150222_Mat/Fullvcxtrj.csv', 'wb'))
    for key, value in vcxtrj.items():
       writer.writerow([key, value])

    writer = csv.writer(open('./mat/20150222_Mat/Fullvcytrj.csv', 'wb'))
    for key, value in vcytrj.items():
       writer.writerow([key, value])

    writer = csv.writer(open('./mat/20150222_Mat/Fullvctime.csv', 'wb'))
    for key, value in vctime.items():
       writer.writerow([key,value])


    '''

    # ==================================================================

    # Print "Save the dictionary into a pickle file"
    pickle.dump( vctime, open( "../DoT/CanalSt@BaxterSt-96.106/mat/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/vctime.p", "wb" ) )
    pickle.dump( vcxtrj, open( "../DoT/CanalSt@BaxterSt-96.106/mat/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/vcxtrj.p", "wb" ) )
    pickle.dump( vcytrj, open( "../DoT/CanalSt@BaxterSt-96.106/mat/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/vcytrj.p", "wb" ) )
    # save the labels where bad time frame appended
    pickle.dump( notconnectedLabel, open("../DoT/CanalSt@BaxterSt-96.106/mat/CanalSt@BaxterSt-96.106_2015-06-16_16h03min52s762ms/VCTIMEnotconnectedLabel.p","wb"))


    # chunk_len = framerate*40 # 40s
    # chunk_center = range(1/2*chunk_len,3000,chunk_len)  #change 1000 to the Framenumber
    # chunk_center = chunk_center [1:]

    # # temp_vcxtrj = {}
    # # temp_vcytrj = {}
    # # temp_vctime = {}
    # # for ii in obj_pair.globalID[0:400]:  
    # #     temp_vcxtrj[ii] = test_vcxtrj[ii]
    # #     temp_vcytrj[ii] = test_vcytrj[ii]
    # #     temp_vctime[ii] = test_vctime[ii]

    # potential_key = []

    # for ii in range(size(chunk_center,0)):


    #     for key, value in temp_vctime.iteritems():
    #         if value!=[]:
    #             startF = value[0]
    #             endF = value[1]
    #             if not(startF >= chunk_center[ii]+1/2*chunk_len or endF < chunk_center[ii]-1/2*chunk_len):
    #                 potential_key.append(int(key))


    # potential_x = []
    # potential_y = []

    # set_x = []
    # set_y = []
    # set_frm = []
    # # get intersection for those IDs
    # for kk in range(len(potential_key)):
    #     potential_frm = temp_vctime[potential_key[kk]]
    #     set_frm.append(set(range(potential_frm[0],potential_frm[1],1)))


    #     potential_x = temp_vcxtrj[potential_key[kk]]
    #     set_x.append(set(potential_x))

    #     potential_y = temp_vcytrj[potential_key[kk]]
    #     set_y.append(set(potential_y))


    # parallel_vehicle_ID = []
    # parallel_vehicle_common = []
    # parallel_vehicle_x1 = []
    # parallel_vehicle_x2 = []
    # parallel_vehicle_y1 = []
    # parallel_vehicle_y2 = []



    # for ff in range (size(set_frm)-1):
    #     z = set_frm[ff]
    #     for ff2 in range(ff+1, size(set_frm)):
    #         common_frm = z.intersection(set_frm[ff2])
    #         if len(common_frm) >= 10:
    #             common_frm = list(common_frm)
    #             parallel_vehicle_ID.append([ff, ff2])
    #             parallel_vehicle_common.append(common_frm)

    #             parallel_vehicle_x1.append(vcxtrj[ff][range(common_frm[0]-vctime[ff][0],common_frm[-1]-vctime[ff][0],1)])
    #             parallel_vehicle_x2.append(vcxtrj[ff2][range(common_frm[0]-vctime[ff2][0],common_frm[-1]-vctime[ff2][0],1)])

    #             parallel_vehicle_y1.append(vcytrj[ff][range(common_frm[0]-vctime[ff][0],common_frm[-1]-vctime[ff][0],1)])
    #             parallel_vehicle_y2.append(vcytrj[ff2][range(common_frm[0]-vctime[ff2][0],common_frm[-1]-vctime[ff2][0],1)])

    #  #  still need to debug here!!







    # # 2. Filter out thoes intersect too short


    # if common_frm.size








    # # 3. save





    # # tracks2015 = pickle.load( open ("/home/chengeli/Downloads/tracks2015.pkl","rb")) 
     





    













