"""Bundled real club crests and player portraits; custom-club shield is original."""
from pathlib import Path
import tkinter as tk

CLUBS = {
    'Arsenal': ('ARS','#db2638','#ffffff'),
    'Aston Villa': ('AVL','#802c48','#8bd0ed'),
    'Bournemouth': ('BOU','#d52b38','#161d2c'),
    'Brentford': ('BRE','#eb3344','#ffffff'),
    'Brighton': ('BHA','#2372c8','#ffffff'),
    'Chelsea': ('CHE','#225ac3','#ffffff'),
    'Crystal Palace': ('CRY','#2354b3','#e73950'),
    'Everton': ('EVE','#254cb1','#ffffff'),
    'Fulham': ('FUL','#f2f4f8','#242b38'),
    'Hull City': ('HUL','#efaa32','#242b38'),
    'Ipswich Town': ('IPS','#286ac4','#ffffff'),
    'Leeds United': ('LEE','#f7f8fa','#e8c342'),
    'Liverpool': ('LIV','#cc283e','#ffffff'),
    'Manchester City': ('MCI','#74b9de','#ffffff'),
    'Manchester United': ('MUN','#d92d36','#f1c95d'),
    'Newcastle United': ('NEW','#232d39','#f4f6fc'),
    'Nottingham Forest': ('NFO','#d93243','#ffffff'),
    'Sunderland': ('SUN','#e13b4a','#ffffff'),
    'Tottenham Hotspur': ('TOT','#eff3fa','#233052'),
}

class BadgeBook:
    """Keep PhotoImage references alive across pages; no network or Pillow needed."""
    def __init__(self,master):
        self.master=master; self.cache={}; self.pairs={}; self.portraits={}
        self.root=Path(__file__).resolve().parent/'assets'
    def get(self,club,size=32):
        code=CLUBS.get(club,('YOU',))[0]; key=(code,size)
        if key not in self.cache:
            path=Path(__file__).resolve().parent/'assets'/f'{code}_{size}.png'
            self.cache[key]=tk.PhotoImage(master=self.master,file=str(path))
        return self.cache[key]
    def pair(self,home,away):
        key=(home,away)
        if key not in self.pairs:
            image=tk.PhotoImage(master=self.master,width=68,height=28)
            for club,x in [(home,0),(away,38)]:
                image.tk.call(str(image),'copy',str(self.get(club,28)),'-to',x,0)
            self.pairs[key]=image
        return self.pairs[key]

    def has_portrait(self,pid):
        return (self.root/'players'/f'{pid}_96.png').exists()
    def portrait(self,pid,size=40):
        key=(pid,size)
        if key not in self.portraits:
            path=self.root/'players'/f'{pid}_{size}.png'
            if not path.exists():path=self.root/'players'/f'unknown_{size}.png'
            self.portraits[key]=tk.PhotoImage(master=self.master,file=str(path))
        return self.portraits[key]
