import pygame.camera
pygame.camera.init() ##initializing the camera module
camlist = pygame.camera.list_cameras()

imgsize = (640, 480)
#imgsize = (1024, 768)
#imgsize = (800, 600)
displaytest = pygame.display.set_mode(imgsize, 0)

from skimage import data

from skimage import filter

import numpy as np

import os


###############################
##DR: Update April 18th 2015
##We found out how to not write temporary files to disk when taking screenshots.
##The solution was to use 'pgmagick', which provides bindings to the ImageMagick functionality
##and allows us to take screenshots and save them to images, then blobs, then into PIL, then finally into Pygame.
##All this while holding the screenshot in memory, meaning we cut out saving and reading.
##Unfortunately, it doesn't really look like we can set size parameters or anything, so it's defaulting to 800x600.
##Hopefully the lack of temporary writing will make up for this resolution increase.
###############################

#import pgmagick

#from PIL import Image

#from cStringIO import StringIO


#testimage = np.fromfile('photowebcam.bmp', dtype='uint8')
#testimage = pygame.image.load('beautifulme.bmp')

#############################################################
##DR: We've got a working greenscreen program now, 'functionalgreenscreenprogram.py'
##So we can take any arbitrary image (so long as it's 640*480, the resolution we take the webcam images at)
##
##UPDATED: WE TRIED TO OPTIMIZE BY CUTTING OUT CODE
##But we were still getting incredibly laggy (<10fps) results when trying to go to 1240x720 resolution.
##I would expect that when we have this program, in conjunction with Orbiter, running, that we'd get even fewer fps, maybe even stalling.
##So we're going to stick to 640*480 resolution for now (Orbiter isn't that HD anyways), and maybe if we get access to a better computing system
##we'll be able to go to higher resolutions.
##############################################################


def inversemaskmaker(image, backcolour, screen="none"): ##Everything that IS the greenscreen, as the other function returns a bool for everything NOT the greenscreen.
	##The 'image' should already by a 3d numpy array.
	##As well, we've designed this function to work primarily with RGB images (in that we make assumptions on the order of the 'backcolour' tuple, thresholding, etc.
	
	#buffersize = 100 ##T'was originally 25
	buffersize = 75 ##T'was originally 25
	##50 kept more hand
	
	lowerlimitlist = list()
	upperlimitlist = list() 
	for colour in backcolour[0:3]: ##Remember that python's indexing (0:3) will really only grab 0, 1 and 2 (i.e. it is top exclusive).
		lowerlim = colour - buffersize
		if (lowerlim <= 0):
			lowerlim = 0
		upperlim = colour+buffersize
		if (upperlim >= 255):
			upperlim = 255
		lowerlimitlist.append(lowerlim)
		upperlimitlist.append(upperlim)
	
	#print("COLOUR THRESHOLDS")
	#colourlimits = [list((x,y)) for x,y in zip(lowerlimitlist, upperlimitlist)]
	#print(x,y) for x,y in zip(lowerlimitlist, upperlimitlist)
	#print(colourlimits)
	
	if (screen == "green"): ##We're using a green screen
		#greenval = backcolour[1] ##In RGB tuple, the green val.
		R = [(0, 255), (lowerlimitlist[1], upperlimitlist[1]), (0, 255)]
			##I guess we assume that greenval is going to be greater than 25?
	elif (screen == "red"): #A red screen? Suppose it's possible.
		#redval = backcolour[0] ##RGB tuple red value.
		R = [(lowerlimitlist[0], upperlimitlist[1]), (0, 255), (0, 255)]
	elif (screen == "blue"):
		#blueval = backcolour[2] ##RGB tuple blue value.
		R = [(0,255), (0, 255), (lowerlimitlist[2], upperlimitlist[2])]
	else: ##No screen specified, so we'll just take the average background colour and use that as the threshold for all colours.
		R = [(lowerlimitlist[0], upperlimitlist[0]), (lowerlimitlist[1], upperlimitlist[1]), (lowerlimitlist[2], upperlimitlist[2])]
		##^^Range for average colour of background (RGB).
	red_range = np.logical_and(R[0][0] < image[:,:,0], image[:,:,0] < R[0][1]) ##Basically going through every pixel and ensuring it's in the current colour's value range. If yes, then it returns a true. We use the chained 'and' statement at the end to see if a pixel satisfies EACH of the three colour threshold ranges, then returns a true for that pixel (which we use to generate our mask).
	green_range = np.logical_or(R[1][0] > image[:,:,0], image[:,:,0] > R[1][1]) ##Everything outside the green range is labelled false? Yes, this makes sense actually.
	blue_range = np.logical_and(R[2][0] < image[:,:,0], image[:,:,0] < R[2][1])
	valid_range = np.logical_and(red_range, green_range, blue_range)
	##^^This converts the three ranges to a chained 'and' statement? As in, if a pixel is within each pixel range (satisfying each 'if' boolean statement) then it produces a boolean TRUE?
	#image[valid_range] = 200 ##We fill everything that fits our 'valid_range' threshold chain with 200.
	##We're just going to experiment with using this function to produce masks and map values to masks as opposed to the method below that relies on the Otsu threshold, which fails for 3d (colour) images (as far as I can see).
	return(valid_range) ##We return a mask for the image, not the image itself. This is for later, when we overlay program windows on the mask of an image's background.



