#author: minesh
#for parsing pascal voc style xml annotation files saved by labelImg annotation tool
#date 5 feb 2017

import os,sys,glob
import  xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import re
listOfXmls=glob.glob(sys.argv[1]+'*.xml')
for annotationFile in listOfXmls:
	wordCount=0
	print annotationFile
	tree=ET.parse(annotationFile)
	root=tree.getroot()
	#print root.tag
	
	for child in root:
		if child.tag=="path":
			fullImagePath=child.text
			#fullImage=Image.open(fullImagePath)
			fullImageFileName=os.path.basename(fullImagePath)
			fullImage=Image.open(fullImageFileName)#assuming the code is run from the folder where images are
			fullImageName=os.path.splitext(fullImageFileName)[0]
			bBoxDrawnImageFileName=fullImageName+'_bboxes.jpg'
			outImg = Image.new("RGBA",fullImage.size)
			outImg.paste(fullImage)
			draw = ImageDraw.Draw(outImg)

		if child.tag=="object":
			wordCount=wordCount+1
			for objectChild in child.iter():
						
				if objectChild.tag=="bndbox":
					for bndBoxChild in objectChild.iter():
						if bndBoxChild.tag=="xmin":
							xmin=bndBoxChild.text
						if bndBoxChild.tag=="ymin":
                                                        ymin=bndBoxChild.text
						if bndBoxChild.tag=="xmax":
                                                        xmax=bndBoxChild.text
						if bndBoxChild.tag=="ymax":
                                                        ymax=bndBoxChild.text
					draw.rectangle((int(xmin),int(ymin),int(xmax),int(ymax)), outline="cyan")
					#croppedWord.save(croppedImageName)
	outImg.save(bBoxDrawnImageFileName)
		
		
	
	


    
    
