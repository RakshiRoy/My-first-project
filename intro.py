from tkinter import *
from PIL import Image, ImageTk, ImageSequence
import pygame

# Initialize the Pygame mixer
pygame.mixer.init()

# Load and play sound
def play_sound():
    global sound
    sound = pygame.mixer.Sound("soundfile.wav")  # Replace with your sound file
    sound.play()

# Function to play the GIF
def play_gif():
    img = Image.open("ironsnap2.gif")  # Replace with your GIF file
    lbl = Label(root)
    lbl.place(x=0, y=0)

    # Play sound
    play_sound()

    # Load all frames into memory
    frames = [frame.resize((1000, 500)) for frame in ImageSequence.Iterator(img)]

    # Animation function
    def update_frame(frame_index):
        try:
            frame = frames[frame_index]
            photo_image = ImageTk.PhotoImage(frame)
            lbl.config(image=photo_image)
            lbl.image = photo_image  # Keep a reference to avoid garbage collection
            root.update_idletasks()
            root.after(50, update_frame, (frame_index + 1) % len(frames))
        except:
            sound.stop()  # Stop the sound if the animation ends

    # Start animation
    update_frame(0)

# Create the main window
root = Tk()
root.geometry("1000x500")

# Call the function to play the GIF
play_gif()

# Start the Tkinter event loop
root.mainloop()