def maskmaker(image, backcolour, screen="none"):
	##The 'image' should already by a 3d numpy array.
	##As well, we've designed this function to work primarily with RGB images (in that we make assumptions on the order of the 'backcolour' tuple, thresholding, etc.
	
	#buffersize = 75 ##T'was originally 25
	buffersize = 50 ##T'was originally 25
	##50 kept more hand
	
	lowerlimitlist = list()
	upperlimitlist = list() 
	for colour in backcolour[0:3]: ##Remember that python's indexing (0:3) will really only grab 0, 1 and 2 (i.e. it is top exclusive).
		lowerlim = colour - buffersize
		if (lowerlim <= 0):
			lowerlim = colour
		upperlim = colour+buffersize
		if (upperlim >= 255):
			upperlim = colour
		lowerlimitlist.append(lowerlim)
		upperlimitlist.append(upperlim)
	
	print("COLOUR THRESHOLDS")
	colourlimits = [list((x,y)) for x,y in zip(lowerlimitlist, upperlimitlist)]
	#print(x,y) for x,y in zip(lowerlimitlist, upperlimitlist)
	print(colourlimits)
	
	if (screen == "green"): ##We're using a green screen
		#greenval = backcolour[1] ##In RGB tuple, the green val.
		R = [(0, 255), (lowerlimitlist[1], upperlimitlist[1]), (0, 255)]
			##I guess we assume that greenval is going to be greater than 25?
	elif (screen == "red"): #A red screen? Suppose it's possible.
		#redval = backcolour[0] ##RGB tuple red value.
		R = [(lowerlimitlist[0], upperlimitlist[1]), (0, 255), (0, 255)]
	elif (screen == "blue"):
		#blueval = backcolour[2] ##RGB tuple blue value.
		R = [(0,255), (0, 255), (lowerlimitlist[2], upperlimitlist[2])]
	else: ##No screen specified, so we'll just take the average background colour and use that as the threshold for all colours.
		R = [(lowerlimitlist[0], upperlimitlist[0]), (lowerlimitlist[1], upperlimitlist[1]), (lowerlimitlist[2], upperlimitlist[2])]
		##^^Range for average colour of background (RGB).
	red_range = np.logical_and(R[0][0] < image[:,:,0], image[:,:,0] < R[0][1]) ##Basically going through every pixel and ensuring it's in the current colour's value range. If yes, then it returns a true. We use the chained 'and' statement at the end to see if a pixel satisfies EACH of the three colour threshold ranges, then returns a true for that pixel (which we use to generate our mask).
	green_range = np.logical_and(R[1][0] < image[:,:,0], image[:,:,0] < R[1][1])
	blue_range = np.logical_and(R[2][0] < image[:,:,0], image[:,:,0] < R[2][1])
	valid_range = np.logical_and(red_range, green_range, blue_range)
	##^^This converts the three ranges to a chained 'and' statement? As in, if a pixel is within each pixel range (satisfying each 'if' boolean statement) then it produces a boolean TRUE?
	#image[valid_range] = 200 ##We fill everything that fits our 'valid_range' threshold chain with 200.
	##We're just going to experiment with using this function to produce masks and map values to masks as opposed to the method below that relies on the Otsu threshold, which fails for 3d (colour) images (as far as I can see).
	return(valid_range) ##We return a mask for the image, not the image itself. This is for later, when we overlay program windows on the mask of an image's background.


