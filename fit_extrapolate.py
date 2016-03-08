# preprocessing padding to start and end regions
import os
import math
import pdb,glob
import numpy as np
from scipy.io import loadmat,savemat
from scipy.sparse import csr_matrix
import matplotlib.pyplot as plt
from scipy.interpolate import spline
from scipy.interpolate import interp1d
from scipy.interpolate import InterpolatedUnivariateSpline
from sklearn.cluster import KMeans
from mpl_toolkits.mplot3d import Axes3D
from sets import Set
from DataPathclass import *
DataPathobj = DataPath(VideoIndex)

def filteringCriterion(xk,yk,xspd,yspd):
	minspdth = 5
	fps = 30
	transth = 100*fps/6
	speed = np.abs(xspd)+np.abs(yspd)
	livelong      =  len(xk)>4   # chk if trj is long enough
	if not livelong:
		return False
	else:
		notStationary = sum(speed<3) < transth
		moving1       = max(speed)>minspdth # check if it is a moving point
		moving2       = (np.abs(np.sum(xspd))>=1e-2) and (np.abs(np.sum(yspd))>=1e-2)
		loc_change    = (np.max(xk)-np.min(xk)>=5) or (np.max(yk)-np.min(yk)>=5)
		
		# if (np.sum(xspd)<=1e-2 and np.sum(xaccelerate)<=1e-1) or (np.sum(yspd)<=1e-2 and np.sum(yaccelerate)<=1e-1):
		# if len(xspd)<=3 and (np.sum(xspd)<=1e-2) and (np.sum(xaccelerate)<=1e-1):
		# if ((np.abs(np.sum(xspd))<=1e-2) and (np.abs(np.sum(yspd))<=1e-2)) or ((np.max(xk)-np.min(xk)<=5) and (np.max(yk)-np.min(yk)<=5)):
		return bool(livelong*notStationary*moving1*moving2*loc_change)



def polyFitTrj(x,y,xspd_mtx,yspd_mtx):
	badTrj  = []
	goodTrj = []
	p3      = [] #polynomial coefficients, order 3
	for kk in range(x.shape[0]):
		xk = x[kk,:][x[kk,:]!=0]
		yk = y[kk,:][y[kk,:]!=0]
		
		# xaccelerate = np.diff(xspd)
		# yaccelerate = np.diff(yspd)

		xspd = xspd_mtx[kk,:][np.where(x[kk,:]!=0)[0][1:]]
		yspd = yspd_mtx[kk,:][np.where(x[kk,:]!=0)[0][1:]]

		# print sum(xspd)
		# print sum(accelerate)
		satisfyCriterion = filteringCriterion(xk,yk,xspd,yspd)
		if not satisfyCriterion:
			badTrj.append(kk)
			# plt.plot(x[kk,:][x[kk,:]!=0],y[kk,:][y[kk,:]!=0])
			# pdb.set_trace()
		else:
			goodTrj.append(kk)
			# p3.append(np.polyfit(x[kk,:][x[kk,:]!=0], y[kk,:][y[kk,:]!=0], 3))  # fit a poly line to the last K points
			#### p3.append(np.polyfit( y[kk,:][y[kk,:]!=0], x[kk,:][x[kk,:]!=0],3))
			p3.append(np.polyfit(x[kk,:][x[kk,:]!=0], y[kk,:][y[kk,:]!=0], 2))

	outlierID =[]
	p3 = np.array(p3)
	goodTrj = np.array(goodTrj)
	for ii in range(p3.shape[1]):
		data = p3[:,ii]
		outlierID = outlierID+ list(np.where(np.isnan(data)==True)[0])

		mu,std = fitGaussian(data[np.ones(len(data), dtype=bool)-np.isnan(data)])
		outlierID = outlierID + list(np.where(data>=mu+std)[0])+list(np.where(data<=mu-std)[0])
		# print p3[outlierID,:]
	outlierID = np.unique(outlierID)
	TFid = np.ones(len(goodTrj),'bool')
	TFid[outlierID] = False
	goodTrj = goodTrj[TFid]
	p3      = p3[TFid]
	return np.array(p3),np.array(goodTrj)


# extrapolate original trj
def extraPolate(xk, yk):
	# positions to inter/extrapolate
	# y_extraPosistion = np.linspace(start_Y, end_Y, 2)
	y_extraPosistion = range(start_Y, end_Y, 1)
	# spline order: 1 linear, 2 quadratic, 3 cubic ... 
	order = 1
	# do inter/extrapolation
	spline = InterpolatedUnivariateSpline(yk, xk, k=order)
	x_extraPosistion = spline(y_extraPosistion)

	# example showing the interpolation for linear, quadratic and cubic interpolation
	# plt.figure()
	plt.plot(x_extraPosistion, y_extraPosistion)
	plt.draw()
	# pdb.set_trace()
	# for order in range(1, 4):
	#     s = InterpolatedUnivariateSpline(xi, yi, k=order)
	#     y = s(x)
	#     plt.plot(x, y)
	plt.show()

