Path = 'Event/PersonalDump/'
ShortVersion = False
OneTable = False
DumpCrystal = False
Island = 0
# eventstyle = 'style = "background:#ffe4c3" |'
eventstyle = ''
# Go to root of PyNXReader
import sys
sys.path.append('../')
from lookups import PKMString
from structure import Den
from structure import NestHoleReward8Archive, NestHoleDistributionEncounter8Archive, NestHoleCrystalEncounter8Archive, NestHoleDistributionReward8Archive
from structure import PersonalTable

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

def getstars(rank):
	stars = '★'
	for pp in range(rank):
		stars += '★'
	return stars

def getitem(itemid):
	if itemid >= 1130 and itemid <= 1229:
		tr = itemid - 1130
		return "{{Bag|TR " + pmtext.trtypes[tr] + "}}{{TR|" + f'{tr}' + "|8}}"
	else:
		return "{{Bag|" + pmtext.items[itemid] + "}}{{i|" + pmtext.items[itemid] + "}}"

def getspecies(species, isgmax = False, formid = 0, isShiny = False):
	formtext = pmtext.forms[pt.getFormeNameIndex(species,formid)]
	if species == 849:
		t = '{{MSP|' + f'{species:03}' +('GM' if isgmax else 'L' if formid == 1 else '') + '}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	elif species == 868:
		t = '{{MSP|' + f'{species:03}' + '}}<br>[[' + pmtext.species[species] + ']]' + ('<br />[[File:Dynamax Sprite.png|link=Gigantamax]]' if isgmax else '')
	elif species == 869:
		t = '{{MSP|' + f'{species:03}' +('GM' if isgmax else '') + '}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	elif species == 678 or species == 876:
		t = '{{MSP|' + f'{species:03}' +('F' if formid else '') + '}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	elif species in PersonalTable.Alolalist and formid == 1:
		t = '{{MSP|' + f'{species:03}' + 'A}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	elif species in PersonalTable.Galarlist and formid:
		t = '{{MSP|' + f'{species:03}' + 'G}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	elif species in [422,423]:
		t = '{{MSP|' + f'{species:03}' +('E' if formid else '') + '}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	elif species == 479 and formid > 0:
		if formid == 1:
			rotomform = 'H'
		else:
			rotomform = 'W'
		t = '{{MSP|' + f'{species:03}' + rotomform + '}}<br>[[' + pmtext.species[species] + ']]<br><small>' + formtext + '</small>'
	else:
		t = '{{MSP|' + f'{species:03}' +('GM' if isgmax else '') + '}}<br>[[' + pmtext.species[species] + ']]' + (f'<br>FormeID:{formid}' if formid > 0 else '')
	if isShiny:
		t+= '<br>[[File:ShinySWSHStar.png]]'
	return t

def getmsg1(entry, rank, isCrystal = False):
	return '| ' + getspecies(entry.Species(),entry.IsGigantamax(),entry.AltForm(),entry.ShinyFlag() == 2) + (f' || {getstars(rank)} || ' if isCrystal else f' || {entry.Probabilities(rank)}% || ')

