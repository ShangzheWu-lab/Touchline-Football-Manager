"""Small season features: deterministic weather, preparation, injuries and objectives."""
import hashlib
import random
from collections import Counter
from data import PLAYERS, FORMATIONS

# Venue names checked against https://www.premierleague.com/en/news/4725666
STADIUMS = {
 'Arsenal':'Emirates Stadium', 'Aston Villa':'Villa Park',
 'Bournemouth':'Vitality Stadium', 'Brentford':'Gtech Community Stadium',
 'Brighton':'American Express Stadium', 'Chelsea':'Stamford Bridge',
 'Crystal Palace':'Selhurst Park', 'Everton':'Hill Dickinson Stadium',
 'Fulham':'Craven Cottage', 'Hull City':'MKM Stadium', 'Ipswich Town':'Portman Road',
 'Leeds United':'Elland Road', 'Liverpool':'Anfield', 'Manchester City':'Etihad Stadium',
 'Manchester United':'Old Trafford', 'Newcastle United':"St James' Park",
 'Nottingham Forest':'City Ground', 'Sunderland':'Stadium of Light',
 'Tottenham Hotspur':'Tottenham Hotspur Stadium',
}
PREPARATIONS = ('Balanced','Recovery','Attack','Defence')
WEATHER = ('Clear','Cloudy','Rain','Wind')
INJURIES = ('Knock','Ankle sprain','Muscle strain')