#cam = pygame.camera.Camera(camlist[1], (640, 480), "HSV") #YUV may be better for us to use for image processing? Not sure.
#cam = pygame.camera.Camera(camlist[1], (640, 480), "RGB") #YUV may be better for us to use for image processing? Not sure.
#cam = pygame.camera.Camera(camlist[0], (640, 480)) #YUV may be better for us to use for image processing? Not sure.
cam = pygame.camera.Camera(camlist[0], (320, 240)) #YUV may be better for us to use for image processing? Not sure.
#cam = pygame.camera.Camera(camlist[1], (800, 600)) #Will the slightly higher resolution lag us?

#cam = pygame.camera.Camera(camlist[1], (1280, 720)) #YUV may be better for us to use for image processing? Not sure.

##DR^ NOTE: This resolution is impossible on laptops (read: really, really laggy).

#cam = pygame.camera.Camera(camlist[1]) #YUV may be better for us to use for image processing? Not sure.
#cam.start()
#img = cam.get_image() #Should return an image object, of what class I'm not sure of.
##Will it be readable by scipy?

snapshot = pygame.surface.Surface(imgsize, 0, displaytest) ##providing a surface to write images to; just so we don't have to store images.

class Capture (object):
	def __init__(self, cameraobj):
		#self.size = (640, 480)
		self.size = (320, 240)
		#self.size = (800, 600) ##How much will this slow things down?
		#self.size = (1280, 720) ##<- Can't go to this kind of resolution on a laptop.
		self.display = pygame.display.set_mode(self.size, 0)
		self.cam = cameraobj
		self.cam.start()
		self.snapshot = pygame.surface.Surface(self.size, 0, self.display) ##providing a surface to write images to; just so we don't have to store images.
	def displayimg(self, update=False): ##We wait until the camera is ready to take a picture.
		#if self.cam.query_image():
		#	self.snapshot = self.cam.get_image(self.snapshot)
		if self.background:
			#print("accounting for background?")
			#self.snapshot = self.cam.get_image(self.snapshot)
			#self.snapshot = self.cam.get_image()
			
			#pygame.transform.threshold(self.thresholded,self.snapshot,(0,0,0),(0,0,0),(0,0,0),2,self.background)
			
			#self.snapshot = self.thresholded ##Applying an early fix to try to help the mask generation function.
			
			#self.thresholded = pygame.surface.Surface(self.size, 0, self.display)
			#pygame.transform.threshold(self.thresholded,self.snapshot,(0,0,255),(30,30,30),(0,0,0),1,self.background)
			#pygame.transform.threshold(self.thresholded,self.snapshot,(0,0,255), diff_color = (30,30,30),(255,0,0),1,self.background)
			#self.thresholded = pygame.surfarray.array3d(self.snapshot)
			#colouredimage = pygame.surfarray.array3d(self.snapshot)
			#colouredimage = pygame.surfarray.array3d(self.background)
			
			#self.testarray = np.array(np.asarray(self.background))
			#print(type(self.thresholded))
			#print(self.thresholded[1])
			#pygame.transform.laplacian(self.thresholded) ##Generating laplace lines?
			##We can use Sobel filtering provided by scipy instead.
			
			#colouredimage[15:50,:] = np.array((255,0,0)) ##Passing colours to a 3d array. Can't seem to specify specific pixel thought...?
			
			#self.transposed = np.transpose(colouredimage)
			
			#self.transposed = colouredimage
			'''
			val = filter.threshold_otsu(self.transposed)
			#self.val2 = filter.threshold_otsu(self.testarray)
			print("background colour")
			print(val)
			mask = self.transposed > val
			maskback = self.transposed < val
			self.mask = mask
			
			self.transposed = pygame.surfarray.array3d(self.snapshot) #grabbing the current image.
			'''
			
			#print("making maskedimage")
			#self.masked = maskmaker(self.transposed, self.backcolour, "green")
			#self.masked = maskmaker(self.transposed, self.backcolour, "green")
			#self.maskedimage = pygame.surfarray.array3d(self.snapshot)
			self.maskedimage = pygame.surfarray.array3d(self.cam.get_image())
			self.masked = inversemaskmaker(self.maskedimage, self.backcolour, "green")
			
			#self.maskedimage[self.masked] = 255 ##Writing to the mask?
			#samplearray = pygame.surfarray.array3d(self.sample)
			
			##Didn't work just trying to do a direct replacement of pixels...Probably because numpy doesn't like us trying to replace RGB values...it does this weird thing where it only replaces the red value...
			##So we're going to try generating a pygame surface, blitting the sample picture over it, and going from there.
			
			#self.parentmask = pygame.surface.Surface(self.size, 0, self.display) ##We use this to ensure that when we generate the mask surface that it's framed within the original image properly.
			
			#self.surfacemask = self.parentmask.subsurface() ##Making a subsurface so we can make our mask and have it in the same position?
			'''
			self.surfacemask = pygame.surfarray.make_surface(self.maskedimage[self.masked])
			
			self.parentpixels = pygame.PixelArray(self.parentmask) ##Empty surface.
			
			self.samplepixels = pygame.PixelArray(self.sample) ##The sample image that we're hoping to overlay.
			
			self.parentpixels[self.masked] = self.samplepixels[self.masked] ##Replacing the pixels in parentpixels with the same pixels in the sample image?
			
			self.overlayed = pygame.PixelArray.make_surface(self.parentpixels) ##Should hopefully be a surface with replaced pixels?
			
			print("Overlayed surface?")
			print(type(self.overlayed))
			
			self.finalimage = self.snapshot
			
			self.finalimage.blit(self.overlayed, (0, 0)) ##Should draw only those pixels with actual values, otherwise we draw 0's right? Or maybe they'll be black...
			
			
			#pygame.Surface.blit(
			'''
			
			#self.testshape = samplearray[1,1] ##Should be one pixel, right?
			#print(self.testshape.shape)
			
			#self.examplepixel = np.array([255,0,0], dtype='uint8')
			#self.examplepixel2 = np.array([0,0,255], dtype='uint8')
			##SO we should definetly be able to feed this into self.maskedimage, right?
			
			#self.maskedimage[self.masked] = samplearray[self.masked] ##Replacing the mask in the current image with a slice of the sample image within the same mask.
			#self.maskedimage[self.masked] = self.examplepixel ##Replacing the mask in the current image with a slice of the sample image within the same mask.
			
			#self.invertedmask = np.invert(self.masked) ##The original mask is everything that's not green...?
			##^^Tested. With a buffer of 75 pixels, we saw the hand completely turn red (while, ironically, the green screen remained unchanged).
			
			#self.testimagearray = pygame.surfarray.array3d(testimage)
			
			#os.system("import -window 0x05a00009 -resize 800 orbitertemp.bmp") ##Writing a temporary image, which we grab immediately after...
			##We should really figure out how to get import to write to a temporary file, or buffer, whatever, to avoid having to write to disk and back again.
			##Also, this returns us a 800x600 image, so we'll need to make sure to take webcam images at the same resolution, else getting index errors.
			
			if (update == True):
				
				img = pgmagick.Image()
				
				#img = Image((800, 600))
				
				#from pgmagick import Geometry
				
				#whatwhat = img.read("x:0x05a00009") ##Read is part of the pgmagick 'Image' class.
				#img.read("x:0x05a00009") ##Read is part of the pgmagick 'Image' class.
				img.read("x:0x04600009 -resize 320X240") ##Read is part of the pgmagick 'Image' class.
				
				#img.display()
				
				#img2 = Image(img, Geometry(800, 600))
				
				#img2.write('pgmagick.jpg')
				
				#print(img.type())
				
				#print("changed to png?")
				
				#img2 = Image()
				
				#img2.read("x:0x05a00009", pgmagick.Geometry(640, 480))
				
				#img2.write(filename = 'pgmagickimg2.jpg')
				
				#test = open('pgmagickapi.png', 'wb')
				#test.write('hello')
				#if (k <2):
				#	img.write('pgmagickapi.png') ##DR: So I have absolutely no idea why, but it seems that
				##img is a 800x600 image?
				
				
				#blob2 = pgmagick.Blob()
				
				#img.write(blob2)
				
				blob3 = pgmagick.Blob()
				#bloborig = pgmagick.Blob()
				
				#img.write('resizedSCREENSHOT.png')
				
				img.write(blob3, 'RGB', 16) ##Writing 16bit RGB blob?
				
				img = None ##Save RAM?
				
				
				#img.write(bloborig)
				#from pgmagick.api import Image
	
				#img = pgmagick.Image(bloborig, pgmagick.Geometry(640, 480))
				#img = pgmagick.Image(bloborig)
				
				#img.write('reblobbed2.png')
				
				#blob4 = pgmagick.Blob()
				
				#img.write(blob4, 'RGB', 16) ##Hopefully this allows us to change the resolution on the fly?
				
				#rbgstring = blob3.data
				
				#print(dir(blob2))
				
				#testdatastring = blob2.data ##Dear god, is this the BLOB data?!?!?!?
				
				#print(len(testdatastring))
				
				#unblob = pgmagick.Image(blob2) ##UPDATE: So we were able to successfully output 'unblob.png', which is generated from 'blob2', a blob form of 'img'.
				
				#unblob.write('unblob2.png')
				
				#import wand.image as wand
				
				#testwand = wand.Image(blob=testdatastring)
				
				#print("testwand made?")
				
				#testwand.save(filename ='testwand.png')
				
				#print("testwand saved?")
				'''
				import numpy as np
				
				#imageh = testwand.height
				#imagew = testwand.height
				
				
				#wandblob = testwand.make_blob()
				#arrayimage = np.array(testdatastring)
				#arrayimage.shape = (imagew, imageh, 3)
				
				from PIL import Image
				
				#tempfile = open('testtemp.png', 'wb')
				
				#testwand.save(file = tempfile)
				from cStringIO import StringIO
				#IOstream = StringIO(wandblob)
				IOstream2 = StringIO(testdatastring)
				
				#testPIL = Image.open(IOstream)
				testPIL2 = Image.open(IOstream2)
				
				print("PIL worked?")
				
				#testPIL.save('PILimage.png')
				#testPIL2.save('origblobPIL.png')
				
				print("saved PIL?")
				
				import pygame.camera
				
				mode = testPIL2.mode
				print(mode)
				print(type(mode)) ##Please be a str
				pilsize = testPIL2.size
				print(pilsize)
				print(type(pilsize))
				pildata = testPIL2.tostring()
				'''
				
				pygamesurface = pygame.image.fromstring(blob3.data, (800, 600), "RGB")
				#pygamesurface = pygame.image.fromstring(blob4.data, (640, 480), "RGB") ##We can't seem to be able to change this resolution.
				
				pygame.transform.scale(pygamesurface, (320, 240)) ##rescaling to 320, 240. Doesn't speed up shit.
				
				blob3 = None ##Clearing up some RAM?
				
				#print("made pygame surface?")
				
				#pygame.image.save(pygamesurface, 'pygamesurfacetest.png')
				
				#print("pygamesurface saved?")
				
				self.testimagearray = pygame.surfarray.array3d(pygamesurface) ##And the moment of truth, where our screenshot gets converted to a numpy array for later slicing into webcam image (via mask).
				
				##Since we preserve 'testimagearray' in 'self' between iterations, we can get away without defining it in between.
				
			#currtestimage = None ##'None' is python's equivalent to 'NULL'. We do this to try to free up RAM.
			
			#self.maskedimage[self.invertedmask] = self.examplepixel2 ##Basically, when I insert my hand, it should be blue.
			#self.maskedimage[self.invertedmask] = samplearray[self.invertedmask] ##Basically, when I insert my hand, it should be blue.
			#self.maskedimage[self.invertedmask] = self.testimagearray[self.invertedmask] ##Basically, when I insert my hand, it should be blue.
			#self.maskedimage[self.masked] = self.testimagearray[self.masked] ##Basically, when I insert my hand, it should be blue.
			self.maskedimage[self.masked] = self.testimagearray[self.masked] ##Basically, when I insert my hand, it should be blue.
			#self.maskedimage[self.invertedmask] = self.testimagearray[self.invertedmask] ##Basically, when I insert my hand, it should be blue.
			#self.maskedimage[self.masked] = 0
			#print("maskedimage")
			#print(type(self.maskedimage))
			
			#self.testimagearray = None ##I feel like saving RAM isn't helping at all.
			
			#self.thresholded[mask,:] = np.array([255, 0, 0])
			#samplearray = pygame.surfarray.array3d(self.sample)
			#self.transposed[maskback] = samplearray[maskback]
			#self.thresholded[-mask,:] = np.array([0, 0, 255])
			#self.transposed[-mask] = 255
			########################################################
			##DR: Actually, we might be able to use the 'Otsu filter' from scikit package, which should give us a background value
			##that we can use to generate a mask for the background.
			##from here, I'm hoping that we can replace the mask with an equivalent mask from a bitstream produced by the orbiter graphical engine?
			########################################################
			
			#self.thresholded = pygame.surfarray.make_surface(self.transposed)
			
			self.maskedimage2 = pygame.surfarray.make_surface(self.maskedimage)
			
			self.maskedimage = None ##Save RAM?
			
			#self.maskedimage2.set_alpha(255) ##Should get rid of transparency?
			
			#pygame.surfarray.blit_array(self.display, self.maskedimage) ##Should let us avoid producing surfaces?
			
			self.display.blit(self.maskedimage2, (0,0))
			
			#self.maskedimage = pygame.surfarray.make_surface(self.maskedimage) #convert numpy array to pygame surface for blitting.
			
			
			#print(type(self.thresholded))
			#self.display.blit(self.thresholded, (0, 0)) ##If the above 'if' statement fails then the camera's not ready for a new picture, so we display the old picture.
			#self.display.blit(self.maskedimage, (0, 0)) ##If the above 'if' statement fails then the camera's not ready for a new picture, so we display the old picture.
			#self.display.blit(self.finalimage, (0, 0)) ##If the above 'if' statement fails then the camera's not ready for a new picture, so we display the old picture.
			pygame.display.flip() #What actually gets the image to show.
		else:
			self.snapshot = self.cam.get_image(self.snapshot)
			self.display.blit(self.snapshot, (0, 0)) ##If the above 'if' statement fails then the camera's not ready for a new picture, so we display the old picture.
			pygame.display.flip() #What actually gets the image to show.

	def sample(self):
		self.sample = pygame.surface.Surface(self.size, 0, self.display) ##providing a surface to write images to; just so we don't have to store images.
		self.sample = self.cam.get_image()
		self.display.blit(self.sample, (0,0))
		pygame.display.flip() #Actually outputs the image.
		
	def calibrate(self):
		self.thresholded = pygame.surface.Surface(self.size, 0, self.display)
		self.background = pygame.surface.Surface(self.size, 0, self.display)
		bg = [] ##Going to be storing some images in memory buffa
		for i in range(0,10): ##More calibration photos taken, just to be super sure on this green thing.
			bg.append(self.cam.get_image(self.background))
		pygame.transform.average_surfaces(bg, self.background) #Grabbing the average colour?
		self.backcolour = pygame.transform.average_color(self.background) ##Should return the average colour of the background, which we'll use in order to mask it?
		#self.backcolour = pygame.Surface.map_rgb(self.backcolour)
		#self.backcolour = pygame.Surface.unmap_rgb(self.backcolour)
		print("displaying background image")
		self.display.blit(self.background, (0,0))
		pygame.display.flip #actually displaying it.
		pygame.transform.threshold(self.thresholded,self.snapshot,(255,0,0),(30,30,30),(0,0,0),1,self.background)

#displaytest.blit(img, (0,0))
#pygame.display.flip() ##DR: SO apparently, without this 'flip' the image won't appear in the window.

testcapt = Capture(cam)


import time

print("going to be taking the sample overlay image")

#time.sleep(5.9)

#testcapt.sample()

print("sample overlay taken")

print("Now going to be calibrating background")

#time.sleep(7.1)

testcapt.calibrate()

print("background calibrated")

import pgmagick

updatecounter = 2
for k in range(150):
	#testcapt.displayimg() #Should print an image to our display.
	#print("new img?")
	if (updatecounter == 2): #We've gone through at least 2 'k's
		print("UPDATE")
		testcapt.displayimg(update=True) ##We tell the 'displayimg' to grab another image from orbiter.
		updatecounter = 0 ##We want to wait for another 2 images.
	else:
		testcapt.displayimg()
		updatecounter = updatecounter + 1
	

backcolour = testcapt.backcolour

print(backcolour)

#snapshot = img #Storing img?

#import pygame.image