def smooth(xk, yk):
	# # x_smooth = np.linspace(xk.min(), xk.max(), 200)
	# # y_smooth = spline(xk, yk, x_smooth,order = 2)
	# y_smooth = np.linspace(yk.min(), yk.max(), 200)
	# # x_smooth = spline(yk, xk, y_smooth, order = 1)
	# s = InterpolatedUnivariateSpline(yk, xk, k=2)
	# x_smooth = s(y_smooth)
	# plt.plot(x_smooth, y_smooth, linewidth=1)

	f1 = interp1d(xk, yk, kind='linear', axis=-1, copy=True, bounds_error=True, fill_value=np.nan, assume_sorted=False)
	x_smooth_per_pixel = np.arange(xk.min(), xk.max(),0.5)
	y_smooth_per_pixel = f1(x_smooth_per_pixel)
	x_smooth_same_len = np.linspace(x_smooth_per_pixel.min(), x_smooth_per_pixel.max(),len(xk))
	f2 = interp1d(x_smooth_per_pixel, y_smooth_per_pixel, kind='slinear', axis=-1, copy=True, bounds_error=True, fill_value=np.nan, assume_sorted=False)
	y_smooth_same_len = f2(x_smooth_same_len)
	# plt.plot(x_smooth, y_smooth, linewidth=1)
	# plt.draw()
	# pdb.set_trace()
	return x_smooth_same_len, y_smooth_same_len


# k-means on polynomial coefs
def kmeansPolyCoeff(p3):
	np.random.seed(5)
	estimators = {'k_means_20': KMeans(n_clusters=20),
	              'k_means_8': KMeans(n_clusters=8),
	              'k_means_bad_init': KMeans(n_clusters=30, n_init=1,
	                                              init='random')}

	fignum = 1
	for name, est in estimators.items():
	    est.fit(p3)
	    labels = est.labels_
	    fig = plt.figure(fignum, figsize=(4, 3))
	    plt.clf()
	    plt.title(str(name))
	    ax = Axes3D(fig, rect=[0, 0, .95, 1], elev=48, azim=134)

	    plt.cla()
	    ax.scatter(p3[:1000, 0], p3[:1000, 1], p3[:1000, 2], c=labels[:1000].astype(np.float))

	    # ax.w_xaxis.set_ticklabels([])
	    # ax.w_yaxis.set_ticklabels([])
	    # ax.w_zaxis.set_ticklabels([])
	    fignum = fignum + 1

def readData(matfile):
	# print "Processing truncation...", str(matidx+1)
	ptstrj = loadmat(matfile)
	x    = csr_matrix(ptstrj['xtracks'], shape=ptstrj['xtracks'].shape).toarray()
	y    = csr_matrix(ptstrj['ytracks'], shape=ptstrj['ytracks'].shape).toarray()
	return x,y,ptstrj


def getSmoothMtx(x,y):
	x_smooth_mtx = np.zeros(x.shape)
	y_smooth_mtx = np.zeros(y.shape)
	xspd_smooth_mtx = np.zeros(x.shape)
	yspd_smooth_mtx = np.zeros(y.shape)

	for kk in range(0,x.shape[0],1):
		xk = x[kk,:][x[kk,:]!=0]
		yk = y[kk,:][y[kk,:]!=0]
		if len(xk)>5 and (min(xk.max()-xk.min(), yk.max()-yk.min())>2): # range span >=2 pixels  # loger than 5, otherwise all zero out
			x_smooth, y_smooth = smooth(xk, yk)
			x_smooth_mtx[kk,:][x[kk,:]!=0]=x_smooth
			y_smooth_mtx[kk,:][y[kk,:]!=0]=y_smooth
			xspd_smooth = np.diff(x_smooth)
			# xaccelerate = np.diff(xspd_smooth)
			yspd_smooth = np.diff(y_smooth)
			# yaccelerate = np.diff(yspd_smooth)
			xspd_smooth_mtx[kk,:][np.where(x[kk,:]!=0)[0][1:]]=xspd_smooth
			yspd_smooth_mtx[kk,:][np.where(x[kk,:]!=0)[0][1:]]=yspd_smooth
	return x_smooth_mtx,y_smooth_mtx,xspd_smooth_mtx,yspd_smooth_mtx


