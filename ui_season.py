"""Bilingual dashboard and season panels; no external service required at runtime."""
import tkinter as tk
from tkinter import ttk
from data import PLAYERS, RAW
from season import PREPARATIONS
BG='#0c1424';PANEL='#162237';INK='#edf3ff';MUTED='#9aabc4';GREEN='#53e0a4'

class SeasonUI:
    def weather_name(self,value):
        return self.t(value,{'Clear':'晴','Cloudy':'多云','Rain':'雨','Wind':'大风'}[value])
    def prep_name(self,value):
        return self.t({'Balanced':'Balanced training','Recovery':'Recovery session','Attack':'Attacking drills','Defence':'Defensive drills'}[value],
                      {'Balanced':'常规训练','Recovery':'恢复训练','Attack':'进攻演练','Defence':'防守演练'}[value])
    def prep_description(self,value):
        return self.t({
          'Balanced':'No bonus or penalty. Preparation applies once, at kick-off.',
          'Recovery':'All players +8 fitness at kick-off; injury risk ×0.55. Injuries still need matches to heal.',
          'Attack':'Your goal expectation +0.25; opponent +0.10. More attacking opportunities, more exposure.',
          'Defence':'Opponent goal expectation −0.25; yours −0.10. Fewer chances at both ends.'}[value],{
          'Balanced':'不额外加成或减成。训练效果仅在开赛时结算一次。',
          'Recovery':'开赛时全员体能 +8，伤病概率 ×0.55；现有伤病仍需按场次康复。',
          'Attack':'己方预期进球 +0.25，对手 +0.10；增加进攻，也增加防守压力。',
          'Defence':'对手预期进球 −0.25，己方 −0.10；降低双方机会。'}[value])
    def condition_text(self,ctx):
        effect=self.t('Rain: chances ×0.90, slightly higher injury risk','雨天：进球机会 ×0.90，伤病风险略增') if ctx['weather']=='Rain' else self.t('Wind: chances ×0.85','大风：进球机会 ×0.85') if ctx['weather']=='Wind' else self.t('Normal playing conditions','比赛条件正常')
        return f"{ctx['stadium']}  ·  {self.weather_name(ctx['weather'])} {ctx['temperature']}°C  ·  {ctx['kickoff']}"+'\n'+self.t('Simulated conditions • ','游戏生成天气 · ')+effect
    def readonly(self,parent,text,size=12):
        frame=tk.Frame(parent,bg=PANEL);frame.pack(fill='both',expand=True)
        w=tk.Text(frame,bg=PANEL,fg=INK,font=('Arial',size),relief='flat',wrap='word',padx=14,pady=12,width=22,height=5)
        scroll=ttk.Scrollbar(frame,command=w.yview);scroll.pack(side='right',fill='y');w.pack(fill='both',expand=True);w.configure(yscrollcommand=scroll.set)
        w.insert('1.0',text);w.configure(state='disabled');return w
    def goal_text(self):
        g=self.game;lines=[self.t('BOARD OBJECTIVES','董事会目标')]
        for title,current,target in g.goals():
            title=self.t(title,{'Points':'联赛积分','Goals':'联赛进球','Clean sheets':'零封场次'}[title]);done=current>=target
            lines.append(('✓ ' if done else '○ ')+f'{title}: {current} / {target}')
        lines.append('\n'+self.t('Objectives are season milestones; they do not grant hidden stat bonuses.','目标用于赛季评价，不会暗中增加球员能力。'))
        lines.append('\n'+self.t('CLUB SCORERS','队内射手榜'))
        for pid,n in sorted(g.scorers.items(),key=lambda item:-item[1])[:5]:lines.append(f"{PLAYERS[pid]['name']}  ·  {n}")
        if not g.scorers:lines.append(self.t('No goals yet.','暂未进球。'))
        return '\n\n'.join(lines)
    def medical_text(self):
        g=self.game;lines=[]
        for pid,inj in g.injuries.items():
            kind=self.t(inj['kind'],{'Knock':'轻微碰撞伤','Ankle sprain':'踝关节扭伤','Muscle strain':'肌肉拉伤'}[inj['kind']])
            lines.append(f"{PLAYERS[pid]['name']} · {self.pos(PLAYERS[pid]['pos'])}\n{kind} · "+self.t(f"Out for next {inj['remaining']} match(es)",f"缺席接下来 {inj['remaining']} 场"))
        if not lines:lines.append(self.t('All players available.','全员健康，可以出场。'))
        lines.append('\n'+self.t('Injuries are diagnosed after full time. A player with 1 remaining match must sit out the NEXT fixture, then returns.','伤病在赛后检查时确诊。剩余 1 场意味着必须缺席下一场，随后恢复。'))
        lines.append(self.t('Recovery adds fitness; it does not instantly heal injuries. Auto select excludes injured players.','恢复训练提高体能，不会立即治愈伤病。自动排阵会排除伤员。'))
        return '\n\n'.join(lines)
    def news_text(self):
        return self.t('IN-GAME CLUB NEWS • Not real-world reporting\n\n','游戏内球队新闻 · 非现实报道\n\n')+'\n\n'.join('• '+self.t(en,zh) for en,zh in self.game.news())
    def season_overview(self):
        g=self.game
        if g.drafting:self.draft_page();return
        rank=g.standings().index(g.name)+1;row=g.table[g.name]
        self.clear('overview',g.name,self.t('Club headquarters','球队总部')+f' · {g.week} / 19 · '+g.formation)
        cards=tk.Frame(self.body,bg=BG);cards.pack(fill='x',pady=(0,12))
        avg=sum(g.fitness[p] for p in g.lineup)/11
        form=' '.join(self.t(v,{'W':'胜','D':'平','L':'负'}[v]) for v in g.form()) or '—'
        for en,zh,value in [('RANK / POINTS','排名 / 积分',f'#{rank} / {row["Pts"]}'),('XI FITNESS','首发平均体能',f'{avg:.0f}%'),('INJURIES','伤员',str(len(g.injuries))),('LAST FIVE','近五场',form)]:
            card=tk.Frame(cards,bg=PANEL);card.pack(side='left',fill='both',expand=True,padx=4)
            self.label(card,self.t(en,zh),11,MUTED).pack(pady=(8,3));self.label(card,value,20,GREEN).pack(pady=(0,8))
        if g.week<19:
            ctx=g.context();a,b=ctx['home'],ctx['away'];opponent=b if a==g.name else a
            match=tk.Frame(self.body,bg=BG);match.pack(fill='x')
            self.club_label(match,a,32).pack(side='left');self.label(match,' VS ',12,MUTED).pack(side='left');self.club_label(match,b,32).pack(side='left')
            self.label(match,self.t('Opponent rating','对手实力')+f' {RAW[opponent][0]}',12,MUTED).pack(side='right')
            self.label(self.body,self.condition_text(ctx),11,MUTED).pack(anchor='w',pady=(5,8))
            controls=tk.Frame(self.body,bg=BG);controls.pack(fill='x',pady=(0,4))
            self.label(controls,self.t('Training','训练'),12).pack(side='left',padx=(0,5))
            self.prep_select=ttk.Combobox(controls,values=[self.prep_name(p) for p in PREPARATIONS],state='readonly',width=17,font=('Arial',12));self.prep_select.current(PREPARATIONS.index(g.preparation));self.prep_select.pack(side='left',padx=(0,12));self.prep_select.bind('<<ComboboxSelected>>',self.change_preparation)
            self.label(controls,self.t('Tactic','战术'),12).pack(side='left',padx=(0,5))
            self.tactic=ttk.Combobox(controls,values=[self.t('Balanced','平衡'),self.t('Attacking','进攻'),self.t('Defensive','防守')],state='readonly',width=10,font=('Arial',12));self.tactic.current(0);self.tactic.pack(side='left')
            self.button(controls,self.t('Play match →','开始比赛 →'),self.start_match,True).pack(side='right')
            self.prep_hint=self.label(self.body,self.prep_description(g.preparation),11,GREEN);self.prep_hint.pack(fill='x',pady=(3,10));self.prep_hint.configure(anchor='w');self.prep_hint.bind('<Configure>',lambda e:self.prep_hint.configure(wraplength=max(100,e.width-8)))
        else:
            title=self.t('CHAMPIONS','联赛冠军') if rank==1 else self.t('TOP FOUR','进入前四') if rank<=4 else self.t('SURVIVAL','保级成功') if rank<=17 else self.t('RELEGATED','球队降级')
            self.label(self.body,title,22,GREEN).pack(anchor='w',pady=(4,12))
        content=tk.Frame(self.body,bg=BG);content.pack(fill='both',expand=True)
        side=tk.Frame(content,bg=BG,width=320);side.pack(side='right',fill='y',padx=(14,0));side.pack_propagate(False)
        notebook=ttk.Notebook(side);notebook.pack(fill='both',expand=True)
        for en,zh,text in [('News','新闻',self.news_text()),('Medical','医疗',self.medical_text()),('Goals','目标',self.goal_text())]:
            panel=tk.Frame(notebook,bg=PANEL);notebook.add(panel,text=self.t(en,zh));self.readonly(panel,text)
        self.button(side,self.t('Manage starting XI','调整首发阵容'),self.squad_page).pack(fill='x',pady=(10,0))
        field=tk.Frame(content,bg=BG);field.pack(side='left',fill='both',expand=True)
        self.pitch(field,g.lineup,g.formation)
    def change_preparation(self,event=None):
        try:self.game.set_preparation(PREPARATIONS[self.prep_select.current()])
        except ValueError as exc:self.warn(exc);return
        self.dirty=True;self.prep_hint.configure(text=self.prep_description(self.game.preparation))
    def medical_page(self):
        self.clear('medical',self.t('Medical centre','医疗中心'),self.t('Unavailable players and recovery timelines','伤员名单与康复进度'))
        self.readonly(self.body,self.medical_text(),14)
        self.button(self.body,self.t('Manage starting XI','调整首发阵容'),self.squad_page,True).pack(anchor='e',pady=12)
    def replay_stats(self,events,score):
        teams=self.replay_report['match'][:2];result=[]
        for team in teams:
            kinds=[e['kind'] for e in events if e['team']==team]
            result.append((sum(k in ('goal','save','wide') for k in kinds),sum(k in ('goal','save') for k in kinds),kinds.count('corner')))
        return self.t('Shots / On target / Corners','射门 / 射正 / 角球')+f'    {result[0][0]} / {result[0][1]} / {result[0][2]}    —    {result[1][0]} / {result[1][1]} / {result[1][2]}'