def getmsg2(entry, rank, isCrystal = False):
	pi = pt.getFormeEntry(entry.Species(),entry.AltForm())
	msg = f'{entry.Level()}' + ' || '
	msg += (f"{entry.IVHp()}/{entry.IVAtk()}/{entry.IVDef()}/{entry.IVSpAtk()}/{entry.IVSpDef()}/{entry.IVSpe()} || " if isCrystal else (f'{entry.FlawlessIVs()}' + ' || '))
	msg += f'{entry.Shield()}' + ' || '
	msg += f'{entry.DynamaxLevel()}' + ' || '
	msg += f'{entry.DynamaxBoost():0.1f}' + '× || '
	Sep = '}}<br>{{m|'
	msg += '{{m|'
	if entry.Move3() > 0:
		msg += f"{pmtext.moves[entry.Move0()]}{Sep}{pmtext.moves[entry.Move1()]}{Sep}{pmtext.moves[entry.Move2()]}{Sep}{pmtext.moves[entry.Move3()]}"
	elif entry.Move2() > 0:
		msg += f"{pmtext.moves[entry.Move0()]}{Sep}{pmtext.moves[entry.Move1()]}{Sep}{pmtext.moves[entry.Move2()]}"
	elif entry.Move1() > 0:
		msg += f"{pmtext.moves[entry.Move0()]}{Sep}{pmtext.moves[entry.Move1()]}"
	else:
		msg += f"{pmtext.moves[entry.Move0()]}"
	msg += "}}"
	if entry.AdditionalMove1Rate() > 0 and entry.AdditionalMove1PP() > 0:
		msg += "<br><br>{{m|" + f"{pmtext.moves[entry.AdditionalMove1()]}" + "}}<br>" + f"({entry.AdditionalMove1Rate()}% - {entry.AdditionalMove1PP()}PP)"
	if entry.AdditionalMove2Rate() > 0 and entry.AdditionalMove2PP() > 0:
		msg += "<br>{{m|" + f"{pmtext.moves[entry.AdditionalMove2()]}" + "}}<br>" + f"({entry.AdditionalMove2Rate()}% - {entry.AdditionalMove2PP()}PP)"
	msg += ' || '

	dropid = entry.DropTableID()
	# look up local drop tables
	for jj in range(drop.TablesLength()):
		ldt = drop.Tables(jj)
		if dropid == ldt.TableID():
			for kk in range(ldt.EntriesLength()):
				ldte = ldt.Entries(kk)
				if ldte.Values(rank) > 0:
					msg += f'{ldte.Values(rank)}% ' + getitem(ldte.ItemID()) + "<br>"
	# look up event drop tables
	for jj in range(dropreward.TablesLength()):
		edt = dropreward.Tables(jj) # event drop table
		if dropid == edt.TableID():
			msg += eventstyle
			for kk in range(edt.EntriesLength()):
				edte = edt.Entries(kk)
				if rank == 0:
				 	value = edte.Value0()
				elif rank == 1:
				 	value = edte.Value1()
				elif rank == 2:
					value = edte.Value2()
				elif rank == 3:
					value = edte.Value3()
				else:
					value = edte.Value4()
				if value > 0:
					msg += f'{value}% ' + getitem(edte.ItemID()) + "<br>"
	msg = msg[:-4] + ' || '


	bonusid = entry.BonusTableID()
	# look up local bonus tables
	for jj in range(bonus.TablesLength()):
		lbt = bonus.Tables(jj)
		if bonusid == lbt.TableID():
			for kk in range(lbt.EntriesLength()):
				lbte = lbt.Entries(kk)
				if lbte.Values(rank) > 0:
					msg += f'{lbte.Values(rank)}×' + getitem(lbte.ItemID()) + "<br>"
	# look up event bonus tables
	for jj in range(bonusreward.TablesLength()):
		ebt = bonusreward.Tables(jj) # event bonus table
		if bonusid == ebt.TableID():
			msg += eventstyle
			for kk in range(ebt.EntriesLength()):
				ebte = ebt.Entries(kk)
				if rank == 0:
				 	value = ebte.Value0()
				elif rank == 1:
				 	value = ebte.Value1()
				elif rank == 2:
					value = ebte.Value2()
				elif rank == 3:
					value = ebte.Value3()
				else:
					value = ebte.Value4()
				if value > 0:
					msg += f'{value}×' + getitem(ebte.ItemID()) + "<br>"
	msg = msg[:-4] + ' || '

	comment = ''
	if entry.ShinyFlag() == 1:
		comment += "Cannot be shiny<br>"
	elif entry.ShinyFlag() == 2:
		pass # comment += "Shiny<br>"
	if entry.Ability() == 4:
		pass # comment +=f"can be HA<br>"
	elif entry.Ability() == 3:
		comment +=f"No Hidden Ability<br>"
	elif entry.Ability() == 2:
		comment += f"Ability:（{{{{a|{pmtext.abilities[pi.AbilityH()]}}}}}）<br>"
	elif entry.Ability() == 1:
		comment += f"Ability:（{{{{a|{pmtext.abilities[pi.Ability2()]}}}}}）<br>"
	else:
		comment += f"Ability:（{{{{a|{pmtext.abilities[pi.Ability1()]}}}}}）<br>"
	if entry.Nature() == 25:
		pass # random nature
	else:
		comment += f"Nature: [[{pmtext.natures[entry.Nature()]}]]<br>"
	# if not isCrystal and entry.Field13() > 4:
		# comment += f"Cannot be captured<br>"
	# if entry.AltForm() > 0:
	# 	comment += f"Forme:{entry.AltForm()}<br>"
	msg += ('-' if comment == '' else comment[:-4])
	return msg

