import pyrealsense2 as rs
import tkinter as tk
import functools as ft
import numpy as np
from PIL import Image, ImageTk
import time
import copy
import argparse
from datetime import datetime

class Application(tk.Frame):
    def __init__(self, master=None,args=None):
        tk.Frame.__init__(self,master,padx=5,pady=5)
        self.camera_valid = False
        self.color_curr = None
        self.depth_curr = None
        self.cameraInit(args)
        self.item_list = ['None','Ball', 'Boat', 'Cup', 'Fork', 'Glove', 'Hat', 'Shoe', 'Spoon', 'Tayo', 'Teddy']

        cameraFuncWrapper = self.cameraDisconnect if self.camera_valid else ft.partial(self.cameraInit,args)
        self.connect_var = tk.StringVar(self,"Connected" if self.camera_valid else "Not Connected")
        self.connect_button = tk.Button(self,text="Disconnect" if self.camera_valid else "Connect",command=cameraFuncWrapper)
        self.connect_button.grid(row=0,column=0,sticky='ew')
        self.connect_label = tk.Label(self,textvariable=self.connect_var)
        self.connect_label.grid(row=0,column=1,sticky='ew')
        blackimg = ImageTk.PhotoImage(Image.fromarray(np.zeros((240,320),dtype=np.int32)))
        self.image_rgb = tk.Label(self,image=blackimg)
        self.image_rgb.image=blackimg
        self.image_rgb.grid(row=1,column=0,columnspan=1,sticky='ew')
        self.image_depth = tk.Label(self,image=blackimg)
        self.image_rgb.image=blackimg
        self.image_depth.grid(row=1,column=1,columnspan=1,sticky='ew')
        self.shot_button = tk.Button(self,text='촬영',command=self.shot)
        self.shot_button.grid(row=2,column=0,columnspan=2,sticky='ew')
        
        self.red_selected = self.createList(self, 'Red',self.item_list,2)
        self.green_selected = self.createList(self, 'Green',self.item_list,3)
        self.blue_selected = self.createList(self, 'Blue',self.item_list,4)

        self.update()

    def createList(self,root,name,item_list,columnidx):
        element = tk.LabelFrame(root,text=name)
        var = tk.IntVar(root, 0)
        for i,item in enumerate(item_list):
            self.item_f = tk.Frame(element)
            self.item_label = tk.Label(self.item_f,text=item,width=10)
            self.item_radio = tk.Radiobutton(self.item_f,variable=var, value=i)                
            self.item_radio.grid(row=0,column=0)
            self.item_label.grid(row=0,column=1)
            self.item_f.grid(row=i,column=0)
        element.grid(row=0,column=columnidx,rowspan=3,sticky='ns',padx=5)
        return var
        

    def update(self):
        camera_func_wrapper = self.cameraDisconnect if self.camera_valid else ft.partial(self.cameraInit,args)
        self.connect_var.set("Connected" if self.camera_valid else "Not Connected")
        self.connect_button.config(text="Disconnect" if self.camera_valid else "Connect",command=camera_func_wrapper)
        if self.camera_valid:
            self.getFrame()
            imgrgb = ImageTk.PhotoImage(self.color_curr.resize(size=(320,240)))
            self.image_rgb.config(image=imgrgb)
            self.image_rgb.image=imgrgb
            imgdepth = ImageTk.PhotoImage(self.depth_curr.resize(size=(320,240),resample=0))
            self.image_depth.config(image=imgdepth)
            self.image_depth.image=imgdepth
        self.after(1000//30, self.update)

    def cameraInit(self,args):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth,args.width,args.height,rs.format.z16,30)
        config.enable_stream(rs.stream.color,args.width,args.height,rs.format.bgr8,30)
        self.total_frames = args.total_frames
        try:
            self.profile = self.pipeline.start(config)
        except Exception as err:
            print(err)
            self.quit()
            return
        print("Connected")
        self.camera_valid = True

    def cameraDisconnect(self):
        self.pipeline.stop()
        print("Disconnected")
        self.camera_valid=False

    def getFrame(self):
        while True:
            frame = self.pipeline.wait_for_frames()
            color = frame.get_color_frame()
            depth = frame.get_depth_frame()
            if depth is None or color is None:
                continue
            depth_np = np.asanyarray(depth.as_frame().get_data())
            color_np = np.asanyarray(color.as_frame().get_data())
            break
        self.color_curr = Image.fromarray(color_np[:,:,::-1])
        self.depth_curr = Image.fromarray(depth_np)
        
    def shot(self):
        t = datetime.now()
        t_string = t.strftime("%Y%m%d_%H%M%S_")
        item_string = "{}_{}_{}_".format(self.item_list[self.red_selected.get()]
                                         , self.item_list[self.green_selected.get()]
                                         , self.item_list[self.blue_selected.get()])
        self.color_curr.save(t_string+item_string+'color.png')
        self.depth_curr.save(t_string+item_string+'depth.png')

    def shotbinder(self,event):
        self.shot()

    def record(self,duration=2): #Unused
        colors = []
        depths = []
        try:
            n_frames = 0
            i = 0
            while n_frames < self.total_frames:
                i+=1
                frame = self.pipeline.wait_for_frames()
                color = frame.get_color_frame()
                depth = frame.get_depth_frame()
                if depth is None or color is None or i % (30//args.FPS) !=0:
                    continue
                n_frames+=1
                depth_np = np.asanyarray(depth.as_frame().get_data())
                color_np = np.asanyarray(color.as_frame().get_data())
                depths.append(copy.copy(depth_np))
                colors.append(copy.copy(color_np))
        finally:
            for i in range(len(depths)):
                color_pil = Image.fromarray(colors[i][:,:,::-1])
                depth_pil = Image.fromarray(depths[i])
                color_pil.save('color{}.png'.format(i+1))
                depth_pil.save('depth{}.png'.format(i+1))



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-width', type=int, default=640, help='image size(width), (default: 640)')
    parser.add_argument('-height', type=int, default=480, help='image size(height), (default: 480)')
    parser.add_argument('-FPS', type=int, default=30, help='FPS of dataset, it should be a divisor of 30 , (default: 1)')
    parser.add_argument('-total_frames', type=int, default=20, help='number of frames(images), (default: 30)')
    args = parser.parse_args()
    root = tk.Tk()
    root.resizable(0,0)
    root.title("Test")
    app = Application(root,args)
    app.pack()
    root.bind("<space>",app.shotbinder)
    root.mainloop()
