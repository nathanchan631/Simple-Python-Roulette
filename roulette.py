"""
Nathan Chan
nathanchan631@gmail.com
Python Roulette with Tkinter
"""
import tkinter as tk
from dataclasses import dataclass
from random import random

from PIL import Image, ImageTk, ImageEnhance
from numpy import linspace

# Arc measure of each section of the wheel in degrees
SECTOR_LENGTH = 360 / 37

# Starts at 32 and moves counter-clockwise (does not include 0)
WHEEL_CONTENTS = [
    26, 3, 35, 12, 28, 7, 29, 18, 22, 9, 31, 14, 20, 1, 33, 16, 24, 5,
    10, 23, 8, 30, 11, 36, 13, 27, 6, 34, 17, 25, 2, 21, 4, 19, 15, 32
]

# Non-single-number bets and their winning numbers
BET_TYPES = [
    range(1, 35, 3),  # Column 1
    range(2, 36, 3),  # Column 2
    range(3, 37, 3),  # Column 3
    range(1, 13),  # Dozen 1
    range(13, 25),  # Dozen 2
    range(25, 37),  # Dozen 3
    range(2, 37, 2),  # Even
    WHEEL_CONTENTS[1::2],  # Red
    WHEEL_CONTENTS[::2],  # Black
    range(1, 36, 2),  # Odd
    range(1, 19),  # Low
    range(19, 37)  # High
]

