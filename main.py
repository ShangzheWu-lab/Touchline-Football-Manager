"""Run with python main.py. Bilingual offline Tkinter football manager."""
import json
from pathlib import Path
from collections import Counter
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from game import Game
from data import PLAYERS, POSITIONS, MINIMUM, FORMATIONS
from badges import BadgeBook
from ui_season import SeasonUI

BG='#0c1424'; PANEL='#162237'; INK='#edf3ff'; MUTED='#9aabc4'; GREEN='#53e0a4'
CLUB_ZH={'Arsenal':'阿森纳','Aston Villa':'阿斯顿维拉','Bournemouth':'伯恩茅斯','Brentford':'布伦特福德','Brighton':'布莱顿','Chelsea':'切尔西','Crystal Palace':'水晶宫','Everton':'埃弗顿','Fulham':'富勒姆','Hull City':'赫尔城','Ipswich Town':'伊普斯维奇','Leeds United':'利兹联','Liverpool':'利物浦','Manchester City':'曼城','Manchester United':'曼联','Newcastle United':'纽卡斯尔联','Nottingham Forest':'诺丁汉森林','Sunderland':'桑德兰','Tottenham Hotspur':'托特纳姆热刺'}

class FlatButton(tk.Canvas):
    """Portable, keyboard-accessible button without Aqua colour overrides."""
    def __init__(self,parent,text,command,accent=False):
        self.caption=text; self.command=command
        self.base=GREEN if accent else '#263a56'; self.ink=BG if accent else INK
        super().__init__(parent,height=44,width=max(140,len(text)*9+24),bg=self.base,
                         highlightthickness=2,highlightbackground=self.base,highlightcolor=GREEN,
                         takefocus=True,cursor='hand2',bd=0)
        self.bind('<Configure>',self.paint)
        self.bind('<Enter>',lambda e:super(FlatButton,self).configure(bg='#35634f' if self.ink==BG else '#354e70'))
        self.bind('<Leave>',lambda e:super(FlatButton,self).configure(bg=self.base))
        self.bind('<Button-1>',lambda e:self.focus_set())
        self.bind('<ButtonRelease-1>',self.activate)
        self.bind('<Return>',self.activate); self.bind('<space>',self.activate)
    def paint(self,event=None):
        self.delete('all'); self.create_text(self.winfo_width()/2,self.winfo_height()/2,
            text=self.caption,fill=self.ink,font=('Arial',13,'bold'))
    def activate(self,event=None):
        if event is None or event.type!=tk.EventType.ButtonRelease or (0<=event.x<self.winfo_width() and 0<=event.y<self.winfo_height()): self.command()
        return 'break'

