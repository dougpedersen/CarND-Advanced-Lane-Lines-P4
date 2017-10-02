## P4 - Advanced Lane Finding Project Writeup

The goals / steps of this project are the following:

* Compute the camera calibration matrix and distortion coefficients given a set of chessboard images.
* Apply a distortion correction to raw images.
* Use color transforms, gradients, etc., to create a thresholded binary image.
* Apply a perspective transform to rectify binary image ("birds-eye view").
* Detect lane pixels and fit to find the lane boundary.
* Determine the curvature of the lane and vehicle position with respect to center.
* Warp the detected lane boundaries back onto the original image.
* Output visual display of the lane boundaries and numerical estimation of lane curvature and vehicle position.

[//]: # (Image References)

[image1]: ./camera_cal/calibration5.jpg "Original"
[image2]: ./output_images/undistorted15.jpg "Undistorted checkerboard"
[image3]: ./test_images/test4.jpg "Original Road"
[image4]: ./test_images/undistorted/undist3.jpg "Undistorted Road"
[image5]: ./test_images/thresholds/thresh3.jpg "Thresholded Road"
[image6]: ./test_images/warped/warp4.jpg "Warped Road"
[image7]: ./test_images/tracked/trackedb3.jpg "Warped Road"
[image8]: ./test_images/lanes/tracked3.jpg "Estimated Lane on Road"
[video1]: ./project_video.mp4 "Source Video"

## [Rubric](https://review.udacity.com/#!/rubrics/571/view) Points

### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---

### Writeup / README

#### 1. This Writeup / README includes all the rubric points and how I addressed each one.  

You're reading it!

### Camera Calibration

#### 1. Briefly state how you computed the camera matrix and distortion coefficients. Provide an example of a distortion corrected calibration image.

The code for this step is contained cam_cal.py  

I start by preparing "object points", which will be the (x, y, z) coordinates of the chessboard corners in the world (cam_cal.py, lines 16-17). Here I am assuming the chessboard is fixed on the (x, y) plane at z=0, such that the object points are the same for each calibration image.  Thus, `objp` is just a replicated array of coordinates, and `objpoints` will be appended with a copy of it every time I successfully detect all chessboard corners in a test image.  

`imgpoints` will be appended with the (x, y) pixel position of each of the corners in the image plane with each successful 6x9 chessboard detection by cv2.findChessboardCorners (cam_cal.py, line 32). Images camera_cal\calibration1.jpg, calibration4.jpg, and calibration5.jpg were not detected because of obscured corners. 

I then used the output `objpoints` and `imgpoints` to compute the camera calibration and distortion coefficients using the `cv2.calibrateCamera()` function (cam_cal.py, line 48).  I applied this distortion correction to a calibration image using the `cv2.undistort()` function and obtained this result: 

![alt text][image1] 

Undistorted:
![alt text][image2]

### Pipeline (single images)

#### 1. An example of a distortion-corrected image.

The distortion correction was applied to the test images using the cv2 undistort() function and the camera matrix and distortion coefficients, mtx and dist, calculated in cam_cal.py.  Here is an example of the correction, mostly evident in the bottom corners:
![alt text][image3] 

Undistorted:
![alt text][image4]

#### 2. Description of color transforms, gradients or other methods to create a thresholded binary image.  Provide an example of a binary image result.

Note: the files image_process.py and video_process.py have the duplicate functions that are discussed here. I will refer to their implementation in video_process.py. Much of this work is based on the examples in the project walk through: [Self-Driving Car Project Q&A - Advanced Lane Finding](http://www.youtube.com/watch?v=vWY8YUayf9Q)   

I used a combination of color and gradient thresholds to generate a binary image. There are 4 functions to apply:

- abs_sobel_thresh() Sobel x or y, then take the absolute value and apply a threshold
- mag_thresh() 		 Sobel x and y, then compute the magnitude of the gradient and apply a threshold
- dir_threshold() 	 Sobel x and y, then compute the angle of the gradient and apply a threshold
- color_threshold()  Transform color space to HLS and HSV, return binary values meeting the S and V thresholds.  

Thresholding routines are at lines 25 through 94 in `video_process.py` and the usage is at lines 108-112.  Here's an example of my output for this step (mag_thresh and dir_thresh were include but not used for the final images).  

![alt text][image5]

#### 3. Description of performed perspective transform and provide an example of a transformed image.

The code for the perspective transform appears in lines 114 through 128 in the file `video_process.py`. The warping code uses an image (`preprocessImage`), as well as source (`src`) and destination (`dst`) points.  The source points were defined parametrically based on a trapezoidal specification of the lane image. The parameters for the trapezoid were in terms of percent of image bottom width, middle width, bottom trim and top height. I lowered the bottom trip 94.5% (cut of 5.5%) so that a little of the car hood was included. This was done because it improved the curve fits close to the car. The destination was set to the middle 50 percent of the image width, and the full height, where the original image size was 1280x720.  

This resulted in the following source and destination points:

Source: 
       
 589,         446

 691,         446

1126,         680

 154,         680

Destination:

320,     0

960,     0

960,   720

320,   720

I verified that my perspective transform was working as expected by drawing the `src` and `dst` points onto a test image and its warped counterpart to verify that the lines appear parallel in the warped image, as can be seen below:

![alt text][image6]


#### 4. Description of how (and identify where in your code) you identified lane-line pixels and fit their positions with a polynomial?

The lane finding code was in function 'find_window_centroids()' on line 30 of 'tracker.py'. The warped image was input and divided up into 9 vertical layers (720/80 = 0). The layers were convolved with a rectangular window, with a width of 25 and the peaks used for the left and right estimates on lines 51 through 64. The bottom layer was a simple peak find of the summed vertical lines on lines 42-45. The left and right center estimates were used to make 9 boxes on each layer for each side. 

The center of the estimated line boxes were fit with a 2nd order polynomial on lines 171-176 of 'video_process.py'.  Here is an example image with the curve fit shown: 

![alt text][image7]



#### 5. Describe how (and identify where in your code) you calculated the radius of curvature of the lane and the position of the vehicle with respect to center.

I did this in lines 202 through 214 in my code in `video_process.py`. This code performed the calculation outlined in section 35 of the project lessons. Given the 2nd order curve fit, curve_fit_cr, to the center of the estimated line boxes for the left lane line, the radius of curvature is: 

Rcurve = (1 + (2Ay + B)^2)^(3/2) / abs(2A)  

The radius was found for both the left and right lanes and then averaged for the video text output.

The position of the camera with respect to the center of the lane was calculated in the same section of code. It averages the ends of the lines closest to the camera and compares this x estimate to the center of the image (width/2).

Both estimates are scaled by rough estimates of m's per pixel and are printed on the output images.

#### 6. Example image of result plotted back down onto the road such that the lane area is identified clearly.

This step is implemented in lines 178 through 196 in `video_process.py` in the function `process_image()`.  Here is an example of my result on a test image:

![alt text][image8]

---

### Pipeline (video)

#### 1. Link to your video output.  The pipeline performs reasonably well on the entire project video (some wobbly lines, but no catastrophic failures that cause the car to drive off the road).

## TODO: restrict the right lane line. At about 30.5s it went to the corner.
Use VideoFileClip("project_video.mp4").subclip(28,33)

Here's a [link to my video result](./output3_tracked.mp4) 

---

### Discussion

#### 1. Briefly discuss any problems / issues you faced in your implementation of this project.  Where will your pipeline likely fail?  What could you do to make it more robust?

After review, I added code in lines 135 through 142 in `video_process.py` to reject lane estimates that are too wide at the bottom of the image.  This was a shortcoming of the original method used. If the lane estimate is too wide, the previous estimate is used. This smoothed the output.

I think it would be helpful to have an indication on confidence. Checking if the convolution did not return a high enough value or that the left and right lane line estimates are not parallel curves would be a good way to eliminate false data. 

The pipeline can fail if the lines move fasted that the sliding window search allows. This could be caused by a curvy or hilly road. It can also fail if objects like cars obstruct the view or the lines temporarily disappear, e.g. construction or intersections.
