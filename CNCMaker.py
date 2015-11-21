#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import Tkinter
#import pocket_V1
import subprocess



class simpleapp_tk(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.grid()

        self.entryVariable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self,textvariable=self.entryVariable)
        #self.entry.grid(column=0,row=0,sticky='EW')
        self.entry.bind("<Return>", self.OnPressEnter)
        self.entryVariable.set(u"")

        button1 = Tkinter.Button(self,text=u"pocket",
                                command=self.OnButton1Click)
        button1.grid(column=0,row=0)
        button1.config( height = 2, width = 10 )

        button2 = Tkinter.Button(self,text=u"engrave",
                                command=self.OnButton2Click)
        button2.grid(column=0,row=1)
        button2.config( height = 2, width = 10 )

        self.labelVariable = Tkinter.StringVar()
        label = Tkinter.Label(self,textvariable=self.labelVariable,
                              anchor="w",fg="white",bg="blue")
        label.grid(column=0,row=2,columnspan=2,sticky='EW')
        self.labelVariable.set(u"Choose an option")

        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,True)
        self.update()
        #self.geometry(self.geometry())       
        self.geometry('300x300')       
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    def OnButton1Click(self):
        self.labelVariable.set( self.entryVariable.get()+" pocket" )
        #execfile("pocket_V1.py")
	#pocket_V1.main() # do whatever is in test1.py
        subprocess.call("./pocket_V1.py", shell=True)
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    def OnButton2Click(self):
        self.labelVariable.set( self.entryVariable.get()+" engrave" )
        subprocess.call("./engrave-11.py", shell=True)
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    def OnPressEnter(self,event):
        self.labelVariable.set( self.entryVariable.get()+" (You pressed ENTER)" )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

if __name__ == "__main__":
    app = simpleapp_tk(None)
    app.title('CNCMaker')
    app.mainloop()