class App(SeasonUI,tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Touchline • Road to Glory'); self.geometry('1400x900'); self.minsize(1180,780); self.configure(bg=BG)
        self.settings=Path.home()/'.touchline_settings.json'; self.lang='en'
        try: self.lang=json.loads(self.settings.read_text()).get('language','en')
        except (OSError,ValueError,AttributeError): pass
        if self.lang not in ('en','zh'): self.lang='en'
        self.game=None; self.dirty=False; self.replaying=False; self.timer=None; self.page='welcome'
        self.badges=BadgeBook(self); self.edit_xi=[]; self.picks=[]
        self.protocol('WM_DELETE_WINDOW',self.close)
        style=ttk.Style(self); style.theme_use('clam')
        style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=INK,rowheight=42,borderwidth=0,font=('Arial',13))
        style.configure('Portrait.Treeview',rowheight=54)
        style.configure('Treeview.Heading',background='#23344e',foreground=INK,font=('Arial',12,'bold'),padding=9)
        style.map('Treeview',background=[('selected','#276951')],foreground=[('selected','white')])
        style.configure('TNotebook',background=BG,borderwidth=0)
        style.configure('TNotebook.Tab',background=PANEL,foreground=INK,padding=(10,8),font=('Arial',12))
        style.map('TNotebook.Tab',background=[('selected','#276951')],foreground=[('selected','white')])
        style.configure('TCombobox',padding=7); self.option_add('*TCombobox*Listbox.font',('Arial',13))
        self.sidebar=tk.Frame(self,bg=PANEL,width=210); self.sidebar.pack(side='left',fill='y'); self.sidebar.pack_propagate(False)
        self.body=tk.Frame(self,bg=BG); self.body.pack(side='left',fill='both',expand=True,padx=22,pady=22)
        self.build_sidebar(); self.welcome()
    def t(self,en,zh): return zh if self.lang=='zh' else en
    def club(self,name): return CLUB_ZH.get(name,name) if self.lang=='zh' else name
    def pos(self,pos): return {'GK':'门将','DEF':'后卫','MID':'中场','FWD':'前锋'}[pos] if self.lang=='zh' else pos
    def label(self,parent,text,size=13,color=INK):
        return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=color,font=('Arial',size),justify='left')
    def button(self,parent,text,command,accent=False): return FlatButton(parent,text,command,accent)
    def build_sidebar(self):
        for child in self.sidebar.winfo_children(): child.destroy()
        self.label(self.sidebar,'TOUCHLINE',20,GREEN).pack(anchor='w',padx=16,pady=(22,4))
        self.label(self.sidebar,self.t('ROAD TO GLORY','通往荣耀之路'),11,MUTED).pack(anchor='w',padx=16,pady=(0,18))
        for en,zh,page in [('Overview','球队总览','overview'),('Draft room','球员选秀','draft'),('Squad & tactics','阵容与战术','squad'),('League table','联赛积分榜','table'),('Results','赛程与赛果','results')]:
            self.button(self.sidebar,self.t(en,zh),lambda p=page:self.navigate(p)).pack(fill='x',padx=12,pady=4)
        tk.Frame(self.sidebar,bg='#34435a',height=1).pack(fill='x',padx=18,pady=14)
        for en,zh,cmd in [('Save game','保存游戏',self.save),('Load game','读取存档',self.load),('New club','创建新球队',self.new_game),('How to play','游戏说明',self.help)]:
            self.button(self.sidebar,self.t(en,zh),cmd).pack(fill='x',padx=12,pady=4)
        language=tk.Frame(self.sidebar,bg=PANEL); language.pack(side='bottom',fill='x',padx=14,pady=20)
        self.label(language,'Language / 语言',11,MUTED).pack(anchor='w',pady=(0,8))
        self.language=ttk.Combobox(language,values=['English','简体中文'],state='readonly',font=('Arial',13),width=14)
        self.language.set('简体中文' if self.lang=='zh' else 'English'); self.language.pack(fill='x')
        self.language.bind('<<ComboboxSelected>>',self.change_language)
    def change_language(self,event=None):
        self.lang='zh' if self.language.get()=='简体中文' else 'en'
        try: self.settings.write_text(json.dumps({'language':self.lang}),encoding='utf-8')
        except OSError: pass
        name=self.name_entry.get() if self.page=='welcome' else None
        selected_round=self.round_select.get() if self.page=='results' else None
        tactic_index=self.tactic.current() if self.page=='overview' and self.game and self.game.week<19 and not self.game.drafting else None
        self.build_sidebar()
        if self.page=='match': self.match_page(); return
        self.show(self.page,preserve=True)
        if name is not None: self.name_entry.delete(0,'end'); self.name_entry.insert(0,name)
        if selected_round: self.round_select.set(selected_round); self.fill_results()
        if tactic_index is not None: self.tactic.current(tactic_index)
    def clear(self,page,title,subtitle=''):
        self.page=page
        for child in self.body.winfo_children(): child.destroy()
        self.label(self.body,title,25).pack(anchor='w')
        self.label(self.body,subtitle,12,MUTED).pack(anchor='w',pady=(7,16))
    def show(self,page,preserve=False):
        if page=='draft': self.draft_page(preserve)
        elif page=='squad': self.squad_page(preserve)
        else: {'welcome':self.welcome,'overview':self.overview,'table':self.table_page,'results':self.results_page,'medical':self.medical_page}[page]()
    def navigate(self,page):
        if self.replaying: self.info(self.t('Finish or skip the replay first.','请先看完或跳过比赛回放。')); return
        if not self.game: self.welcome(); return
        self.show(page)
    def info(self,text): messagebox.showinfo(self.t('Touchline','提示'),text,parent=self)
    def error_text(self,text):
        if self.lang=='en': return text
        mapping={'Use a club name of 1–26 printable characters.':'球队名称必须为 1–26 个可显示字符。','Choose a new club name, not an existing club.':'请创建新队名，不要使用现有球队名称。','Select exactly two different players from this club.':'请从该队选择两名不同的球员。','Keep room for 2 GK, 6 DEF, 6 MID and 4 FWD. Pick a needed position.':'请为至少 2 名门将、6 名后卫、6 名中场和 4 名前锋保留名额。','Select 11 different players from your squad.':'请从名单中选择 11 名不同的首发球员。','Unknown formation.':'未知阵型。','Invalid or damaged save file. Your current game was not changed.':'存档无效或损坏，当前游戏未受影响。','Finish the draft first, or start a new season after week 19.':'请先完成选秀；19 轮结束后请开始新赛季。'}
        if text in mapping:return mapping[text]
        extras={'Injured players cannot start. Replace them or use Auto select.':'伤员不能首发，请替换伤员或使用自动排阵。','Not enough fit players for this formation. Choose another formation.':'当前阵型健康球员不足，请选择其他阵型。','Unknown preparation.':'未知训练方案。','Preparation is available between league matches.':'请在完成选秀后、赛季结束前选择训练。'}
        if text in extras:return extras[text]
        if ' requires ' in text:
            return self.t('Invalid lineup.','首发人数不符合当前阵型，请按界面显示的各位置人数调整。')
        return '操作失败：'+text
    def warn(self,exc): messagebox.showwarning(self.t('Please check','请检查'),self.error_text(str(exc)),parent=self)
    def welcome(self):
        self.clear('welcome',self.t('Build a club. Write its story.','创建球队，书写你的传奇。'),self.t('2026/27 fantasy season • Offline football manager','2026/27 架空赛季 · 离线足球经理'))
        hero=tk.Canvas(self.body,bg='#103e35',height=210,highlightthickness=0); hero.pack(fill='x',pady=12)
        hero.create_text(30,90,text=self.t('YOUR CLUB.\nYOUR STARTING XI.','你的球队。\n你的首发十一人。'),anchor='w',fill='white',font=('Arial',30,'bold'))
        self.label(self.body,self.t('Name your club to replace Coventry City','为替代考文垂加入联赛的新球队命名'),16).pack(anchor='w',pady=(20,10))
        self.name_entry=tk.Entry(self.body,font=('Arial',18),bg=PANEL,fg=INK,insertbackground=GREEN,relief='flat')
        self.name_entry.insert(0,'Sydney United'); self.name_entry.pack(fill='x',ipady=12)
        self.button(self.body,self.t('Create club →','创建球队 →'),self.create,True).pack(anchor='w',pady=18)
        self.label(self.body,self.t('11 draft rounds / 22 players / 19 matches\nFour formations. Choose your XI. Rotate tired players.\nReal club crests and player photographs; fantasy ratings and roster affiliations.','11 轮选秀 / 22 人名单 / 19 场联赛\n四种阵型，自选首发，轮换疲劳球员。\n真实队徽及球员照片；球员归属和评分采用简化游戏数据。'),14,MUTED).pack(anchor='w')
    def create(self):
        try:self.game=Game(self.name_entry.get())
        except ValueError as exc:self.warn(exc); return
        self.dirty=True; self.draft_page()
    def tree(self,parent,columns,widths,portraits=False):
        frame=tk.Frame(parent,bg=BG); frame.pack(fill='both',expand=True)
        tree=ttk.Treeview(frame,columns=[c[0] for c in columns],show='tree headings' if portraits else 'headings',
                          height=10,selectmode='browse',style='Portrait.Treeview' if portraits else 'Treeview')
        if portraits: tree.column('#0',width=54,minwidth=54,stretch=False); tree.heading('#0',text='')
        for (key,en,zh),width in zip(columns,widths):
            tree.heading(key,text=self.t(en,zh)); tree.column(key,width=width,minwidth=35,anchor='w' if key in ('Player','Club','Home','Away') else 'center')
        scroll=ttk.Scrollbar(frame,command=tree.yview); scroll.pack(side='right',fill='y')
        tree.configure(yscrollcommand=scroll.set); tree.pack(fill='both',expand=True)
        tree.tag_configure('mine',foreground=GREEN); tree.tag_configure('tired',foreground='#ffc477')
        return tree
    def club_label(self,parent,club,size=32):
        return tk.Label(parent,text='  '+self.club(club),image=self.badges.get(club,size),compound='left',bg=parent.cget('bg'),fg=INK,font=('Arial',16,'bold'))
    def fixture(self,parent,a,b):
        bar=tk.Frame(parent,bg=BG); bar.pack(fill='x',pady=12)
        self.club_label(bar,a,48).pack(side='left'); self.label(bar,'  VS  ',14,MUTED).pack(side='left',padx=8); self.club_label(bar,b,48).pack(side='left')
    def draft_page(self,preserve=False):
        g=self.game
        if not g.drafting:self.overview(); return
        club=g.draft_clubs[len(g.squad)//2]
        if not preserve:self.picks=[]
        self.clear('draft',self.t('Draft','选秀')+f' {len(g.squad)//2+1:02d} / 11',self.t('Click a player to select or deselect. Sign exactly two per round.','点击球员选择或取消，每轮签下两人。'))
        head=tk.Frame(self.body,bg=BG); head.pack(fill='x',pady=(0,12))
        self.club_label(head,club,48).pack(side='left'); self.label(head,f'{len(g.squad)} / 22 '+self.t('signed','已签约'),16,GREEN).pack(side='right')
        footer=tk.Frame(self.body,bg=BG); footer.pack(side='bottom',fill='x',pady=(14,0))
        self.pick_label=self.label(footer,'',13,MUTED); self.pick_label.pack(side='left')
        self.button(footer,self.t('Sign selected players →','签下所选球员 →'),self.confirm_draft,True).pack(side='right')
        content=tk.Frame(self.body,bg=BG); content.pack(fill='both',expand=True)
        side=tk.Frame(content,bg=PANEL,width=295); side.pack(side='right',fill='y',padx=(14,0)); side.pack_propagate(False)
        self.label(side,self.t('YOUR SQUAD','我的阵容'),15,GREEN).pack(anchor='w',padx=14,pady=12)
        self.player_card=tk.Label(side,bg=PANEL,fg=INK,font=('Arial',12),compound='top'); self.player_card.pack(fill='x',padx=8)
        self.roster_text=tk.Text(side,bg=PANEL,fg=INK,font=('Arial',12),bd=0,wrap='word',padx=14,pady=6,width=24,state='disabled')
        sc=ttk.Scrollbar(side,command=self.roster_text.yview); sc.pack(side='right',fill='y'); self.roster_text.pack(fill='both',expand=True); self.roster_text.configure(yscrollcommand=sc.set)
        self.roster_text.tag_configure('heading',foreground=GREEN,font=('Arial',13,'bold'),spacing1=12,spacing3=6)
        self.roster_text.tag_configure('pending',foreground='#ffc477')
        self.roster_text.tag_configure('muted',foreground=MUTED)
        left=tk.Frame(content,bg=BG); left.pack(side='left',fill='both',expand=True)
        self.draft_tree=self.tree(left,[('Pick','Pick','选择'),('Player','Player','球员'),('Position','Position','位置'),('Rating','Rating','评分')],[45,220,70,60],True)
        for p in g.candidates(): self.draft_tree.insert('','end',iid=p['id'],image=self.badges.portrait(p['id'],40),values=('✓' if p['id'] in self.picks else '□',p['name'],self.pos(p['pos']),p['rating']))
        self.draft_tree.bind('<ButtonRelease-1>',self.toggle_pick); self.draft_tree.bind('<space>',self.toggle_pick)
        self.refresh_draft_roster()
        if self.picks: self.portrait_card(self.picks[-1])
    def portrait_card(self,pid):
        p=PLAYERS[pid]
        note='' if self.badges.has_portrait(pid) else '\n'+self.t('Photo unavailable','暂无照片')
        if pid in self.game.injuries:note+='\n'+self.t('Injured: ','伤停：')+str(self.game.injuries[pid]['remaining'])+self.t(' match(es)',' 场')
        self.player_card.configure(image=self.badges.portrait(pid,96),text=f"{p['name']}\n{self.pos(p['pos'])} · {p['rating']}"+note)
    def refresh_draft_roster(self):
        w=self.roster_text; w.configure(state='normal'); w.delete('1.0','end')
        for pos,minimum in MINIMUM.items():
            signed=[PLAYERS[p] for p in self.game.squad if PLAYERS[p]['pos']==pos]
            pending=[PLAYERS[p] for p in self.picks if PLAYERS[p]['pos']==pos]
            extra=f' (+{len(pending)})' if pending else ''
            w.insert('end',f'{self.pos(pos)}  {len(signed)}{extra} / {minimum} '+self.t('min','最低')+'\n','heading')
            for p in signed:w.insert('end',f"{p['name']} · {p['rating']}\n")
            for p in pending:w.insert('end',f"+ {p['name']} · {p['rating']}\n",'pending')
            if not signed and not pending:w.insert('end',self.t('No players yet\n','尚无球员\n'),'muted')
        w.configure(state='disabled'); self.pick_label.configure(text=f'{len(self.picks)} / 2 '+self.t('selected','已选'))
    def toggle_pick(self,event):
        pid=self.draft_tree.identify_row(event.y) if event.type==tk.EventType.ButtonRelease else self.draft_tree.focus()
        if not pid:return
        self.portrait_card(pid)
        if pid in self.picks:self.picks.remove(pid)
        elif len(self.picks)<2:self.picks.append(pid)
        for item in self.draft_tree.get_children():self.draft_tree.set(item,'Pick','✓' if item in self.picks else '□')
        self.refresh_draft_roster(); return 'break'
    def confirm_draft(self):
        try:self.game.draft(self.picks)
        except ValueError as exc:self.warn(exc); return
        self.dirty=True; self.draft_page()
    def overview(self):
        self.season_overview()
    def pitch(self,parent,ids,formation):
        frame=tk.Frame(parent,bg='#164c3d');frame.pack(fill='both',expand=True)
        canvas=tk.Canvas(frame,bg='#164c3d',height=380,highlightthickness=0)
        scroll=ttk.Scrollbar(frame,command=canvas.yview);scroll.pack(side='right',fill='y')
        canvas.configure(yscrollcommand=scroll.set);canvas.pack(fill='both',expand=True)
        def draw(event=None):
            if not canvas.winfo_exists():return
            canvas.delete('all');w=canvas.winfo_width();h=max(510 if formation=='3-4-1-2' else 440,canvas.winfo_height())
            canvas.configure(scrollregion=(0,0,w,h))
            for i in range(8):canvas.create_rectangle(0,i*h/8,w,(i+1)*h/8,fill='#164c3d' if i%2 else '#195542',outline='')
            canvas.create_rectangle(12,12,w-12,h-12,outline='#679a81',width=2)
            canvas.create_line(12,h/2,w-12,h/2,fill='#679a81');canvas.create_oval(w/2-35,h/2-35,w/2+35,h/2+35,outline='#679a81')
            groups={pos:[p for p in ids if PLAYERS[p]['pos']==pos] for pos in POSITIONS}
            rows=[(groups['FWD'],.12),(groups['MID'],.35),(groups['DEF'],.59),(groups['GK'],.82)]
            if formation=='3-4-1-2':rows=[(groups['FWD'],.09),(groups['MID'][4:],.27),(groups['MID'][:4],.45),(groups['DEF'],.64),(groups['GK'],.83)]
            for players,y in rows:
                for j,pid in enumerate(players):
                    x=w*(j+1)/(len(players)+1);yy=h*y;fit=self.game.fitness[pid];hurt=pid in self.game.injuries
                    canvas.create_image(x,yy,image=self.badges.portrait(pid,40))
                    canvas.create_text(x,yy+27,text=PLAYERS[pid]['name'].split()[-1],fill='white',font=('Arial',10,'bold'))
                    if hurt:
                        status=self.t('OUT ','伤停 ')+str(self.game.injuries[pid]['remaining']);colour='#ff8591'
                    else:status=f'{fit}%';colour=GREEN if fit>=85 else '#ffd182' if fit>=70 else '#ff8591'
                    canvas.create_rectangle(x-24,yy+40,x+24,yy+45,fill='#123029',outline='')
                    canvas.create_rectangle(x-24,yy+40,x-24+48*fit/100,yy+45,fill=colour,outline='')
                    canvas.create_text(x,yy+57,text=status,fill=colour,font=('Arial',10,'bold'))
            canvas.create_text(20,16,text=formation+' · '+self.t('Fitness','体能'),fill=GREEN,anchor='nw',font=('Arial',12,'bold'))
        canvas.bind('<Configure>',draw);canvas.after_idle(draw)
        canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
        return canvas
    def squad_page(self,preserve=False):
        g=self.game
        if g.drafting:self.draft_page(); return
        if not preserve:self.edit_xi=list(g.lineup); self.edit_formation=g.formation
        self.clear('squad',self.t('Squad & tactics','阵容与战术'),self.t('Choose a formation, click players to toggle XI, then Apply. Changes stay pending until applied.','选择阵型，点击球员调整首发，再点击应用；应用前不会改变正式首发。'))
        bar=tk.Frame(self.body,bg=BG); bar.pack(fill='x',pady=(0,12))
        self.label(bar,self.t('Formation','阵型')).pack(side='left',padx=(0,12))
        self.formation_select=ttk.Combobox(bar,values=list(FORMATIONS),state='readonly',width=10,font=('Arial',14)); self.formation_select.set(self.edit_formation); self.formation_select.pack(side='left')
        self.formation_select.bind('<<ComboboxSelected>>',self.change_formation)
        self.button(bar,self.t('Apply XI','应用首发'),self.apply_xi,True).pack(side='right',padx=(8,0))
        self.button(bar,self.t('Auto select','自动排阵'),self.auto_xi).pack(side='right')
        self.xi_status=self.label(self.body,'',13,GREEN); self.xi_status.pack(anchor='w',pady=(0,12))
        content=tk.Frame(self.body,bg=BG); content.pack(fill='both',expand=True)
        self.pitch_frame=tk.Frame(content,bg=BG,width=410); self.pitch_frame.pack(side='right',fill='both',padx=(14,0)); self.pitch_frame.pack_propagate(False)
        self.player_card=tk.Label(self.pitch_frame,bg=BG,fg=INK,font=('Arial',12),compound='top'); self.player_card.pack(side='bottom',pady=12)
        self.pitch_holder=tk.Frame(self.pitch_frame,bg=BG); self.pitch_holder.pack(fill='both',expand=True)
        left=tk.Frame(content,bg=BG); left.pack(side='left',fill='both',expand=True)
        self.squad_tree=self.tree(left,[('XI','XI','首发'),('Player','Player','球员'),('Position','Pos','位置'),('Rating','Rating','评分'),('Fitness','Fitness','体能')],[40,185,55,55,60],True)
        for pid in sorted(g.squad,key=lambda p:(list(POSITIONS).index(PLAYERS[p]['pos']),-PLAYERS[p]['rating'])):
            p=PLAYERS[pid]; fit=g.fitness[pid]
            self.squad_tree.insert('','end',iid=pid,image=self.badges.portrait(pid,40),values=('✓' if pid in self.edit_xi else '□',p['name'],self.pos(p['pos']),p['rating'],(self.t('OUT ','伤停 ')+str(g.injuries[pid]['remaining'])) if pid in g.injuries else f'{fit}%'),tags=('tired',) if fit<75 or pid in g.injuries else ())
        self.squad_tree.bind('<ButtonRelease-1>',self.toggle_xi); self.squad_tree.bind('<space>',self.toggle_xi)
        self.update_xi()
    def update_xi(self):
        counts=Counter(PLAYERS[p]['pos'] for p in self.edit_xi); req=FORMATIONS[self.edit_formation]
        self.xi_status.configure(text=f'{len(self.edit_xi)} / 11   |   '+'   '.join(f'{self.pos(p)} {counts[p]}/{n}' for p,n in req.items()))
        for child in self.pitch_holder.winfo_children():child.destroy()
        self.pitch(self.pitch_holder,self.edit_xi,self.edit_formation)
    def change_formation(self,event=None):
        self.edit_formation=self.formation_select.get(); self.update_xi()
    def toggle_xi(self,event):
        pid=self.squad_tree.identify_row(event.y) if event.type==tk.EventType.ButtonRelease else self.squad_tree.focus()
        if not pid:return
        self.portrait_card(pid)
        if pid in self.edit_xi:self.edit_xi.remove(pid)
        elif not self.game.available(pid):self.info(self.t('This player is injured and cannot start.','该球员正在养伤，不能首发。'))
        elif len(self.edit_xi)<11:self.edit_xi.append(pid)
        else:self.info(self.t('Deselect a starter before adding another player.','请先取消一名首发，再加入其他球员。'))
        self.squad_tree.set(pid,'XI','✓' if pid in self.edit_xi else '□'); self.update_xi(); return 'break'
    def apply_xi(self):
        try:self.game.set_lineup(self.edit_xi,self.edit_formation)
        except ValueError as exc:self.warn(exc); return
        self.dirty=True; self.overview()
    def auto_xi(self):
        try:self.edit_xi=self.game.suggested_lineup(self.edit_formation)
        except ValueError as exc:self.warn(exc);return
        self.squad_page(preserve=True)
    def start_match(self):
        try:report=self.game.play(['Balanced','Attacking','Defensive'][self.tactic.current()])
        except ValueError as exc:self.warn(exc); return
        self.dirty=True; self.replaying=True; self.replay_report=report; self.minute=0
        self.match_page(); self.tick()
    def match_page(self):
        report=self.replay_report
        self.clear('match',self.t('Match centre','比赛中心'),self.t('MATCHWEEK','第')+f" {report['week']} / 19")
        a,b,_,_=report['match']; self.fixture(self.body,a,b)
        if 'context' in report:self.label(self.body,self.condition_text(report['context']),12,MUTED).pack(anchor='w',pady=(0,8))
        self.score_label=self.label(self.body,'',42,GREEN); self.score_label.pack(pady=10)
        self.clock=self.label(self.body,'',14,MUTED); self.clock.pack()
        self.stats_label=self.label(self.body,'',12,GREEN);self.stats_label.pack(pady=(8,0))
        self.log=tk.Text(self.body,bg=PANEL,fg=INK,font=('Arial',14),height=8,relief='flat',padx=16,pady=14,state='disabled'); self.log.pack(fill='both',expand=True,pady=18)
        self.match_actions=tk.Frame(self.body,bg=BG); self.match_actions.pack(fill='x')
        self.update_replay()
    def update_replay(self):
        a,b,_,_=self.replay_report['match']; score=[0,0]
        self.log.configure(state='normal'); self.log.delete('1.0','end')
        incidents=self.replay_report.get('commentary',[{'minute':m,'team':t,'scorer':p,'kind':'goal'} for m,t,p in self.replay_report['events']])
        visible=[e for e in incidents if e['minute']<=self.minute]
        for e in visible:
            minute,team,scorer,kind=e['minute'],e['team'],e['scorer'],e['kind']
            if kind=='goal':score[0 if team==a else 1]+=1
            action=self.t({'goal':'GOAL','save':'Shot saved','wide':'Shot wide','corner':'Corner won'}[kind],{'goal':'进球','save':'射门被扑出','wide':'射门偏出','corner':'获得角球'}[kind])
            self.log.insert('end',f"{minute:02d}'  "+action+'  '+self.club(team)+(f' · {scorer}' if scorer else '')+'\n')
        self.stats_label.configure(text=self.replay_stats(visible,score))
        if self.minute>=90:
            for injury in self.replay_report.get('injuries',[]):
                name=PLAYERS[injury['pid']]['name'];n=injury['remaining']
                self.log.insert('end','\n'+self.t(f'Post-match medical: {name} will miss {n} match(es).',f'赛后医疗检查：{name} 将缺席 {n} 场。')+'\n')
            for pid in self.replay_report.get('returned',[]):
                self.log.insert('end',self.t(f'{PLAYERS[pid]["name"]} has recovered.',f'{PLAYERS[pid]["name"]} 已康复。')+'\n')
            if 'xg' in self.replay_report:
                xg=self.replay_report['xg'];self.log.insert('end','\n'+self.t('Model expected goals: ','模型预期进球：')+f'{xg[0]:.2f} – {xg[1]:.2f}\n')
        if self.minute>=90 and not self.replay_report['events']:self.log.insert('end',self.t('Neither side finds the net.','双方均未破门。'))
        self.log.configure(state='disabled'); self.log.see('end')
        self.score_label.configure(text=f'{score[0]}  –  {score[1]}')
        self.clock.configure(text=self.t('FULL TIME • Table updated','全场结束 · 积分榜已更新') if self.minute>=90 else f"{self.minute:02d}'")
        for child in self.match_actions.winfo_children():child.destroy()
        if self.minute>=90:self.button(self.match_actions,self.t('Continue →','继续 →'),self.overview,True).pack(side='right')
        else:self.button(self.match_actions,self.t('Skip to full time','跳至全场结束'),self.skip_replay).pack(side='right')
    def tick(self):
        self.timer=None; self.minute=min(90,self.minute+3); self.update_replay()
        if self.minute>=90:self.replaying=False
        else:self.timer=self.after(200,self.tick)
    def skip_replay(self):
        if self.timer:self.after_cancel(self.timer); self.timer=None
        self.minute=90; self.replaying=False; self.update_replay()
    def table_page(self):
        g=self.game; self.clear('table',self.t('League table','联赛积分榜'),self.t('Sorted by points, goal difference, goals, then name.','依次按积分、净胜球、进球数和队名排序。')+f'  {g.week} / 19')
        cols=[('#','#','排名'),('Club','Club','球队'),('P','P','场'),('W','W','胜'),('D','D','平'),('L','L','负'),('GF','GF','进球'),('GA','GA','失球'),('GD','GD','净胜'),('Pts','Pts','积分')]
        tree=self.tree(self.body,cols,[40,240,42,42,42,42,48,48,48,52],True)
        for rank,club in enumerate(g.standings(),1):
            r=g.table[club]; tree.insert('','end',image=self.badges.get(club,32),values=[rank,self.club(club)]+[r[k] for k in ('P','W','D','L','GF','GA')]+[r['GF']-r['GA'],r['Pts']],tags=('mine',) if club==g.name else ())
    def results_page(self):
        self.clear('results',self.t('Results & fixtures','赛程与赛果'),self.t('Home team first • Browse all 19 rounds','主队在左 · 查看全部 19 轮'))
        bar=tk.Frame(self.body,bg=BG); bar.pack(fill='x',pady=(0,12))
        self.label(bar,self.t('Matchweek','轮次')).pack(side='left',padx=(0,12))
        self.round_select=ttk.Combobox(bar,values=list(range(1,20)),state='readonly',width=8,font=('Arial',14)); self.round_select.set(max(1,self.game.week)); self.round_select.pack(side='left')
        self.result_tree=self.tree(self.body,[('Home','Home','主队'),('Score','Score','比分'),('Away','Away','客队')],[270,100,270],True)
        self.result_tree.column('#0',width=80,minwidth=80,stretch=False); self.result_tree.heading('#0',text=self.t('H / A','主 / 客'))
        self.round_select.bind('<<ComboboxSelected>>',lambda e:self.fill_results()); self.fill_results()
    def fill_results(self):
        week=int(self.round_select.get())-1; g=self.game; tree=self.result_tree; tree.delete(*tree.get_children())
        rows=g.history[week]['results'] if week<g.week else [[a,b,None,None] for a,b in g.schedule[week]]
        for a,b,x,y in rows:tree.insert('','end',image=self.badges.pair(a,b),values=(self.club(a),self.t('Scheduled','未开始') if x is None else f'{x} – {y}',self.club(b)),tags=('mine',) if g.name in (a,b) else ())
    def save(self):
        if not self.game:return
        path=filedialog.asksaveasfilename(parent=self,title=self.t('Save season','保存赛季'),defaultextension='.json',initialfile='touchline_save.json',filetypes=[(self.t('Game save','游戏存档'),'*.json')])
        if not path:return
        try:self.game.save(path)
        except (OSError,ValueError) as exc:self.warn(exc); return
        self.dirty=False; self.info(self.t('Season saved. Pending lineup edits are not saved until applied.','赛季已保存。尚未应用的阵容调整不会写入存档。'))
    def can_leave(self):
        if self.replaying:self.info(self.t('Finish or skip the replay first.','请先看完或跳过回放。')); return False
        return not self.dirty or messagebox.askyesno(self.t('Unsaved progress','进度未保存'),self.t('Discard unsaved progress? Choose No to return and save.','放弃未保存的进度吗？选择“否”可返回保存。'),parent=self)
    def load(self):
        if not self.can_leave():return
        path=filedialog.askopenfilename(parent=self,title=self.t('Load season','读取赛季'),filetypes=[(self.t('Game save','游戏存档'),'*.json')])
        if not path:return
        try:loaded=Game.load(path)
        except (OSError,ValueError) as exc:self.warn(exc); return
        self.game=loaded; self.dirty=False; self.overview()
    def new_game(self):
        if self.can_leave():self.game=None; self.dirty=False; self.welcome()
    def close(self):
        if self.can_leave():self.destroy()
    def help(self):
        self.info(self.t('NEW SEASON FEATURES\nTraining is selected in Overview and applied once at kick-off.\nRecovery: +8 fitness and lower injury risk. Attack/Defence change chances with trade-offs.\nInjuries are diagnosed after matches; players miss the next 1–3 games.\nThe medical tab shows who is unavailable. Auto selection excludes injured players.\nWeather is simulated, affects both teams and never changes on refresh.\nNews comes from this save; board goals are 25 points, 30 goals and 5 clean sheets.\n\n','新增赛季功能\n在总览选择训练，开赛时仅结算一次。\n恢复：体能 +8、降低伤病风险；进攻／防守演练各有利弊。\n伤病在赛后确诊，伤员将缺席接下来 1–3 场。\n医疗页签显示伤员；自动排阵会排除伤员。\n天气由游戏生成，影响双方，不会因刷新而改变。\n新闻源于当前存档；目标为 25 分、30 球和 5 场零封。\n\n')+
        self.t('1. Name your club, then draft two players per round.\n2. Keep at least 2 GK, 6 DEF, 6 MID and 4 FWD.\n3. Choose 4-3-3, 4-4-2, 5-4-1 or 3-4-1-2.\n4. Select XI manually or Auto select, then Apply XI.\n5. Play 19 rounds; rotate tired players between matches.\n6. Save/load JSON files at any time.\n\n3-4-1-2 uses five MID players; the fifth plays behind the forwards.\nFormation sets positions; ratings and fitness determine strength.\nAttacking raises both teams’ chances; Defensive lowers both.\nLanguage can be switched without losing progress. Player names stay in Latin script.\nPhotos and crests are bundled; missing photos use a marked placeholder.\nRoster affiliations and ratings are fantasy game data.',
        '1. 创建球队，每轮选两名球员，共 11 轮。\n2. 至少保留 2 名门将、6 名后卫、6 名中场、4 名前锋。\n3. 选择 4-3-3、4-4-2、5-4-1 或 3-4-1-2。\n4. 手动选择或自动排阵后，点击“应用首发”。\n5. 进行 19 轮联赛，注意轮换疲劳球员。\n6. 可随时保存或读取 JSON 存档。\n\n3-4-1-2 使用五名中场，第五名位于前锋身后。\n阵型决定位置要求；评分与体能决定球队实力。\n进攻战术增加双方机会，防守战术减少双方机会。\n切换语言不会丢失进度；球员姓名保留拉丁字母。\n照片及队徽随包提供，缺失照片明确标注。\n球员归属及评分为简化游戏数据。'))

if __name__=='__main__': App().mainloop()