def plotTrj(x,y,p3=[],Trjchoice=[]):
	if Trjchoice==[]:
		Trjchoice=range(x.shape[0])

	plt.ion()
	plt.figure()
	for ii in range(0,len(Trjchoice),1):
		kk = Trjchoice[ii]
		xk = x[kk,:][x[kk,:]!=0]
		yk = y[kk,:][y[kk,:]!=0]
		if len(xk)>=5 and (min(xk.max()-xk.min(), yk.max()-yk.min())>2): # range span >=2 pixels
			# plt.plot(xk)
			# plt.plot(yk)
			# plt.plot(xk, yk)
			# extraPolate(xk, yk)
			'''1'''
			x_fit = np.linspace(xk.min(), xk.max(), 200)
			# y_fit = pow(x_fit,3)*p3[ii,0] + pow(x_fit,2)*p3[ii,1] + pow(x_fit,1)*p3[ii,2]+ p3[ii,3]
			y_fit = pow(x_fit,2)*p3[ii,0]+pow(x_fit,1)*p3[ii,1]+ p3[ii,2]

			x_range = xk.max()-xk.min()
			x_fit_extra = np.linspace(max(0,xk.min()-x_range*0.50), min(xk.max()+x_range*0.50,700), 200)
			# y_fit_extra = pow(x_fit_extra,3)*p3[ii,0] + pow(x_fit_extra,2)*p3[ii,1] + pow(x_fit_extra,1)*p3[ii,2]+ p3[ii,3]
			y_fit_extra = pow(x_fit_extra,2)*p3[ii,0]+pow(x_fit_extra,1)*p3[ii,1]+ p3[ii,2]
			
			# '''2'''
			# y_fit = np.linspace(yk.min(), yk.max(), 200)
			# x_fit = pow(y_fit,3)*p3[ii,0] + pow(y_fit,2)*p3[ii,1] + pow(y_fit,1)*p3[ii,2]+ p3[ii,3]
			plt.plot(x_fit_extra, y_fit_extra,'r')
			plt.plot(x_fit, y_fit,'g')
			plt.draw()
	plt.show()

def saveSmoothMat(x_smooth_mtx,y_smooth_mtx,xspd_smooth_mtx,yspd_smooth_mtx,p3,goodTrj,ptstrj,matfile):
	print "saving smooth new trj:", matfile
	'only keep the goodTrj, delete all bad ones'
	ptstrjNew = {}
	ptstrjNew['xtracks'] = csr_matrix(x_smooth_mtx[goodTrj,:])
	ptstrjNew['ytracks'] = csr_matrix(y_smooth_mtx[goodTrj,:])
	ptstrjNew['Ttracks'] = ptstrj['Ttracks'][goodTrj,:]
	ptstrjNew['Huetracks'] = ptstrj['Huetracks'][goodTrj,:]
	ptstrjNew['trjID']     = ptstrj['trjID'][:,goodTrj]
	ptstrjNew['fg_blob_index']    = ptstrj['fg_blob_index'][goodTrj,:] 
	ptstrjNew['fg_blob_center_X'] = ptstrj['fg_blob_center_X'][goodTrj,:]
	ptstrjNew['fg_blob_center_Y'] = ptstrj['fg_blob_center_Y'][goodTrj,:] 
	ptstrjNew['polyfitCoef'] = p3

	ptstrjNew['xspd'] = csr_matrix(xspd_smooth_mtx[goodTrj,:])
	ptstrjNew['yspd'] = csr_matrix(yspd_smooth_mtx[goodTrj,:])

	# parentPath = os.path.dirname(matfile)
	# smoothPath = os.path.join(parentPath,'smooth/')
	# if not os.path.exists(smoothPath):
	# 	os.mkdir(smoothPath)
	# onlyFileName = matfile[len(parentPath)+1:]
	onlyFileName = matfile[len(DataPathobj.kltpath):]
	savename = os.path.join(DataPathobj.smoothpath,onlyFileName)
	savemat(savename,ptstrjNew)



def main(matfile):
	# "if consecutive points are similar to each other, merge them, using one to represent"
	# didn't do this, smooth and resample instead
	x,y,ptstrj = readData(matfile)
	x_smooth_mtx,y_smooth_mtx,xspd_smooth_mtx,yspd_smooth_mtx = getSmoothMtx(x,y)
	# plotTrj(x_smooth_mtx,y_smooth_mtx)
	p3,goodTrj = polyFitTrj(x_smooth_mtx,y_smooth_mtx,xspd_smooth_mtx,yspd_smooth_mtx)
	# kmeansPolyCoeff(p3)
	# plotTrj(x_smooth_mtx,y_smooth_mtx,p3,goodTrj)
	saveSmoothMat(x_smooth_mtx,y_smooth_mtx,xspd_smooth_mtx,yspd_smooth_mtx,p3,goodTrj,ptstrj,matfile)



if __name__ == '__main__':		
	# define start and end regions
	#Canal video's dimensions:
	"""(528, 704, 3)
	start :<=100,
	end: >=500,"""

	start_Y = 100;
	end_Y   = 500;

	# matfilepath    = '/Users/Chenge/Desktop/testklt/'
	matfilepath = DataPathobj.kltpath
	matfiles       = sorted(glob.glob(matfilepath + 'klt_*.mat'))
	start_position = 0 
	matfiles       = matfiles[start_position:]

	for matidx,matfile in enumerate(matfiles):
		main(matfile)