def getspecies_short(species, isgmax = False, formid = 0):
	if species == 849 or species == 869:
		t = f'{species:03}' +('GM' if isgmax else '') + '|' + pmtext.species[species]
	else:
		t = f'{species:03}' + '|' + pmtext.species[species]
	return t

def getform_short(species, isgmax = False, formid = 0, isShiny = False):
	t = ''
	formtext = pmtext.forms[pt.getFormeNameIndex(species,formid)]
	if species in [422,423,849,869,678,876] or ((species in pt.Galarlist or species in pt.Alolalist) and formid):
		t = f"|form={formtext}"
	if isgmax:
		t = "|form=Gigantamax" if t == '' else (t + '<br>Gigantamax')
	if isShiny:
		t = "|form=Shiny" if t == '' else (t + '<br>Shiny')
	return t

def gettype_short(species, formid = 0):
	pi = pt.getFormeEntry(species,formid)
	type1 = pmtext.types[pi.Type1()]
	type2 = pmtext.types[pi.Type2()]
	if type1 == type2:
		return "type1=" + type1
	else:
		return "type1=" + type1 + "|type2=" + type2

def getmsg2_short(entry, rank):
	msg = f'|Raid|{entry.Level()}|{entry.Probabilities(rank)}%|'
	msg += gettype_short(entry.Species(),entry.AltForm())
	msg += getform_short(entry.Species(),entry.IsGigantamax(),entry.AltForm(),entry.ShinyFlag() == 2) + "}}"
	return msg

pmtext = PKMString('en')
buf = bytearray(open('../resources/bytes/local_drop','rb').read())
drop = NestHoleReward8Archive.GetRootAsNestHoleReward8Archive(buf,0)
buf = bytearray(open('../resources/bytes/local_bonus','rb').read())
bonus = NestHoleReward8Archive.GetRootAsNestHoleReward8Archive(buf,0)
buf = bytearray(open('../resources/bytes/personal_swsh','rb').read())
pt = PersonalTable(buf)

buf = bytearray(open(Path + 'normal_encount','rb').read()) if Island == 0 else bytearray(open(Path + f'normal_encount_rigel{Island}','rb').read())
eventencounter = NestHoleDistributionEncounter8Archive.GetRootAsNestHoleDistributionEncounter8Archive(buf,0x20)
buf = bytearray(open(Path + 'drop_rewards','rb').read())
dropreward = NestHoleDistributionReward8Archive.GetRootAsNestHoleDistributionReward8Archive(buf,0x20)
buf = bytearray(open(Path + 'bonus_rewards','rb').read())
bonusreward = NestHoleDistributionReward8Archive.GetRootAsNestHoleDistributionReward8Archive(buf,0x20)
buf = bytearray(open(Path + 'dai_encount','rb').read())
crystalencounter = NestHoleCrystalEncounter8Archive.GetRootAsNestHoleCrystalEncounter8Archive(buf,0x20)

tablenum = eventencounter.TablesLength()
tablelength = eventencounter.Tables(0).EntriesLength()
if tablenum != 2 or eventencounter.Tables(1).EntriesLength() != tablelength:
	print('Not a standard table')