class SeasonFeatures:
    def available(self,pid): return pid not in self.injuries

    def context(self,week=None):
        """Stable generated conditions; refreshing the screen never rerolls weather."""
        week=self.week if week is None else week
        if not 0<=week<19: return None
        a,b=next(pair for pair in self.schedule[week] if self.name in pair)
        seed=int.from_bytes(hashlib.sha256(f'{self.name}:{week}:{a}:{b}'.encode()).digest()[:8],'big')
        rng=random.Random(seed)
        return {'stadium':STADIUMS.get(a,self.name+' Park'),'home':a,'away':b,
                'weather':rng.choices(WEATHER,[3,4,2,1])[0], 'temperature':rng.randint(5,23),
                'kickoff':rng.choice(['12:30','15:00','17:30','20:00'])}

    def set_preparation(self,value):
        if value not in PREPARATIONS: raise ValueError('Unknown preparation.')
        if self.drafting or self.week>=19: raise ValueError('Preparation is available between league matches.')
        self.preparation=value

    def suggested_lineup(self,formation=None):
        formation=formation or self.formation
        if formation not in FORMATIONS: raise ValueError('Unknown formation.')
        selected=[]
        for pos,n in FORMATIONS[formation].items():
            choices=[p for p in self.squad if PLAYERS[p]['pos']==pos and self.available(p)]
            selected+=sorted(choices,key=self.effective,reverse=True)[:n]
        if len(selected)!=11: raise ValueError('Not enough fit players for this formation. Choose another formation.')
        return selected

    def resolve_medical(self,starting_fitness,preparation,weather):
        """Diagnosed after the game: a new injury misses the next 1–3 fixtures.

        Existing injuries count down only after a match. Keep enough healthy players
        for every supported formation, so this small roster cannot become unplayable.
        """
        returned=[]
        for pid in list(self.injuries):
            self.injuries[pid]['remaining']-=1
            if self.injuries[pid]['remaining']==0:
                returned.append(pid);del self.injuries[pid]
        new=[]
        healthy=Counter(PLAYERS[p]['pos'] for p in self.squad if self.available(p))
        required={pos:max(f[pos] for f in FORMATIONS.values()) for pos in ('GK','DEF','MID','FWD')}
        candidates=list(self.lineup); self.rng.shuffle(candidates)
        for pid in candidates:
            pos=PLAYERS[pid]['pos']
            if healthy[pos]<=required[pos]:continue
            risk=0.012+max(0,80-starting_fitness[pid])*0.0017
            if weather=='Rain':risk+=0.008
            if preparation=='Recovery':risk*=0.55
            if self.rng.random()<risk:
                remaining=self.rng.randint(1,3);kind=INJURIES[remaining-1]
                self.injuries[pid]={'remaining':remaining,'kind':kind}
                new.append({'pid':pid,'remaining':remaining,'kind':kind});break
        return new,returned

    def form(self,limit=5):
        result=[]
        for report in self.history[-limit:]:
            a,b,x,y=report['match'];own,opp=(x,y) if a==self.name else (y,x)
            result.append('W' if own>opp else 'D' if own==opp else 'L')
        return result

    def goals(self):
        clean=sum((r['match'][3] if r['match'][0]==self.name else r['match'][2])==0 for r in self.history)
        return [('Points',self.table[self.name]['Pts'],25),('Goals',self.table[self.name]['GF'],30),('Clean sheets',clean,5)]

    def news(self):
        """Bilingual game-world stories derived from actual save data, not real news."""
        stories=[]
        for pid,injury in self.injuries.items():
            name=PLAYERS[pid]['name'];n=injury['remaining']
            stories.append((f'Medical update: {name} will miss the next {n} match(es).',f'医疗通报：{name} 将缺席接下来 {n} 场比赛。'))
        if self.history:
            last=self.history[-1];a,b,x,y=last['match'];own,opp=(x,y) if a==self.name else (y,x);opponent=b if a==self.name else a
            verdict='Victory' if own>opp else 'Draw' if own==opp else 'Defeat';zh='赢球' if own>opp else '战平' if own==opp else '失利'
            stories.append((f'{verdict}: {self.name} {own}–{opp} {opponent}. The club is now #{self.standings().index(self.name)+1}.',f'{zh}：{self.name} {own}–{opp} {opponent}，目前排名第 {self.standings().index(self.name)+1}。'))
            for pid in last.get('returned',[]):
                stories.append((f'{PLAYERS[pid]["name"]} has recovered and is available again.',f'{PLAYERS[pid]["name"]} 已康复，可以重新出场。'))
            if own>opp and 'strengths' in last and last['strengths'][0 if a==self.name else 1]<last['strengths'][1 if a==self.name else 0]:
                stories.append(('Against the odds: your team beat a stronger-rated opponent.','以弱胜强：球队击败了评分更高的对手。'))
        form=self.form(3)
        if len(form)==3 and form==['W']*3:stories.append(('Three wins in a row! Supporters are celebrating the club’s momentum.','三连胜！球迷正在庆祝球队的出色状态。'))
        tired=sum(self.fitness[p]<75 for p in self.lineup)
        if tired:stories.append((f'Rotation watch: {tired} starters are below 75% fitness. Consider recovery or fresh legs.',f'轮换提醒：{tired} 名首发体能低于 75%，可考虑恢复训练或换人。'))
        if self.scorers:
            top=max(self.scorers,key=self.scorers.get);n=self.scorers[top]
            stories.append((f'Golden boot watch: {PLAYERS[top]["name"]} leads the club with {n} goals.',f'射手动态：{PLAYERS[top]["name"]} 以 {n} 球领跑队内射手榜。'))
        for title,current,target in self.goals():
            if current>=target:stories.append((f'Board objective completed: {title} ({current}/{target}).',f'董事会目标达成：'+{'Points':'积分','Goals':'进球','Clean sheets':'零封'}[title]+f'（{current}/{target}）。'))
        if not self.history:stories.append(('A new era begins. The board targets 25 points, 30 goals and five clean sheets.','新征程开始：董事会希望球队取得 25 分、30 粒进球及 5 场零封。'))
        if self.week==19:
            achieved=sum(current>=target for _,current,target in self.goals())
            stories.insert(0,(f'Season review: {achieved}/3 board objectives achieved.',f'赛季总结：已完成 {achieved}/3 项董事会目标。'))
        return stories
