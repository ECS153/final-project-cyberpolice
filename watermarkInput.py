from tkinter import *
from PIL import Image, ImageTk
from watermark import convertCoordinates

xcoord = 0
ycoord = 0

#function to be called when button is clicked
def setupCoordinates():
    print(xcoord, ycoord)
    convertCoordinates(xcoord, ycoord, "Images/Picture.png")

#function to be called when mouse is clicked
def getCoords(event):
    print ("(%d, %d)" % (canvas.canvasx(event.x), canvas.canvasy(event.y)))
    global xcoord 
    xcoord = canvas.canvasx(event.x)
    global ycoord 
    ycoord = canvas.canvasy(event.y)

if __name__ == "__main__":
    root = Tk()
    #setting up a tkinter canvas with scrollbars
    frame = Frame(root)
    # create frame to hold other widgets
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    # create scrollbar and button
    xscroll = Scrollbar(frame, orient=HORIZONTAL)
    xscroll.grid(row=1, column=0, sticky=E+W)
    yscroll = Scrollbar(frame)
    yscroll.grid(row=0, column=1, sticky=N+S)
    b = Button(frame, text="Confirm")
    b.grid(row=2, column=0)
    # canvas to display image with scrollbar starting at topleft of image
    canvas = Canvas(frame, bd=0, xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
    canvas.grid(row=0, column=0, sticky=N+S+E+W)
    xscroll.config(command=canvas.xview)
    yscroll.config(command=canvas.yview)

    b.config(command=setupCoordinates)
    frame.pack(fill=BOTH,expand=True)

    #adding the image
    img = ImageTk.PhotoImage(Image.open("Images/Picture.png"))
    canvas.create_image(0,0,image=img,anchor="nw")
    canvas.config(scrollregion=canvas.bbox(ALL))

    #mouseclick event
    canvas.bind("<ButtonPress-1>",getCoords)

    # blocks executation from finishing so picture displays
    root.mainloop()