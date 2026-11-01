"""Game rules independent of Tkinter. File I/O and defensive error handling."""
import json
import math
import random
from collections import Counter
from pathlib import Path
from data import RAW, PLAYERS, POSITIONS, MINIMUM, FORMATIONS
from season import SeasonFeatures, PREPARATIONS, WEATHER, INJURIES


def fixtures(teams):
    """Circle algorithm: every pair meets once; each club plays every round."""
    ring = list(teams)
    rounds = []
    for week in range(len(ring) - 1):
        pairs = []
        for i in range(len(ring) // 2):
            a, b = ring[i], ring[-1-i]
            pairs.append([a, b] if (week+i) % 2 else [b, a])
        rounds.append(pairs)
        ring = [ring[0], ring[-1]] + ring[1:-1]
    return rounds


def poisson(mean, rng):
    product, count = 1.0, 0
    while product > math.exp(-mean):
        product *= rng.random()
        count += 1
    return count - 1


class Game(SeasonFeatures):
    def __init__(self, name, seed=None):
        name = name.strip()
        if not name or len(name) > 26 or any(ord(c) < 32 for c in name):
            raise ValueError('Use a club name of 1–26 printable characters.')
        if name.casefold() in {x.casefold() for x in RAW}:
            raise ValueError('Choose a new club name, not an existing club.')
        self.rng = random.Random(seed)
        self.name = name
        # Distinct clubs ensure later rounds always have all four positions.
        self.draft_clubs = self.rng.sample(list(RAW), 11)
        self.squad = []
        self.lineup = []
        self.formation = '4-3-3'
        self.fitness = {}
        self.week = 0
        self.schedule = fixtures([name] + list(RAW))
        self.table = {t: dict(P=0,W=0,D=0,L=0,GF=0,GA=0,Pts=0) for t in [name]+list(RAW)}
        self.history = []
        self.scorers = {}
        self.injuries = {}
        self.preparation = 'Balanced'

    @property
    def drafting(self):
        return len(self.squad) < 22

    def candidates(self):
        if not self.drafting:
            return []
        club = self.draft_clubs[len(self.squad)//2]
        return [p for p in PLAYERS.values() if p['club']==club and p['id'] not in self.squad]

    def draft(self, ids):
        available = {p['id'] for p in self.candidates()}
        if len(ids)!=2 or len(set(ids))!=2 or not set(ids)<=available:
            raise ValueError('Select exactly two different players from this club.')
        counts = Counter(PLAYERS[i]['pos'] for i in self.squad+list(ids))
        missing = sum(max(0, n-counts[p]) for p,n in MINIMUM.items())
        if missing > 22-len(self.squad)-2:
            raise ValueError('Keep room for 2 GK, 6 DEF, 6 MID and 4 FWD. Pick a needed position.')
        self.squad.extend(ids)
        self.fitness.update({i:100 for i in ids})
        if not self.drafting:
            self.auto_lineup()

    def effective(self, pid):
        return PLAYERS[pid]['rating'] * (0.65 + 0.35*self.fitness[pid]/100)

    def auto_lineup(self, formation=None):
        self.set_lineup(self.suggested_lineup(formation),formation)

    def set_lineup(self, ids, formation=None):
        formation = formation or self.formation
        if formation not in FORMATIONS:
            raise ValueError("Unknown formation.")
        if len(ids)!=11 or len(set(ids))!=11 or not set(ids)<=set(self.squad):
            raise ValueError('Select 11 different players from your squad.')
        if Counter(PLAYERS[p]['pos'] for p in ids) != Counter(FORMATIONS[formation]):
            required = FORMATIONS[formation]
            raise ValueError(f"{formation} requires {required['GK']} GK, {required['DEF']} DEF, {required['MID']} MID and {required['FWD']} FWD.")
        if any(not self.available(p) for p in ids):
            raise ValueError("Injured players cannot start. Replace them or use Auto select.")
        self.lineup = list(ids)
        self.formation = formation

    def strength(self, team):
        return sum(self.effective(p) for p in self.lineup)/11 if team==self.name else RAW[team][0]

    def standings(self):
        return sorted(self.table, key=lambda t:(-self.table[t]['Pts'],
                      -(self.table[t]['GF']-self.table[t]['GA']),-self.table[t]['GF'],t))

    def play(self, tactic='Balanced'):
        if self.drafting or self.week >= 19:
            raise ValueError('Finish the draft first, or start a new season after week 19.')
        self.set_lineup(self.lineup)
        if tactic not in ('Attacking','Balanced','Defensive'):
            raise ValueError('Unknown tactic.')
        context=self.context()
        preparation=self.preparation
        if preparation=='Recovery':
            self.fitness={pid:min(100,fit+8) for pid,fit in self.fitness.items()}
        starting_fitness=dict(self.fitness)
        results, events, own_result = [], [], None
        own_means=None; strengths=None
        for home, away in self.schedule[self.week]:
            delta = (self.strength(home)-self.strength(away))/18
            hmean, amean = 1.45+delta, 1.20-delta
            if self.name in (home,away):
                adjustment = {'Attacking':0.4,'Balanced':0,'Defensive':-0.35}[tactic]
                hmean += adjustment
                amean += adjustment
                if preparation=='Attack':
                    if home==self.name:hmean+=0.25;amean+=0.10
                    else:amean+=0.25;hmean+=0.10
                elif preparation=='Defence':
                    if home==self.name:amean-=0.25;hmean-=0.10
                    else:hmean-=0.25;amean-=0.10
                factor={'Clear':1.0,'Cloudy':1.0,'Rain':0.90,'Wind':0.85}[context['weather']]
                hmean*=factor;amean*=factor
                own_means=[round(max(0.15,min(3.8,v)),2) for v in (hmean,amean)]
                strengths=[self.strength(home),self.strength(away)]
            hg = poisson(max(0.15,min(3.8,hmean)),self.rng)
            ag = poisson(max(0.15,min(3.8,amean)),self.rng)
            results.append([home,away,hg,ag])
            for team, gf, ga in ((home,hg,ag),(away,ag,hg)):
                row = self.table[team]
                row['P']+=1; row['GF']+=gf; row['GA']+=ga
                outcome = 'W' if gf>ga else 'D' if gf==ga else 'L'
                row[outcome]+=1; row['Pts'] += {'W':3,'D':1,'L':0}[outcome]
            if self.name in (home,away):
                own_result = [home,away,hg,ag]
                for team, goals in ((home,hg),(away,ag)):
                    for _ in range(goals):
                        scorer = ''
                        if team==self.name:
                            pid = self.rng.choices(self.lineup, weights=[{'GK':0,'DEF':1,'MID':3,'FWD':6}[PLAYERS[p]['pos']] for p in self.lineup])[0]
                            scorer = PLAYERS[pid]['name']
                            self.scorers[pid] = self.scorers.get(pid,0)+1
                        events.append([self.rng.randint(1,90),team,scorer])
        events.sort(key=lambda x:x[0])
        for pid in self.squad:
            self.fitness[pid] = max(55,self.fitness[pid]-self.rng.randint(9,15)) if pid in self.lineup else min(100,self.fitness[pid]+22)
        new_injuries,returned=self.resolve_medical(starting_fitness,preparation,context['weather'])
        # Non-goal incidents illustrate the completed simulation; never alter its score.
        commentary=[{'minute':m,'team':t,'kind':'goal','scorer':p} for m,t,p in events]
        for team,mean in zip(own_result[:2],own_means):
            for _ in range(self.rng.randint(4,8)+int(mean*2)):
                commentary.append({'minute':self.rng.randint(1,90),'team':team,
                                   'kind':self.rng.choice(['save','wide','corner']),'scorer':''})
        commentary.sort(key=lambda e:e['minute'])
        self.week += 1
        report = dict(week=self.week,results=results,match=own_result,events=events,tactic=tactic,
                      context=context,preparation=preparation,xg=own_means,strengths=strengths,
                      injuries=new_injuries,returned=returned,commentary=commentary)
        self.preparation='Balanced' 
        self.history.append(report)
        return report

    def save(self, path):
        """Atomic JSON write; never unpickle user-provided files."""
        data = {k:v for k,v in vars(self).items() if k!='rng'}
        data['version'] = 2
        data['random_state'] = self.rng.getstate()
        path = Path(path)
        temporary = path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        temporary.replace(path)

    @classmethod
    def load(cls, path):
        """Validate saved state before replacing the live game."""
        try:
            if Path(path).stat().st_size > 2_000_000:
                raise ValueError('Save is too large.')
            d = json.loads(Path(path).read_text(encoding='utf-8'))
            if d['version'] not in (1,2):
                raise ValueError('Unsupported save version.')
            g = cls(d['name'])
            squad = d['squad']
            assert isinstance(squad,list) and len(squad)%2==0 and len(squad)<=22
            assert len(set(squad))==len(squad) and set(squad)<=set(PLAYERS)
            assert len(d['draft_clubs'])==11 and len(set(d['draft_clubs']))==11
            assert set(d['draft_clubs'])<=set(RAW)
            # Replay the draft to enforce club provenance and positional guarantees.
            g.draft_clubs = d['draft_clubs']
            for i in range(0,len(squad),2):
                g.draft(squad[i:i+2])
            assert type(d['week']) is int and 0<=d['week']<=19
            assert not g.drafting or d['week']==0
            assert d['schedule']==g.schedule
            assert set(d['fitness'])==set(squad)
            assert all(type(v) is int and 55<=v<=100 for v in d['fitness'].values())
            assert set(d['table'])==set(g.table)
            for row in d['table'].values():
                assert set(row)=={'P','W','D','L','GF','GA','Pts'}
                assert all(type(v) is int and v>=0 for v in row.values())
                assert row['P']==d['week']==row['W']+row['D']+row['L']
                assert row['Pts']==3*row['W']+row['D']
            assert isinstance(d['history'],list) and len(d['history'])==d['week']
            rebuilt = {t:dict(P=0,W=0,D=0,L=0,GF=0,GA=0,Pts=0) for t in g.table}
            for week, report in enumerate(d['history']):
                assert report['week']==week+1 and report['tactic'] in ('Attacking','Balanced','Defensive')
                assert len(report['results'])==10
                own = None
                for pair,result in zip(g.schedule[week],report['results']):
                    a,b,x,y = result
                    assert [a,b]==pair and type(x) is int and type(y) is int and 0<=x<=100 and 0<=y<=100
                    if g.name in (a,b): own=result
                    for t,gf,ga in ((a,x,y),(b,y,x)):
                        r=rebuilt[t]; r['P']+=1; r['GF']+=gf; r['GA']+=ga
                        o='W' if gf>ga else 'D' if gf==ga else 'L'
                        r[o]+=1; r['Pts']+={'W':3,'D':1,'L':0}[o]
                assert report['match']==own
                a,b,x,y=own
                assert len(report['events'])==x+y
                assert Counter(e[1] for e in report['events'])==Counter({a:x,b:y})
                assert all(len(e)==3 and type(e[0]) is int and 1<=e[0]<=90 and isinstance(e[2],str) for e in report['events'])
                if 'context' in report:
                    assert report['context']==g.context(week)
                    assert report['preparation'] in PREPARATIONS
                    assert len(report['xg'])==2 and all(type(v) in (int,float) and 0.15<=v<=3.8 for v in report['xg'])
                    assert len(report['strengths'])==2 and all(type(v) in (int,float) and 0<=v<=100 for v in report['strengths'])
                    assert isinstance(report['commentary'],list) and len(report['commentary'])<=250
                    assert all(type(e['minute']) is int and 1<=e['minute']<=90 and e['team'] in (a,b) and e['kind'] in ('goal','save','wide','corner') and isinstance(e['scorer'],str) for e in report['commentary'])
                    assert sorted((e['minute'],e['team'],e['scorer']) for e in report['commentary'] if e['kind']=='goal')==sorted(tuple(e) for e in report['events'])
                    assert isinstance(report['injuries'],list) and len(report['injuries'])<=1
                    assert all(e['pid'] in squad and type(e['remaining']) is int and 1<=e['remaining']<=3 and e['kind'] in INJURIES for e in report['injuries'])
                    assert isinstance(report['returned'],list) and set(report['returned'])<=set(squad)

            assert rebuilt==d['table']
            assert isinstance(d['scorers'],dict) and set(d['scorers'])<=set(squad)
            assert all(type(v) is int and v>=0 for v in d['scorers'].values())
            assert sum(d['scorers'].values())==d['table'][g.name]['GF']
            g.fitness=d['fitness']
            formation=d.get('formation','4-3-3')
            if formation not in FORMATIONS: raise ValueError('Unknown formation.')
            g.formation=formation
            if not g.drafting: g.set_lineup(d['lineup'])
            else: assert d['lineup']==[]
            for key in ('week','table','history','scorers'):
                setattr(g,key,d[key])
            if d['version']==2:
                injuries=d['injuries'];preparation=d['preparation']
                assert isinstance(injuries,dict) and set(injuries)<=set(squad)
                for injury in injuries.values():
                    assert isinstance(injury,dict) and set(injury)=={'remaining','kind'}
                    assert type(injury['remaining']) is int and 1<=injury['remaining']<=3
                    assert injury['kind'] in INJURIES
                assert preparation in PREPARATIONS
                assert not g.drafting or (not injuries and preparation=='Balanced')
                g.injuries=injuries;g.preparation=preparation
                # A legitimate injury state always leaves every formation playable.
                if not g.drafting:
                    for form in FORMATIONS:g.suggested_lineup(form)
            state=d['random_state']
            g.rng.setstate((state[0],tuple(state[1]),state[2]))
            return g
        except (KeyError,TypeError,AssertionError,IndexError,AttributeError,ValueError,OverflowError) as exc:
            raise ValueError('Invalid or damaged save file. Your current game was not changed.') from exc