if ShortVersion:
	print('{{catch/header/8|red|no}}')
	header = '{{catch/entry8|'
	for star in range(5):
		stars = getstars(star)
		print('{{catch/div|red|'+ stars +'}}')
		for ii in range(tablelength):
			entry1 = eventencounter.Tables(0).Entries(ii)
			entry2 = eventencounter.Tables(1).Entries(ii)
			if entry1.Species() == entry2.Species() and entry1.AltForm() == entry2.AltForm() and entry1.IsGigantamax() == entry2.IsGigantamax() and entry1.ShinyFlag() == entry2.ShinyFlag() and entry1.Probabilities(star) == entry2.Probabilities(star):
				# Same entry
				if entry1.Probabilities(star) > 0:
					msg = header + getspecies_short(entry1.Species(),entry1.IsGigantamax(),entry1.AltForm())
					msg += '|yes|yes'
					msg += getmsg2_short(entry1,star)
					print(msg)
			else:
				if entry1.Probabilities(star) > 0:
					msg = header + getspecies_short(entry1.Species(),entry1.IsGigantamax(),entry1.AltForm())
					msg += '|yes|no'
					msg += getmsg2_short(entry1,star)
					print(msg)
				elif entry2.Probabilities(star) > 0:
					msg = header + getspecies_short(entry2.Species(),entry2.IsGigantamax(),entry2.AltForm())
					msg += '|no|yes'
					msg += getmsg2_short(entry2,star)
					print(msg)
	print('{{catch/footer|red}}')
elif OneTable:
	print('{| class="roundy bg-Sw bd-Sh" style="text-align:center; margin:auto; border:3px solid')
	print('! Pokémon !! Rate !! Games !! Level !! Flawless<br>IVs !! Shield !! Dynamax<br>Level !! Dynamax<br>Boost !! Moves  !! Drop  !! Bonus !! Comment')
	header = '|- style="background:white"\n'
	for star in range(5):
		star = 4 - star
		print('|- style="background:#7dd6ea"\n! colspan="13" | ' + getstars(star))
		for ii in range(tablelength):
			ii = tablelength - 1 - ii
			entry1 = eventencounter.Tables(0).Entries(ii)
			if entry1.Probabilities(star) > 0:
				entry2 = eventencounter.Tables(1).Entries(ii)
				if entry1.Species() == entry2.Species() and entry1.AltForm() == entry2.AltForm() and entry1.IsGigantamax() == entry2.IsGigantamax() and entry1.ShinyFlag() == entry2.ShinyFlag():
					# Same entry
					msg = header + getmsg1(entry1,star)
					msg += '{{GameIconzh/8|SWSH}} || '
					msg += getmsg2(entry1,star)
					print(msg)
				else:
					msg = header + getmsg1(entry1,star)
					msg += '{{GameIconzh/8|SW}} || '
					msg += getmsg2(entry1,star)
					print(msg)
					msg = header + getmsg1(entry2,star)
					msg += '{{GameIconzh/8|SH}} || '
					msg += getmsg2(entry2,star)
					print(msg)
	print('|}\n\n\n')
else: # Full version
	print('__TOC__')
	for ii in range(eventencounter.TablesLength()):
		table = eventencounter.Tables(ii)
		ver = 'Sword' if table.GameVersion() == 1 else 'Shield'
		ver2 = 'SW' if table.GameVersion() == 1 else 'SH'
		print('=={{game|'+ ver2 +'}}==') 
		print('{| class="bg-'+ ver +' bd-'+ ver +' roundy at-c eplist"')
		print('|- class="bgl-'+ ver +'"') 
		print('! ★(Rate) !! Pokémon !! Level !! Flawless<br>IVs !! Shield !! Dynamax<br>Level !! Dynamax<br>Boost !! Moves  !! Drop  !! Bonus !! Comment')
		print('|- style="background:white"')
		print(f'! colspan="11" | Nest ID：{table.TableID()}')
		for jj in range(table.EntriesLength()):
			entry = table.Entries(table.EntriesLength() - jj - 1)
			rank = np.nonzero(entry.ProbabilitiesAsNumpy())[0]
			if rank.size > 0:
				print('|- style="background:white"')
				msg = '| '
				for r in rank:
					msg += getstars(r) + '<br>(' + f'{entry.Probabilities(r)}%)<br>'
				msg =  msg[:-4] + ' || ' 
				msg += getspecies(entry.Species(),entry.IsGigantamax(),entry.AltForm(),entry.ShinyFlag() == 2) + ' || '
				msg += getmsg2(entry,rank)
				print(msg)
		print('|}\n')
	print('==Check==\n{{Wild area news list}}\n\n')