# Bet zone instances data (format: img_name: [(x1, y1), (x2, y2), (x3, y3), ...]
BET_ZONES = {
    'zero': [(770, 88)],  # Bet on zero
    'num': [(710 + (i % 3 * 59), 137 + (i // 3 * 44)) for i in range(36)],  # Number bets
    'column': [(710 + (i * 59), 666) for i in range(3)],  # Column bets
    'dozen': [(654, 203 + (i * 176)) for i in range(3)],  # Dozen bets
    'bottom': [(604, 247 + (i * 88)) for i in range(4)],  # 1 to 1 bets
    'low': [(604, 159)],  # Bet on 1-18
    'high': [(604, 600)]  # Bet on 19-36
}

# Canvas img instances data (format: img_name: (x, y, opacity=1.0))
CANVAS_IMG = {
    'background': (485, 370), 'border': (490, 360), 'title_bar': (350, 55),
    'table': (720, 375), 'pocket': (290, 570), 'left_arrow': (195, 570),
    'right_arrow': (385, 570), 'textbox': (485, 370, 0.0), 'wheel_mask': (290, 290, 0.25)
}


class RouletteGUI:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(self.master, width=970, height=740)

        self.balance = 100.0
        self.init_balance = 100.0
        self.bets = []

        self.chips = [1, 5, 10, 25, 100]

        self.hovered_bet = None
        self.selected_bet = None

        self.wheel_angle = 0.0
        self.ball_angle = 0.0
        self.rotations = 0

        # Render the canvas and create canvas objects
        self.canvas.place(x=0, y=0)
        self.bet_zones = [BetZone(self.canvas, f'img/{key}_collider.png', *coords)
                          for key, coord_list in BET_ZONES.items() for coords in coord_list]
        self.canvas_img = {key: CanvasImg(self.canvas, f'img/{key}.png', *data)
                           for key, data in CANVAS_IMG.items()}
        self.chip_obj = CanvasImg(self.canvas, 'img/chip1.png', 290, 570)

        # Wheel objects
        self.wheel_img = Image.open('img/wheel.png')
        self.tk_wheel = ImageTk.PhotoImage(self.wheel_img)
        self.wheel_id = self.canvas.create_image(290, 290, image=self.tk_wheel)

        # Roulette Ball
        self.ball_img = Image.open('img/ball_wheel.png')
        self.tk_ball = ImageTk.PhotoImage(self.ball_img)
        self.ball_id = self.canvas.create_image(290, 290, image=self.tk_ball)

        # Submit bet button
        self.submit_button = tk.Button(self.master, text='Submit Bet', command=self.create_bet,
                                       font=('Myriad-Pro', 14), fg='white', bg='#0f662c',
                                       activeforeground='white', disabledforeground='white',
                                       activebackground='#0f662c', state='disabled')
        self.submit_button.place(x=220, y=645, width=140, height=35)

        # Text
        self.balance_text = self.canvas.create_text(315, 55, text='Balance: $100.00', fill='white',
                                                    font=('Myriad Pro', 13))
        self.winnings_text = self.canvas.create_text(530, 55, text='Round Winnings: None',
                                                     fill='white', font=('Myriad Pro', 13))

        # Events
        self.canvas.bind('<Motion>', lambda event: self.hover())
        self.canvas.tag_bind('bet_zone', '<Button-1>', lambda event: self.set_current_bet())
        self.canvas.tag_bind(self.canvas_img['left_arrow'].canvas_id, '<Button-1>',
                             lambda event: self.choose_chip('left'))
        self.canvas.tag_bind(self.canvas_img['right_arrow'].canvas_id, '<Button-1>',
                             lambda event: self.choose_chip('right'))
        self.canvas.tag_bind(self.canvas_img['wheel_mask'].canvas_id, '<Button-1>',
                             lambda event: self.spin() if self.bets and not self.rotations
                             else None)

        # Bring to front
        self.canvas.tag_raise('bet_zone')
        self.canvas.tag_raise(self.canvas_img['wheel_mask'].canvas_id)
        self.canvas.tag_raise(self.canvas_img['textbox'].canvas_id)

    def choose_chip(self, direction):
        """Set the selected chip when one of the arrows is clicked."""
        # Shift chips list
        if direction == 'left':
            self.chips.insert(0, self.chips.pop())
        else:
            self.chips.append(self.chips.pop(0))
        self.chip_obj.img = Image.open(f'img/chip{self.chips[0]}.png')

        # If a bet is selected and the player has sufficient money
        if self.chips[0] <= self.balance and self.selected_bet is not None:
            self.submit_button['state'] = 'normal'
            self.submit_button['background'] = '#1c9e48'
        else:
            self.submit_button['state'] = 'disabled'
            self.submit_button['background'] = '#0f662c'

    def hover(self):
        """Set the hovered bet when a bet zone is hovered on."""
        # Get hovered bet zone
        obj_id = self.canvas.find_withtag(tk.CURRENT)[0] - 1

        # Hover on a bet zone
        if 0 <= obj_id <= 48 and self.selected_bet is None and self.bet_zones[obj_id].chip is None:
            if self.hovered_bet is not None:
                self.bet_zones[self.hovered_bet].opacity = 0.0

            self.bet_zones[obj_id].opacity = 0.25
            self.hovered_bet = obj_id

        # Mouse outside of bet table image
        elif self.selected_bet is None and self.hovered_bet is not None:
            self.bet_zones[self.hovered_bet].opacity = 0.0

    def set_current_bet(self):
        """Set the current bet when a bet zone is clicked."""
        # Get clicked bet zone
        obj_id = self.canvas.find_withtag(tk.CURRENT)[0] - 1

        # Click on unoccupied bet zone
        if self.bet_zones[obj_id].chip is None:
            if self.selected_bet is not None:
                self.bet_zones[self.selected_bet].opacity = 0.0

                # Click on a zone that is already selected
                if self.selected_bet == obj_id:
                    self.selected_bet = None
                    self.submit_button['state'] = 'disabled'
                    self.submit_button['background'] = '#0f662c'
                    return

                self.bet_zones[obj_id].opacity = 0.25
                self.hovered_bet = obj_id

            self.selected_bet = self.hovered_bet

            # If the player has sufficient money
            if self.chips[0] <= self.balance:
                self.submit_button['state'] = 'normal'
                self.submit_button['background'] = '#1c9e48'

    def create_bet(self):
        """Create a bet object if the submit button is clicked."""
        # Create a chip object on the selected bet zone.
        bet_zone = self.bet_zones[self.selected_bet]
        bet_zone.draw_chip(self.chip_obj.img.filename)

        # Create a bet object and subtract from the player's balance.
        self.bets.append(Bet(self.chips[0], self.selected_bet))
        self.balance -= self.chips[0]

        self.submit_button['state'] = 'disabled'
        self.submit_button['background'] = '#0f662c'
        self.canvas.itemconfig(self.balance_text, text=f'Balance: ${self.balance:.2f}')

        self.canvas_img['wheel_mask'].opacity = 0.0
        self.canvas_img['textbox'].opacity = 1.0
        self.master.after(1000, self.canvas_img['textbox'].fade_out)

        bet_zone.opacity = 0.0
        self.hovered_bet = None
        self.selected_bet = None

    def spin(self):
        """Recursively spins the wheel and ball."""
        # Run this on the first time the method is called.
        if not self.rotations:
            self.wheel_angle = 360 * random()

        # Rotate the wheel and ball.
        if self.rotations < 322:
            self.ball_angle -= 4.5 - self.rotations / 80
        else:  # Calculate the angle between the ball and the middle of the slot
            self.ball_angle += SECTOR_LENGTH - (self.ball_angle - self.wheel_angle) % SECTOR_LENGTH
        self.wheel_angle += 5 - self.rotations / 100

        # Render the rotated images on the canvas
        self.tk_wheel = ImageTk.PhotoImage(self.wheel_img.rotate(self.wheel_angle))
        self.canvas.itemconfig(self.wheel_id, image=self.tk_wheel)

        self.tk_ball = ImageTk.PhotoImage(self.ball_img.rotate(self.ball_angle))
        self.canvas.itemconfig(self.ball_id, image=self.tk_ball)

        # Call the method again if it has run less than 500 times.
        if self.rotations < 500:
            self.rotations += 1
            self.master.after_idle(self.spin)
        else:
            self.wheel_angle %= 360
            self.ball_angle %= 360
            self.reset()

    def get_result(self):
        """Returns the spin result as an int."""

        # Calculate the ball's rotation relative to the wheel.
        self.ball_angle -= self.wheel_angle
        if self.ball_angle < 0:
            self.ball_angle += 360

        # Loop through each sector of the wheel (not 0) starting at 26 and moving counter-clockwise.
        # Return when the angle is between the lower and upper bounds of the current section.
        for index, angle in enumerate(linspace(SECTOR_LENGTH / 2, 360 - SECTOR_LENGTH * 3 / 2, 36)):
            if angle <= self.ball_angle < angle + SECTOR_LENGTH:
                return WHEEL_CONTENTS[index]
        return 0

    def reset(self):
        """Reset the board after a spin and get ready for the player to place bets."""
        # Set the player's money
        result = self.get_result()
        for bet in self.bets:
            if result in bet.win_num:
                self.balance += bet.win_amount

        self.canvas.itemconfig(self.balance_text, text=f'Balance: ${self.balance:.2f}')
        winnings = f'${self.balance - self.init_balance:.2f}'.replace('$-', '-$')
        self.canvas.itemconfig(self.winnings_text, text=f"Round Winnings: {winnings}")

        self.canvas_img['wheel_mask'].opacity = 0.25

        # Clear the bet table
        for bet_zone in self.bet_zones:
            if bet_zone.chip is not None:
                bet_zone.delete_chip()

        self.init_balance = self.balance
        self.rotations = 0
        self.bets.clear()


class CanvasImg:
    """
    Creates canvas images and stores its related objects and properties.

    Note:
        The image must be in a RGBA color format. If it is not, you can run PIL.Image.convert to
        convert it.

    Attributes:
        canvas (tkinter.Canvas) - the canvas the image should be rendered on
        img_file (str) - the path to the image file
        x (int) - the x coordinate of the image
        y (int) - the y coordinate of the image
        opacity (float) - the opacity of the image (default: 1.0)

        img (PIL.PngImagePlugin.PngImageFile) - corresponding PIL Image object
        tk_img (PIL.ImageTk.PhotoImage) - corresponding PIL ImageTk object
        canvas_id (int) - the id of the image on the canvas
    """

    def __init__(self, canvas, img_file, x, y, opacity=1.0):
        self.canvas = canvas
        self.x = x
        self.y = y

        self.tk_img = None
        self.canvas_id = None

        self._img = Image.open(img_file)
        self.opacity = opacity

    @property
    def img(self):
        """
        Returns a PIL.PngImagePlugin.PngImageFile.

        Gets or sets the PIL image. Invoking the setter will also update self.tk_img and redraw
        the image on the canvas.
        """
        return self._img

    @img.setter
    def img(self, value):
        self._img = value
        self.tk_img = ImageTk.PhotoImage(self._img)
        if self.canvas_id is None:
            self.canvas_id = self.canvas.create_image(self.x, self.y, image=self.tk_img)
        else:
            self.canvas.itemconfig(self.canvas_id, image=self.tk_img)

    @property
    def opacity(self):
        """
        Returns a float.

        Gets or sets the opacity of the PIL image. Invoking the setter will also invoke the object's
        img setter.
        """
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        # Open a copy of the image with opacity 1.0. Then split the image into individual RGBA
        # color channels and reduce the brightness of the alpha layer by a factor of value.
        assert self._img.mode == 'RGBA', 'Image must have a RGBA color format.'
        img = Image.open(self._img.filename)
        img.putalpha(ImageEnhance.Brightness(img.split()[3]).enhance(value))

        self._opacity = value
        self.img = img

    def fade_out(self):
        """Fade out the image on the canvas."""
        if self.opacity >= 0.02:
            self.opacity -= 0.02
            self.canvas.master.after(30, self.fade_out)


class BetZone(CanvasImg):
    """
    Creates a bet zone object. Inherits from the CanvasImg class.

    This class invokes the CanvasImg constructor during initialization.

    Note:
        The default opacity value for this class is 0.0 instead of the inherited default of 1.0.

    Additional Attributes:
        chip (CanvasImg) - A CanvasImg object that is placed on the bet zone
    """

    def __init__(self, canvas, img_file, x, y, opacity=0.0):
        super().__init__(canvas, img_file, x, y, opacity=opacity)
        self.canvas.itemconfig(self.canvas_id, tag='bet_zone')
        self.chip = None

    def draw_chip(self, chip_file):
        """Draws a chip on the bet zone."""
        self.chip = CanvasImg(self.canvas, chip_file, self.x, self.y)
        self.chip.img = self.chip.img.resize((40, 40), Image.ANTIALIAS)

    def delete_chip(self):
        """Removes the chip from the bet zone."""
        self.canvas.delete(self.chip.canvas_id)
        self.chip = None


@dataclass
class Bet:
    """
    An object that stores bet info.

    Attributes:
        bet_amount (float): the bet amount
        bet_id (int): the bet id used for lookup in the BET_TYPES list
    """

    bet_amount: float
    bet_id: int

    @property
    def win_num(self):
        """Returns a list of the winning numbers for the bet. Read only."""
        return [self.bet_id] if self.bet_id < 37 else list(BET_TYPES[self.bet_id - 37])

    @property
    def win_amount(self):
        """Returns the win amount for the bet as a float. Read only."""
        return 36 / len(self.win_num) * self.bet_amount


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Python Roulette')
    root.geometry('970x740')
    RouletteGUI(root)
    root.mainloop()
