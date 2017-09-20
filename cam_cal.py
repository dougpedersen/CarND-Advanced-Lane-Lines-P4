# -*- coding: utf-8 -*-

import numpy as np
import cv2
#import matplotlib.pyplot as plt
#import matplotlib.image as mpimg
import pickle
import glob

def main(): 
    
    # dimensions of chessboard corners.
    nx, ny = 9, 6
    
    # prepare object points (0,0,0), (1,0,0), (2,0,0) .. (8,5,0)
    objp = np.zeros((nx*ny,3), np.float32)
    objp[:,:2] = np.mgrid[:nx, :ny].T.reshape(-1,2)
    
    # arrays to store object points and image points.
    objpoints = [] # 3d points in the real world
    imgpoints = [] # 2d points in image space 
    
    images = glob.glob('camera_cal/*.jpg')
    
    
    # use all available images to calibrate the camera.
    for idx, fname in enumerate(images):
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # find chessboard corners.
        ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
        
        # if found, populate objpoints and imgpoints. 
        if ret == True:
            print ('working on ', fname)
            objpoints.append(objp)
            imgpoints.append(corners)    
            # draw corners here for debug
            cv2.drawChessboardCorners(img, (nx, ny), corners, ret)
            write_name = './output_images/corners_found' + str(idx) + '.jpg'
            cv2.imwrite(write_name, img)
        else:  
            print ('rejected ', fname)
    w,h = img.shape[1], img.shape[0]
    
    # compute camera calibration matrix and distortion coefficients.
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, 
                                                       (w,h), None, None)
    # Output an undistorted checkerboard for debug/writeup
    for idx, fname in enumerate(images):
        img = cv2.imread(fname)
        img = cv2.undistort(img,mtx,dist,None,mtx)
        write_name = './output_images/undistorted'+str(idx)+'.jpg'
        cv2.imwrite(write_name, img)
    
    dist_pickle = {}
    dist_pickle['mtx'] = mtx
    dist_pickle['dist'] = dist
    pickle.dump(dist_pickle, open("./camera_cal/Calibration_pickle.p", "wb"))    
    
if __name__ == '__main__':
    main()