if DumpCrystal:
	tablelength = crystalencounter.Tables(0).EntriesLength()
	if ShortVersion:
		header = '{{catch/entry8|'
		for ii in range(tablelength):
			entry1 = crystalencounter.Tables(0).Entries(ii)
			if entry1.Species() == 0:
				continue
			rank = Den.getCrystalRank(entry1.Level())
			entry2 = crystalencounter.Tables(1).Entries(ii)
			if entry1.Species() == entry2.Species() and entry1.AltForm() == entry2.AltForm() and entry1.IsGigantamax() == entry2.IsGigantamax() and entry1.ShinyFlag() == entry2.ShinyFlag():
				# Same entry
				msg = header + getspecies_short(entry1.Species(),entry1.IsGigantamax(),entry1.AltForm())
				msg += '|' + gettype_short(entry1.Species(),entry1.AltForm())
				msg += getform_short(entry1.Species(),entry1.IsGigantamax(),entry1.AltForm(),False)
				msg += f'|yes|yes|Throw Dynamax Crystals|{entry1.Level()}|{{{{tt|one|Redeem serial number}}}}}}}}'
				print(msg)
			else:
				msg = header + getspecies_short(entry1.Species(),entry1.IsGigantamax(),entry1.AltForm())
				msg += '|' + gettype_short(entry1.Species(),entry1.AltForm())
				msg += f'|yes|no|Throw Dynamax Crystals|{entry1.Level()}|{{{{tt|one|Redeem serial number}}}}}}}}'
				print(msg)
				msg = header + getspecies_short(entry1.Species(),entry1.IsGigantamax(),entry1.AltForm())
				msg += '|' + gettype_short(entry2.Species(),entry2.AltForm())
				msg += f'|no|yes|Throw Dynamax Crystals|{entry1.Level()}|{{{{tt|one|Redeem serial number}}}}}}}}'
				print(msg)
	else:
		eventstyle = ''
		print('{| class="roundy bg-Sw bd-Sh" style="text-align:center; margin:auto; border:3px solid')
		print('! Dynamax Crystal !! Pokémon !! ★ !! Games !! Level !! IVs !! Shield !! Dynamax<br>Level !! Dynamax<br>Boost !! Moves  !! Drop  !! Bonus !! Comment')
		header0 = '|- style="background:white"\n'
		for ii in range(tablelength):
			header = header0 + '| {{i|' + pmtext.items[1279+ii] + '}} |'
			entry1 = crystalencounter.Tables(0).Entries(ii)
			if entry1.Species() == 0:
				continue
			rank = Den.getCrystalRank(entry1.Level())
			entry2 = crystalencounter.Tables(1).Entries(ii)
			if entry1.Species() == entry2.Species() and entry1.AltForm() == entry2.AltForm() and entry1.IsGigantamax() == entry2.IsGigantamax() and entry1.ShinyFlag() == entry2.ShinyFlag():
				# Same entry
				msg = header + getmsg1(entry1,rank,isCrystal = True)
				msg += '{{GameIconzh/8|SWSH}} || '
				msg += getmsg2(entry1,rank,isCrystal = True)
				print(msg)
			else:
				msg = header + getmsg1(entry1,rank,isCrystal = True)
				msg += '{{GameIconzh/8|SW}} || '
				msg += getmsg2(entry1,rank,isCrystal = True)
				print(msg)
				msg = header + getmsg1(entry2,rank,isCrystal = True)
				msg += '{{GameIconzh/8|SH}} || '
				msg += getmsg2(entry2,rank,isCrystal = True)
				print(msg)
		print('|}\n\n\n')
