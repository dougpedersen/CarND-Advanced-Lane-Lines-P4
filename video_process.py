# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 16:58:14 2017

@author: Doug_Pedersen
"""

from moviepy.editor import VideoFileClip
#from IPython.display import HTML
import numpy as np
import cv2
import pickle
#import glob
from tracker import tracker
# Read in the saved objpoints and imgpoints
dist_pickle = pickle.load(open("camera_cal/calibration_pickle.p", "rb"))
mtx = dist_pickle["mtx"]
dist = dist_pickle["dist"]
good_frames = 0
window_centroids_prev = 0
# abs_sobel_thresh - applies Sobel x or y, 
# then takes an absolute value and applies a threshold.
# Note: calling your function with orient='x', thresh_min=5, thresh_max=100
# should produce output like the example image shown above this quiz.
def abs_sobel_thresh(img, orient='x', sobel_kernel=3, thresh=(0,255)):
    
    # Apply the following steps to img
    # 1) Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # 2) Take the derivative in x or y given orient = 'x' or 'y'
    if orient == 'x':
        # x deriv
        sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 0)
    if orient == 'y':
        # y deriv
        sobel = cv2.Sobel(gray, cv2.CV_64F, 0, 1)
    # 3) Take the absolute value of the derivative or gradient
    abs_sobel = np.absolute(sobel)
    # 4) Scale to 8-bit (0 - 255) then convert to type = np.uint8
    scaled_sobel = np.uint8(255*abs_sobel/np.max(abs_sobel))
    # 5) Create a mask of 1's where the scaled gradient magnitude
    #   is > thresh_min and < thresh_max
    binary_output = np.zeros_like(scaled_sobel)
    binary_output[(scaled_sobel >= thresh[0]) & (scaled_sobel <= thresh[1])] = 1
    # 6) Return this mask as your binary_output image
    return binary_output
    
# mag_thresh - applies Sobel x and y, 
# then computes the magnitude of the gradient
# and applies a threshold
def mag_thresh(img, sobel_kernel=3, mag_thresh=(0, 255)):
    
    # Apply the following steps to img
    # 1) Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # 2) Take the gradient in x and y separately
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel)
    # 3) Calculate the magnitude 
    gradmag = np.sqrt(sobelx**2 + sobely**2)
    # 4) Scale to 8-bit (0 - 255) and convert to type = np.uint8
    scale_factor = np.max(gradmag)/255 
    gradmag = (gradmag/scale_factor).astype(np.uint8) 
    # 5) Create a binary mask where mag thresholds are met
    binary_output = np.zeros_like(gradmag)
    binary_output[(gradmag >= mag_thresh[0]) & (gradmag <= mag_thresh[1])] = 1

    # 6) Return this mask as your binary_output image
    return binary_output
    
def dir_threshold(img, sobel_kernel=3, thresh=(0, np.pi/2)):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel)
    with np.errstate(divide='ignore', invalid = 'ignore'):
        absgraddir = np.absolute(np.arctan(sobely, sobelx))
        binary_output = np.zeros_like(absgraddir)
        binary_output[(absgraddir >= thresh[0]) & (absgraddir <= thresh[1])] = 1
    return binary_output
        
        
def color_threshold(img, sthresh=(0, 255),vthresh=(0, 255)):
    hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
    s_channel = hls[:,:,2]
    s_binary = np.zeros_like(s_channel)
    s_binary[(s_channel >= sthresh[0]) & (s_channel <= sthresh[1])] = 1
    
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    v_channel = hsv[:,:,2]
    v_binary = np.zeros_like(v_channel)
    v_binary[(v_channel >= vthresh[0]) & (v_channel <= vthresh[1])] = 1
    output = np.zeros_like(s_channel)
    output[(s_binary == 1) & (v_binary == 1)] = 1
    return output
    
def window_mask(width, height, img_ref, center, level): # level = vertical slice that we're using
    output = np.zeros_like(img_ref)
    output[int(img_ref.shape[0]-(level+1)*height):int(img_ref.shape[0]-level*height), max(0,int(center-width)):min(int(center+width),img_ref.shape[1])] = 1
    return output
    
#images = glob.glob('./test_images/test*jpg')
#for idx, fname in enumerate(images):

def process_image(img):
    global good_frames 
    global window_centroids_prev
    img = cv2.undistort(img,mtx,dist,None,mtx)
    # predict image and generate binary pixels of interest
    preprocessImage = np.zeros_like(img[:,:,0])
    gradx = abs_sobel_thresh(img, orient = 'x', thresh=(12, 255)) # 12
    grady = abs_sobel_thresh(img, orient = 'y', thresh=(25, 255)) # 25
    c_binary = color_threshold(img, sthresh=(100, 255),vthresh=(50, 255))
    preprocessImage[((gradx ==1) & (grady ==1) | (c_binary ==1))] = 255
    # define perspective transform area - trying to get bottom width of lane = top width (parallel)
    img_size = (img.shape[1],img.shape[0])
    bot_width = 0.76 # % of bottom trapezoid height
    mid_width = 0.08 # % of middle trapezoid height
    height_pct = 0.62 # % for trapezoid height (how far we're looking down the road)
    bottom_trim = 0.945 # % from top to bottom to avoid car hood
    src = np.float32([[img.shape[1]*(0.5-mid_width/2),img.shape[0]*height_pct], [img.shape[1]*(0.5+mid_width/2),img.shape[0]*height_pct],
                       [img.shape[1]*(.5+bot_width/2),img.shape[0]*bottom_trim],[img.shape[1]*(0.5-bot_width/2), img.shape[0]*bottom_trim]]) 
    offset = img_size[0]*0.25
    dst = np.float32([[offset, 0], [img_size[0]-offset, 0],[img_size[0]-offset, img_size[1]], [offset, img_size[1]]]) 
    
    # perform transformation
    M = cv2.getPerspectiveTransform(src, dst)
    Minv = cv2.getPerspectiveTransform(dst, src)
    warped = cv2.warpPerspective(preprocessImage, M, img_size, flags = cv2.INTER_LINEAR)
    
    window_width = 25
    window_height = 80
    # Set up overall class to do all the tracking, Originally had My_xm = 4/384
    curve_centers = tracker(Mywindow_width = window_width, Mywindow_height = window_height, Mymargin = 25, My_ym = 30/720, My_xm = 3.7/520 , Mysmooth_factor = 20)
    window_centroids = curve_centers.find_window_centroids(warped)
    lane_max_pix = 580
    if (window_centroids[0][1]-window_centroids[0][0]) > lane_max_pix:
        print('Rejected lane width of: '+str(window_centroids[0][1]-window_centroids[0][0])+' pixels' )
        if good_frames > 0:
            window_centroids = window_centroids_prev 
    else:
        window_centroids_prev = window_centroids
        good_frames = good_frames + 1 
    # Points used to draw all the left and right windows
    l_points = np.zeros_like(warped)
    r_points = np.zeros_like(warped)
    # points used to find the left and right lanes
    rightx = []
    leftx = []
    # Go thru each level and draw the windows
    for level in range(0,len(window_centroids)):
        # Window_mask is a function to draw window areas
        l_mask = window_mask(window_width, window_height, warped, window_centroids[level][0], level)
        r_mask = window_mask(window_width, window_height, warped, window_centroids[level][1], level)
        # add center value found in frame to the list of lane points per left, right
        leftx.append(window_centroids[level][0])
        rightx.append(window_centroids[level][1])
        
        #Add graphic points from window mask here to total pixels found
        l_points[(l_points == 255) | ((l_mask == 1))] = 255
        r_points[(r_points == 255) | ((r_mask == 1))] = 255
        
    # Draw the results
    template = np.array(r_points+l_points,np.uint8) # add both left and right windw pixels together
    zero_channel = np.zeros_like(template)  # zero color channels
    template = np.array(cv2.merge((zero_channel, template, zero_channel)),np.uint8) # make window pixels green
    warpage = np.array(cv2.merge((warped, warped, warped)),np.uint8) # making the original road pixels 3 color channels
    result = cv2.addWeighted(warpage, 1, template, 0.5, 0.0) # overlay the original road image with window results
        
    # fit a curve to the center of the layers boxes 
    yvals = range(0, warped.shape[0]) # 1 pixel increments for plotting
    res_yvals = np.arange(warped.shape[0]-(window_height/2), 0, -window_height)
    
    left_fit = np.polyfit(res_yvals, leftx, 2)    
    left_fitx = left_fit[0]*yvals*yvals + left_fit[1]*yvals + left_fit[2]
    left_fitx = np.array(left_fitx, np.int32)
    right_fit = np.polyfit(res_yvals, rightx, 2)    
    right_fitx = right_fit[0]*yvals*yvals + right_fit[1]*yvals + right_fit[2]
    right_fitx = np.array(right_fitx, np.int32)
    
    left_lane = np.array(list(zip(np.concatenate((left_fitx-window_width/2,left_fitx[::-1]+window_width/2), axis=0),np.concatenate((yvals,yvals[::-1]),axis=0))),np.int32)
    right_lane = np.array(list(zip(np.concatenate((right_fitx-window_width/2,right_fitx[::-1]+window_width/2), axis=0),np.concatenate((yvals,yvals[::-1]),axis=0))),np.int32)
    inner_lane = np.array(list(zip(np.concatenate((left_fitx+window_width/2,right_fitx[::-1]-window_width/2), axis=0),np.concatenate((yvals,yvals[::-1]),axis=0))),np.int32)

    road = np.zeros_like(img)
    road_bkg = np.zeros_like(img)
    cv2.fillPoly(road,[left_lane], color=[255, 0, 0])
    cv2.fillPoly(road,[right_lane], color=[0, 0, 255])
    cv2.fillPoly(road,[inner_lane], color=[0, 255, 0])
    cv2.fillPoly(road_bkg,[left_lane], color=[255, 255, 255])
    cv2.fillPoly(road_bkg,[right_lane], color=[255, 255, 255])
    # result = road # plot lines
    
    road_warped = cv2.warpPerspective(road,Minv,img_size,flags=cv2.INTER_LINEAR)
    road_warped_bkg = cv2.warpPerspective(road_bkg,Minv,img_size,flags=cv2.INTER_LINEAR)
    
    #result = cv2.addWeighted(img, 1.0, road_warped, 1.0, 0.0)
    base = cv2.addWeighted(img, 1.0, road_warped_bkg, -1.0, 0.0)
    result = cv2.addWeighted(base, 1.0, road_warped, 0.7, 0.0)
    ym_per_pix = curve_centers.ym_per_pix # m's per pixel in y dim
    xm_per_pix = curve_centers.xm_per_pix # m's per pixel in x dim
    # find radius of left lane line, then right in real units, then take average
    curve_fit_cr = np.polyfit(np.array(res_yvals, np.float32)*ym_per_pix, np.array(leftx, np.float32)*xm_per_pix, 2)
    curveradl = ((1 + (2*curve_fit_cr[0]*yvals[-1]*ym_per_pix + curve_fit_cr[1])**2)**1.5) / np.absolute(2*curve_fit_cr[0])
    curve_fit_cr = np.polyfit(np.array(res_yvals, np.float32)*ym_per_pix, np.array(rightx, np.float32)*xm_per_pix, 2)
    curveradr = ((1 + (2*curve_fit_cr[0]*yvals[-1]*ym_per_pix + curve_fit_cr[1])**2)**1.5) / np.absolute(2*curve_fit_cr[0])
    curverad = (curveradl + curveradr)/2
    # calculate the offset of the car in the lane
    camera_center = (left_fitx[-1] + right_fitx[-1])/2 # closest fit points to car
    center_diff = (camera_center-warped.shape[1]/2)*xm_per_pix
    side_pos = 'left'
    if center_diff <= 0:
        side_pos = 'right'
        
    # draw the text showing curvature and offset
    cv2.putText(result, 'Radius of Curvature = '+str(round(curverad,3))+' (m)', (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(result, 'Vehicle is '+str(abs(round(center_diff,3)))+'m '+side_pos+' of center',(50,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    # print(str(abs(round(center_diff,3)))+'m '+side_pos+' of center')
    # print(str(abs(round((right_fitx[-1]-left_fitx[-1]),3)))+' pix width'+str(round(curveradl,3))+' (m) '+str(round(curveradr,3))+' (m)')
    # print(str(abs(round((left_fitx[-1] + right_fitx[-1])*xm_per_pix,3)))+'m width')
    # print(str(round(curveradl,2))+'m l, '+str(round(curveradr,2))+'m rt')
    return result



Output_video = './output3_tracked.mp4'
Input_video = 'project_video.mp4'

clip1 = VideoFileClip(Input_video) #.subclip(29,32)
video_clip = clip1.fl_image(process_image)  # expects color images
video_clip.write_videofile(Output_video, audio=False)

