from tkinter import Tk, Label, Button, ttk


class Master:
    def __init__(self, master):
        self.master = master
        master.title("A simple GUI")

        note1 = ttk.Notebook(master)
        note1.grid(column=0, row=0)

        note2 = ttk.Notebook(master)
        note2.grid(column=0, row=1)

        tab1 = ttk.Frame(note1, width=0, height=0)  # Create a tab for notebook 1
        tab2 = ttk.Frame(note2, width=0, height=0)  # Create a tab for notebook 2
        note1.add(tab1, text='Hata Tespit')  # Add tab notebook 1
        note2.add(tab2, text='Hata Inceleme')  # Add tab notebook 2

    def greet(self):
        print("Greetings!")


root = Tk()
my_gui = Master(root)
root.mainloop()
