"""
Nathan Chan
nathanchan631@gmail.com
Python Roulette with Tkinter
"""
import tkinter as tk
from random import random

from PIL import Image, ImageTk, ImageEnhance
from numpy import linspace

SECTOR_LENGTH = 360 / 37

CHIP_VALUES = [1, 5, 10, 25, 100]

WHEEL_CONTENTS = [
    32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
    5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26, 0
]

BET_TYPES = {
    37: [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
    38: [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
    39: [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
    40: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    41: [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
    42: [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
    43: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    44: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36],
    45: [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
    46: [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35],
    47: [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35],
    48: [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
}


class RouletteGUI:
    def __init__(self, master):
        self.master = master

        self.balance = 100
        self.init_balance = 100
        self.bets = []

        self.bet_zones = []
        self.hovered_bet = None
        self.selected_bet = None

        self.selected_chip = 0
        self.chip_files = [f'img/chip{value}.png' for value in CHIP_VALUES]

        self.wheel_angle = 0
        self.wheel_rotations = 0

        self.canvas = tk.Canvas(self.master, width=970, height=740)

        # Add self modifier to avoid garbage collection
        self.background_image = ImageTk.PhotoImage(file='img/background.jpg')
        self.border_image = ImageTk.PhotoImage(file='img/border.png')
        self.title_bar_image = ImageTk.PhotoImage(file='img/title_bar.png')
        self.arrow_image = ImageTk.PhotoImage(file='img/arrow.png')
        self.table_image = ImageTk.PhotoImage(file='img/table.png')
        self.pocket_image = ImageTk.PhotoImage(file='img/pocket.png')
        self.left_arrow_image = ImageTk.PhotoImage(file='img/left_arrow.png')
        self.right_arrow_image = ImageTk.PhotoImage(file='img/right_arrow.png')

        self.wheel_image = Image.open('img/wheel.png')
        self.tk_wheel_image = ImageTk.PhotoImage(self.wheel_image)

        # Font only works if Myriad Pro is downloaded!
        self.submit_button = tk.Button(self.master, text='Submit Bet', command=self.create_bet, font=('Myriad-Pro', 14),
                                       fg='white', activeforeground='white', disabledforeground='white', bg='#0f662c',
                                       activebackground='#0f662c', state='disabled')

        self.canvas.place(x=0, y=0)
        self.init_colliders()

        self.canvas.create_image(485, 370, image=self.background_image)
        self.canvas.create_image(490, 360, image=self.border_image)
        self.canvas.create_image(350, 55, image=self.title_bar_image)
        self.canvas.create_image(720, 375, image=self.table_image)
        self.canvas.create_image(290, 570, image=self.pocket_image)
        self.canvas.create_image(290, 90, image=self.arrow_image)

        self.wheel_obj = self.canvas.create_image(290, 295, image=self.tk_wheel_image)
        self.left_arrow_obj = self.canvas.create_image(195, 570, image=self.left_arrow_image)
        self.right_arrow_obj = self.canvas.create_image(385, 570, image=self.right_arrow_image)

        self.submit_button.place(x=220, y=645, width=140, height=35)
        self.balance_text = self.canvas.create_text(315, 55, text='Balance: $100.00', fill='white',
                                                    font=('Myriad-Pro', 13))
        self.winnings_text = self.canvas.create_text(530, 55, text='Round Winnings: None', fill='white',
                                                     font=('Myriad-Pro', 13))

        self.textbox = CanvasImg(self.canvas, 485, 370, 'img/textbox.png', opacity=0)
        self.chip_obj = CanvasImg(self.canvas, 290, 570, self.chip_files[0])
        self.arrow_mask = CanvasImg(self.canvas, 290, 90, 'img/arrow_mask.png', opacity=0.25)
        self.wheel_mask = CanvasImg(self.canvas, 290, 295, 'img/wheel_mask.png', opacity=0.25)

        self.canvas.bind('<Motion>', lambda event: self.hover())
        self.canvas.bind('<Button-1>', lambda event: self.set_current_bet())
        self.canvas.tag_bind(self.left_arrow_obj, '<Button-1>', lambda event: self.choose_chip('left'))
        self.canvas.tag_bind(self.right_arrow_obj, '<Button-1>', lambda event: self.choose_chip('right'))
        self.canvas.tag_bind(self.wheel_mask.canvas_obj, '<Button-1>', lambda event: self.spin() if self.bets and
                             not self.wheel_rotations else None)

        # Bring to front
        for bet_zone in self.bet_zones:
            self.canvas.tag_raise(bet_zone.canvas_obj)

    def init_colliders(self):
        self.bet_zones.append(BetZone(self.canvas, 770, 88, 'img/zero_collider.png'))
        for i in range(1, 37):
            self.bet_zones.append(BetZone(self.canvas, 710 + ((i - 1) % 3 * 59), 137 + ((i - 1) // 3 * 44),
                                          'img/num_collider.png'))
        for i in range(37, 40):
            self.bet_zones.append(BetZone(self.canvas, 710 + ((i - 1) % 3 * 59), 666,
                                          'img/num_collider.png'))
        for i in range(40, 43):
            self.bet_zones.append(BetZone(self.canvas, 654, 203 + ((i - 40) % 3 * 176),
                                          'img/dozen_collider.png'))
        self.bet_zones.append(BetZone(self.canvas, 604, 159, 'img/low_collider.png'))
        for i in range(44, 48):
            self.bet_zones.append(BetZone(self.canvas, 604, 159 + ((i - 43) * 88),
                                          'img/bottom_collider.png'))
        self.bet_zones.append(BetZone(self.canvas, 604, 600, 'img/high_collider.png'))

    def choose_chip(self, direction):
        if direction == 'left':
            self.selected_chip -= 1 if self.selected_chip > 0 else -4
        else:
            self.selected_chip += 1 if self.selected_chip < 4 else -4
        self.chip_obj.img = Image.open(self.chip_files[self.selected_chip])

        # If a bet is selected and the player has sufficient money
        if CHIP_VALUES[self.selected_chip] <= self.balance and self.selected_bet is not None:
            self.submit_button['state'] = 'normal'
            self.submit_button['background'] = '#1c9e48'
        else:
            self.submit_button['state'] = 'disabled'
            self.submit_button['background'] = '#0f662c'

    def hover(self):
        item_id = self.canvas.find_withtag(tk.CURRENT)[0] - 1

        # Hover on a bet zone
        if 0 <= item_id <= 48 and self.selected_bet is None and not self.bet_zones[item_id].occupied:
            if self.hovered_bet is not None:
                self.bet_zones[self.hovered_bet].opacity = 0

            self.bet_zones[item_id].opacity = 0.25
            self.hovered_bet = item_id

        # Mouse outside of bet table image
        elif self.selected_bet is None and self.hovered_bet is not None:
            self.bet_zones[self.hovered_bet].opacity = 0

    def set_current_bet(self):
        item_id = self.canvas.find_withtag(tk.CURRENT)[0] - 1

        # Click on unoccupied bet zone
        if 0 <= item_id <= 48 and not self.bet_zones[item_id].occupied:
            if self.selected_bet is not None:
                self.bet_zones[self.selected_bet].opacity = 0

                # Click on a zone that is already selected
                if self.selected_bet == item_id:
                    self.selected_bet = None
                    self.submit_button['state'] = 'disabled'
                    self.submit_button['background'] = '#0f662c'
                    return

                self.bet_zones[item_id].opacity = 0.25
                self.hovered_bet = item_id

            self.selected_bet = self.hovered_bet
            if CHIP_VALUES[self.selected_chip] <= self.balance:
                self.submit_button['state'] = 'normal'
                self.submit_button['background'] = '#1c9e48'

    def create_bet(self):
        bet_zone = self.bet_zones[self.selected_bet]
        bet_zone.draw_chip(self.chip_files[self.selected_chip])

        amount = CHIP_VALUES[self.selected_chip]
        self.balance -= amount
        self.bets.append(Bet(amount, self.selected_bet))

        self.submit_button['state'] = 'disabled'
        self.submit_button['background'] = '#0f662c'
        self.canvas.itemconfig(self.balance_text, text=f"Balance: ${'{:.2f}'.format(self.balance)}")

        self.arrow_mask.opacity = 0
        self.wheel_mask.opacity = 0
        self.textbox.opacity = 1
        self.master.after(1000, lambda: self.textbox.fade_out(self.master))

        bet_zone.opacity = 0
        bet_zone.occupied = True
        self.hovered_bet = None
        self.selected_bet = None

    def spin(self):
        if not self.wheel_rotations:
            self.wheel_angle = 360 * random()

        self.tk_wheel_image = ImageTk.PhotoImage(self.wheel_image.rotate(self.wheel_angle))
        self.canvas.itemconfig(self.wheel_obj, image=self.tk_wheel_image)

        self.wheel_angle += 10 - (self.wheel_rotations / 50)
        self.wheel_angle %= 360
        self.wheel_rotations += 1

        if self.wheel_rotations < 500:
            self.master.after(8, self.spin)
        else:
            result = self.get_result()
            for bet in self.bets:
                if result in bet.win_num:
                    self.balance += bet.win_amount
            self.reset()

    def get_result(self):
        # Loops through each section of the wheel, starting at 32 and going around clockwise
        for index, num in enumerate(linspace(SECTOR_LENGTH / 2, 360 + SECTOR_LENGTH / 2, 38)):
            if num <= self.wheel_angle < num + SECTOR_LENGTH:
                return WHEEL_CONTENTS[index]
        return ValueError('Wheel angle not between 0 and 360')

    def reset(self):
        self.canvas.itemconfig(self.balance_text, text=f"Balance: ${'{:.2f}'.format(self.balance)}")
        winnings = '${:.2f}'.format(self.balance - self.init_balance)  # Rounds to two decimal places
        self.canvas.itemconfig(self.winnings_text, text=f"Round Winnings: {winnings.replace('$-', '-$')}")

        self.arrow_mask.opacity = 0.25
        self.wheel_mask.opacity = 0.25

        for bet_zone in self.bet_zones:
            if bet_zone.occupied:
                bet_zone.delete_chip()

        self.init_balance = self.balance
        self.bets.clear()
        self.wheel_rotations = 0


class CanvasImg:
    def __init__(self, canvas, x, y, img_file, opacity=1.0):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.img_file = img_file

        self.img = Image.open(img_file)
        self.opacity = opacity

    @property
    def img(self):
        return self._img

    @property
    def opacity(self):
        return self._opacity

    @img.setter
    def img(self, value):
        self._img = value
        self.tk_img = ImageTk.PhotoImage(self.img)
        try:
            self.canvas.itemconfig(self.canvas_obj, image=self.tk_img)
        except AttributeError:  # Canvas object not yet defined
            self.canvas_obj = self.canvas.create_image(self.x, self.y, image=self.tk_img)

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        img = Image.open(self.img_file)
        img = img.copy() if img.mode == 'RGBA' else img.convert('RGBA')
        # Adjusts alpha channel of image by a factor of self.opacity
        img.putalpha(ImageEnhance.Brightness(img.split()[3]).enhance(self.opacity))
        self.img = img

    def fade_out(self, master):
        if self.opacity >= 0.02:
            self.opacity -= 0.02
            master.after(30, lambda: self.fade_out(master))


class BetZone(CanvasImg):
    def __init__(self, canvas, x, y, img_file, opacity=0.0):
        super().__init__(canvas, x, y, img_file, opacity=opacity)
        self.chip = None
        self.occupied = False

    def draw_chip(self, chip_file):
        self.chip = CanvasImg(self.canvas, self.x, self.y, chip_file)
        self.chip.img = self.chip.img.resize((40, 40), Image.ANTIALIAS)

    def delete_chip(self):
        self.canvas.delete(self.chip.canvas_obj)
        self.chip = None
        self.occupied = False


class Bet:
    def __init__(self, bet_amount, bet_type):
        self.bet_amount = bet_amount
        self.bet_type = bet_type
        self.win_num = BET_TYPES[self.bet_type] if self.bet_type > 36 else [self.bet_type]
        self.win_amount = 36 / len(self.win_num) * self.bet_amount


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Python Roulette')
    root.geometry('970x740')
    RouletteGUI(root)
    root.mainloop()
