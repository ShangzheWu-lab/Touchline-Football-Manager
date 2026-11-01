# Touchline: Road to Glory

An offline Python desktop football management game built for the COMP9001 Python Project Challenge.

Create a club, build a 22-player squad through an eleven-round draft, choose your starting eleven, and compete in a 19-match fantasy Premier League season. The game includes an English/Chinese interface, real club crests and player portraits, fitness and injuries, training choices, match commentary, and JSON saves.

## Requirements

- Python **3.10 or newer** with **Tkinter** and a graphical desktop.
- No third-party Python packages, API keys, or internet connection are needed to play.
- Keep the complete `assets/` directory beside `main.py`.

**For the marker:** this is a Tkinter GUI application. Run it locally; Ed's terminal-only environment cannot display the game window. The entry point is **`main.py`**.

## Download and run

Download the repository using **Code → Download ZIP**, extract the entire archive, and open a terminal in the extracted folder containing `main.py`.

### macOS

Check that your selected Python interpreter can open Tkinter:

```bash
python3 -m tkinter
```

Close the test window, then start the game:

```bash
python3 main.py
```

If you use an activated Conda environment, use its interpreter consistently:

```bash
python -m tkinter
python main.py
```

If `/usr/bin/python3` aborts with a macOS/Tk compatibility error, use a working Conda Python or a Python installation from [python.org](https://www.python.org/downloads/macos/). You can also open `main.py` in that installation's IDLE and select **Run → Run Module**.

### Windows

Double-click `Start_Windows.bat`, or run:

```powershell
py -3 main.py
```

### Linux

Use a Python installation with Tkinter and an active desktop session:

```bash
python3 main.py
```

Some distributions package Tkinter separately as `python3-tk`.

The recommended window size is 1400 × 900. The minimum is 1180 × 780; lists and the pitch can scroll.

## How to play

1. **Create a club.** Enter a new club name to replace Coventry City in the fantasy league.
2. **Draft your squad.** Eleven different clubs are drawn at random. Select two players from each. Keep at least 2 goalkeepers, 6 defenders, 6 midfielders and 4 forwards; the remaining four slots are free choices.
3. **Choose your formation.** Open **Squad & tactics**, select a formation, and choose eleven starters. **Auto select** prepares a lineup; **Apply XI** commits it.
4. **Prepare for the match.** In **Overview**, choose training and a match approach. Review fitness, injuries, the opponent, the venue and the simulated weather.
5. **Play the match.** Watch the commentary or skip to full time. Check the updated league table, medical report and club news.
6. **Rotate and save.** Replace unavailable or tired starters. Use **Save game** to write a JSON save, and **Load game** to resume it.

Switch between **English** and **Simplified Chinese** using the selector at the bottom left. Player names remain in Latin script. Language switching preserves pending draft and lineup selections.

## Formations and lineup selection

| Formation | Goalkeepers | Defenders | Midfielders | Forwards |
|---|---:|---:|---:|---:|
| 4-3-3 | 1 | 4 | 3 | 3 |
| 4-4-2 | 1 | 4 | 4 | 2 |
| 5-4-1 | 1 | 5 | 4 | 1 |
| 3-4-1-2 | 1 | 3 | 5 | 2 |

In 3-4-1-2, the fifth selected midfielder appears behind the forwards. Positions are broad gameplay categories; there is no separate attacking-midfielder attribute.

Deselect a starter before selecting a replacement. Injured players cannot start. Changing the dropdown or clicking **Auto select** does not commit the lineup: click **Apply XI**. Leaving the page without applying discards pending changes; saving stores the committed lineup.

## Fitness, injuries and training

Starter fitness falls by 9–15 after each match, with a floor of 55. Rested players recover 22, capped at 100. Effective player rating is:

```text
rating × (0.65 + 0.35 × fitness / 100)
```

Injuries are diagnosed after a match and cause a player to miss the next **1–3 fixtures**. A player with one match remaining must sit out the next match before returning. Low fitness and rain increase risk. Automatic selection excludes injured players. Positional safeguards keep the small squad playable.

Choose one training preparation before each match. It applies **once at kick-off** and resets to balanced training afterward. Repeatedly changing the selection does not grant extra fitness.

| Preparation | Effect |
|---|---|
| Balanced | No extra adjustment. |
| Recovery | All players gain 8 fitness, capped at 100; injury probability is multiplied by 0.55. Existing injuries still require recovery matches. |
| Attack | Your expected goals increase by 0.25; your opponent's increase by 0.10. |
| Defence | Your opponent's expected goals decrease by 0.25; yours decrease by 0.10. |

Match approach is a separate choice: **Attacking** increases both teams' chances, **Defensive** reduces both, and **Balanced** makes no adjustment.

## Season and match simulation

- Twenty clubs play a single round robin: 19 matchweeks, with ten matches each week.
- A win earns three points, a draw one, and a loss zero.
- Rankings use points, goal difference, goals scored, then club name as a simplified final tiebreaker.
- The season ends after 19 rounds. First place wins the title; the top four and survival are achievements; the bottom three are relegated. There is no second season or separate European tournament.
- Board objectives track **25 points, 30 goals and five clean sheets**. These are milestones, not hidden rating bonuses.
- Ratings, fitness, home advantage, preparation, tactics and weather influence a Poisson score simulation.
- Saved shots, wide shots and corners illustrate the simulated match. The replay reveals events over time; it is not a real-time football engine.

Opponent venues use real stadium names. Your new club uses a fictional venue named after the club. Weather, temperature and kick-off time are **generated game conditions**, not live forecasts. Rain and wind reduce both sides' scoring chances; rain also slightly increases injury risk. Conditions stay fixed when you revisit a fixture.

Club news is generated from your saved results, injuries, recoveries, form, scorers and objective progress. It is **fictional in-game news**, not real-world reporting, and uses no language model or external service.

## Saves and settings

Saves are manual. Use **Save game** before closing. Saves include the squad, lineup, formation, fitness, injuries, training choice, season progress and random-generator state.

The current program writes save schema version 2 and can load earlier version 1 saves. Old saves default to balanced preparation and no injuries. A newly injured player may remain in a saved lineup, but must be replaced before the next match.

The language preference is stored in `~/.touchline_settings.json` when that location is writable. Invalid or damaged save files are rejected without replacing the current game.

## Repository contents

| File or directory | Purpose |
|---|---|
| `main.py` | Main entry point and Tkinter interface. |
| `main.pyw` | Alternate Windows GUI entry point. |
| `game.py` | Drafting, lineups, scheduling, matches and save validation. |
| `data.py` | Fantasy roster, ratings and formation definitions. |
| `season.py` | Injuries, preparation, weather, news and objectives. |
| `ui_season.py` | Dashboard, medical and season information panels. |
| `badges.py` | Local crest and portrait loading. |
| `assets/` | Required bundled images. |
| `Start_Windows.bat` | Windows launcher. |
| `ASSET_SOURCES.json` | Image identities and source attribution. |

Presentation drafts, example saves, test scripts, caches and development/download utilities are excluded from this runtime-focused repository.

## Data and media attribution

The compact **228-player roster and ability ratings are simplified fantasy data**, not a verified live transfer database. Players selected in the draft are fantasy copies; opponents retain fixed team ratings. Some photographs show a player's previous club kit.

The package includes 19 real club crests and 228 player photographs. The custom club uses an original shield. Images come from ESPN and Premier League public media. `ASSET_SOURCES.json` records the individual source URLs and identity mappings. Archived FPL identifiers were obtained from the [Fantasy-Premier-League data project](https://github.com/vaastav/Fantasy-Premier-League). Venue names were checked against the [Premier League stadium guide](https://www.premierleague.com/en/news/4725666).

Club marks and photographs belong to their respective rights holders. This student project does not claim ownership of these assets or affiliation with the clubs, ESPN or the Premier League. No blanket redistribution licence is asserted for third-party media.

## Implementation and validation

The main program is written in Python and uses standard-library modules, including Tkinter, JSON, random, math and pathlib. It demonstrates file I/O, error handling, classes, functions, dictionaries, lists, event callbacks and state validation.

Before preparing this distribution, 16 logic tests passed, including schedule checks, full-season simulation, lineup validation, save/resume compatibility, training behaviour and injury recovery. Test and development files are retained outside this runtime distribution. Desktop rendering and native macOS interactions still require a local smoke test.

AI assistance was used during development and documentation. The student should review and understand the implementation and follow the course's disclosure requirements.
