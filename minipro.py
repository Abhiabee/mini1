import RPi.GPIO as GPIO
import time
from time import sleep
from picamera import PiCamera
import cv2
import numpy as np
import mapper
import os
from PIL import Image,ImageOps,ImageFilter
from PIL import ImageEnhance
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(40,GPIO.IN)

Motor1A = 24
Motor1B = 23
Motor1E = 25

count=0

def setup():
	GPIO.setmode(GPIO.BOARD)      # GPIO Numbering
	GPIO.setup(Motor1A,GPIO.OUT)  # All pins as Outputs
	GPIO.setup(Motor1B,GPIO.OUT)
	GPIO.setup(Motor1E,GPIO.OUT)

def loop():
	# Going forwards
	GPIO.output(Motor1A,GPIO.HIGH)
	GPIO.output(Motor1B,GPIO.LOW)
	GPIO.output(Motor1E,GPIO.HIGH)
 
	sleep(1000)
 
	# Stop
	#GPIO.output(Motor1E,GPIO.LOW)

def process():
    # path of the folder containing the raw images
    inPath = "/home/pi/minipro/black"
    # path of the folder that will contain the modified image
    outPath = "/home/pi/minipro/white"

    for imagePath in os.listdir(inPath):
        # imagePath contains name of the image
        inputPath = os.path.join(inPath, imagePath)
        image=cv2.imread(inputPath)
        image=cv2.resize(image,(1200,800))
        orig=image.copy()

        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        #cv2.imshow("Title",gray)

        blurred=cv2.GaussianBlur(gray,(5,5),0)
        #cv2.imshow("Blur",blurred)

        edged=cv2.Canny(blurred,30,50)
        #cv2.imshow("Canny",edged)


        contours,hierarchy=cv2.findContours(edged,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[-2:]
        contours=sorted(contours,key=cv2.contourArea,reverse=True)


        for c in contours:
           p=cv2.arcLength(c,True)
           approx=cv2.approxPolyDP(c,0.02*p,True)

           if len(approx)==4:
               target=approx
               break
        approx=mapper.mapp(target)

        pts=np.float32([[0,0],[800,0],[800,800],[0,800]])

        op=cv2.getPerspectiveTransform(approx,pts)
        dst=cv2.warpPerspective(orig,op,(800,800))
        gray_final = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
        image=Image.fromarray(gray_final)
        enh_bri = ImageEnhance.Brightness(image)
        brightness = 1.5
        image_brightened = enh_bri.enhance(brightness)
        enh_col = ImageEnhance.Color(image_brightened)
        color = 0.5
        image_colored = enh_col.enhance(color)
        enh_con = ImageEnhance.Contrast(image_colored)
        contrast = 3.0
        image_contrasted = enh_con.enhance(contrast)
        enh_sha = ImageEnhance.Sharpness(image_contrasted)
        sharpness = 3.0
        image_sharped = enh_sha.enhance(sharpness)
        #pil_image.show()


        #cv2.imshow("Scanned",dst)

        cv2.waitKey(0)
        cv2.destroyAllWindows()
        fullOutPath = os.path.join(outPath,'im_new_'+imagePath)
        #cv2.imwrite(fullOutPath,image_sharped)
        image_sharped.save(fullOutPath)

def document():
    pdf=FPDF()
    sdir=("/home/pi/ext/black/")
    width,height=0,0

    for i in range(1,count):
        fname=sdir+"imgage%.d.jpeg" % i
        if os.path.exists(fname):
            if i==1:
                page=Image.open(fname)
                width,height=page.size
                pdf=FPDF(unit='pt',format=[width,height])
            image=fname
	    pdf.add_page()
	    pdf.image(image,0,0,width,height)
	else:
            print("File not Founf:",fname)
        print("Processes %d" %i)
    pdf.output("Converted_Output.pdf","F")
    print("Successfull")


def mailer():
    email_user = 'bookletminiproject@gmail.com'
    email_password = 'bookletlifting'
    email_send = 'deekshadee18@gmail.com'

    subject = 'Internal Assessment Papers'
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject
    body = 'A sec papers'
    msg.attach(MIMEText(body,'plain'))

    filename='Converted_Output.pdf'
    attachment  =open(filename,'rb')

    part = MIMEBase('application','octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',"attachment; filename= "+filename)

    msg.attach(part)
    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(email_user,email_password)


    server.sendmail(email_user,email_send,text)
    server.quit()          
                
    

def mini():
    while(True):
        state=GPIO.input(40)
        if state==False:
            print("No booklet found")
            break
        else:
            count=count+1
            print("Booklet Detected")        
        
            # camera
            camera = PiCamera()
            camera.start_preview()
            sleep(5)
            camera.capture('/home/pi/minipro/black/image%.d.jpeg' %i) 
            camera.stop_preview()
            process()

            #sliding
            setup()
            loop()
            #lifting




       
document()
mailer()

        


        
