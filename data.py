"""Editable, simplified fantasy rosters; ratings and affiliations are game data.
Club field follows the 2026/27 league; Coventry is replaced by the user club.
These compact rosters are NOT a verified current transfer database.
Each club has two keepers, four defenders, three midfielders, three forwards.
"""
import random

# Club: strength, GK names | DEF names | MID names | FWD names.
RAW = {
 'Arsenal': (87, 'David Raya,Kepa Arrizabalaga|William Saliba,Gabriel Magalhaes,Ben White,Jurrien Timber|Declan Rice,Martin Odegaard,Martin Zubimendi|Bukayo Saka,Kai Havertz,Gabriel Martinelli'),
 'Aston Villa': (81, 'Emiliano Martinez,Marco Bizot|Ezri Konsa,Pau Torres,Matty Cash,Lucas Digne|John McGinn,Youri Tielemans,Boubacar Kamara|Ollie Watkins,Morgan Rogers,Emiliano Buendia'),
 'Bournemouth': (77, 'Djordje Petrovic,Fraser Forster|Marcos Senesi,James Hill,Adam Smith,Adrien Truffert|Lewis Cook,Tyler Adams,Alex Scott|Evanilson,Justin Kluivert,Antoine Semenyo'),
 'Brentford': (77, 'Caoimhin Kelleher,Hakon Valdimarsson|Nathan Collins,Sepp van den Berg,Kristoffer Ajer,Rico Henry|Mikkel Damsgaard,Mathias Jensen,Vitaly Janelt|Igor Thiago,Kevin Schade,Dango Ouattara'),
 'Brighton': (79, 'Bart Verbruggen,Jason Steele|Lewis Dunk,Jan Paul van Hecke,Ferdi Kadioglu,Olivier Boscagli|Carlos Baleba,Yasin Ayari,Diego Gomez|Kaoru Mitoma,Yankuba Minteh,Danny Welbeck'),
 'Chelsea': (84, 'Robert Sanchez,Filip Jorgensen|Reece James,Levi Colwill,Marc Cucurella,Wesley Fofana|Cole Palmer,Enzo Fernandez,Moises Caicedo|Pedro Neto,Liam Delap,Joao Pedro'),
 'Crystal Palace': (78, 'Dean Henderson,Walter Benitez|Chris Richards,Tyrick Mitchell,Daniel Munoz,Chadi Riad|Adam Wharton,Jefferson Lerma,Daichi Kamada|Jean Philippe Mateta,Ismaila Sarr,Eddie Nketiah'),
 'Everton': (76, 'Jordan Pickford,Mark Travers|James Tarkowski,Jarrad Branthwaite,Vitaliy Mykolenko,Jake OBrien|Idrissa Gueye,James Garner,Kiernan Dewsbury Hall|Iliman Ndiaye,Beto,Thierno Barry'),
 'Fulham': (77, 'Bernd Leno,Benjamin Lecomte|Joachim Andersen,Calvin Bassey,Antonee Robinson,Kenny Tete|Sander Berge,Alex Iwobi,Tom Cairney|Raul Jimenez,Harry Wilson,Samuel Chukwueze'),
 'Hull City': (71, 'Ivor Pandur,Dillon Phillips|Lewie Coyle,Alfie Jones,Charlie Hughes,Ryan Giles|Regan Slater,Matt Crooks,Joe Gelhardt|Mohamed Belloumi,Oli McBurnie,Liam Millar'),
 'Ipswich Town': (73, 'Alex Palmer,Christian Walton|Dara OShea,Jacob Greaves,Leif Davis,Axel Tuanzebe|Sam Morsy,Jack Taylor,Jens Cajuste|George Hirst,Jaden Philogene,Wes Burns'),
 'Leeds United': (75, 'Lucas Perri,Karl Darlow|Joe Rodon,Pascal Struijk,Jayden Bogle,Gabriel Gudmundsson|Ethan Ampadu,Ao Tanaka,Anton Stach|Joel Piroe,Daniel James,Wilfried Gnonto'),
 'Liverpool': (88, 'Alisson Becker,Giorgi Mamardashvili|Virgil van Dijk,Ibrahima Konate,Conor Bradley,Milos Kerkez|Alexis Mac Allister,Ryan Gravenberch,Dominik Szoboszlai|Mohamed Salah,Cody Gakpo,Hugo Ekitike'),
 'Manchester City': (87, 'Gianluigi Donnarumma,James Trafford|Ruben Dias,Josko Gvardiol,John Stones,Rico Lewis|Rodri,Phil Foden,Tijjani Reijnders|Erling Haaland,Jeremy Doku,Omar Marmoush'),
 'Manchester United': (80, 'Senne Lammens,Altay Bayindir|Matthijs de Ligt,Lisandro Martinez,Harry Maguire,Diogo Dalot|Bruno Fernandes,Kobbie Mainoo,Casemiro|Bryan Mbeumo,Matheus Cunha,Benjamin Sesko'),
 'Newcastle United': (82, 'Nick Pope,Aaron Ramsdale|Sven Botman,Fabian Schar,Dan Burn,Tino Livramento|Bruno Guimaraes,Sandro Tonali,Joelinton|Anthony Gordon,Harvey Barnes,Nick Woltemade'),
 'Nottingham Forest': (77, 'Matz Sels,Angus Gunn|Murillo,Nikola Milenkovic,Neco Williams,Ola Aina|Elliot Anderson,Morgan Gibbs White,Nicolas Dominguez|Chris Wood,Callum Hudson Odoi,Dan Ndoye'),
 'Sunderland': (74, 'Robin Roefs,Anthony Patterson|Dan Ballard,Luke ONien,Trai Hume,Dennis Cirkin|Granit Xhaka,Enzo Le Fee,Chris Rigg|Wilson Isidor,Eliezer Mayenda,Simon Adingra'),
 'Tottenham Hotspur': (81, 'Guglielmo Vicario,Antonin Kinsky|Cristian Romero,Micky van de Ven,Pedro Porro,Destiny Udogie|James Maddison,Dejan Kulusevski,Rodrigo Bentancur|Dominic Solanke,Richarlison,Mohammed Kudus'),
}
POSITIONS = {'GK': 1, 'DEF': 4, 'MID': 3, 'FWD': 3}
MINIMUM = {'GK': 2, 'DEF': 6, 'MID': 6, 'FWD': 4}

def make_players():
    rng = random.Random(9001)
    players = {}
    for club, (base, groups) in RAW.items():
        for pos, group in zip(POSITIONS, groups.split('|')):
            for name in group.split(','):
                pid = str(len(players))
                players[pid] = dict(id=pid, name=name, club=club, pos=pos,
                                    rating=max(60, min(95, base + rng.randint(-6, 5))))
    return players

PLAYERS = make_players()

# Broad position groups; the fifth midfielder in 3-4-1-2 is the attacking midfielder.
FORMATIONS = {
    '4-3-3': {'GK':1, 'DEF':4, 'MID':3, 'FWD':3},
    '4-4-2': {'GK':1, 'DEF':4, 'MID':4, 'FWD':2},
    '5-4-1': {'GK':1, 'DEF':5, 'MID':4, 'FWD':1},
    '3-4-1-2': {'GK':1, 'DEF':3, 'MID':5, 'FWD':2},
}
