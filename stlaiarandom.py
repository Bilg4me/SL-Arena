# -*- coding: utf-8 -*-
"""
Created on Oct 2020

@author: bb

"""

from stlacore import *

# Profils et ciblage 

EF_OFFENSIVE = [EF_DEGATS, EF_ENDORMI, EF_SONNE, EF_DEFENSE_MOINS, EF_DEGATS_DOT, EF_VITESSE_MOINS, EF_JAUGE_MOINS]
EF_STRATEGIQUE = [EF_PROVOCATION,EF_ESQUIVE_GARANTIE,EF_TACTIQUE,EF_ASSISTANCE]
EF_SUPPORT = [EF_SOIN,EF_DEFENSE_PLUS,EF_SOINS_DOT,EF_VITESSE_PLUS,EF_JAUGE_PLUS] + EF_STRATEGIQUE
CIBLAGE_ZONE = [CI_TOUS,CI_VOISINNAGE,CI_RANGEE]
CIBLAGE_PRECIS = [CI_UNIQUE, CI_LANCEUR]

# constantes

VIE_MIN, VIE_MAX = 2000,3500
DEF_MIN, DEF_MAX = 70,200
VITESSE_MIN, VITESSE_MAX = 75,125
ESQ_MIN, ESQ_MAX = 0,25

def pourcentage(mini,maxi, valeur):
	return (valeur - mini) / (maxi - mini)

def profiler(pid):
	profil = ""
	pOff = 0
	pSupp = 0
	pCiblé = 0
	pZone = 0
	pPrivilege = False

	perso = charge_personnage(pid, 0, 0)
	for capacity in perso.capacites:
		for effets in capacity.occurences:
			if effets.eid in EF_OFFENSIVE or effets.cible == CI_ADVERSAIRE:
				pOff += 1
			elif effets.eid in EF_SUPPORT or effets.cible == CI_JOUEUR:
				pSupp += 1
			if effets.ciblage in CIBLAGE_ZONE:
				pZone += 1
			elif effets.ciblage in CIBLAGE_PRECIS:
				pCiblé += 1
			if effets.eid in EF_STRATEGIQUE:
				pPrivilege = True

	if pOff > pSupp:
		profil += "OFFENSIF"
	else:
		profil += "SUPPORT"

	profil += "/"

	if  pCiblé > pZone :
		profil += "PRECIS"
	else:
		profil += "ZONE"

	if pPrivilege:
		profil += "/*"

	return profil

def puissanceStats(perso):
	pvie = pourcentage(VIE_MIN , VIE_MAX, perso.vie)
	pdefense = pourcentage(DEF_MIN, DEF_MAX, perso.defense)
	pvitesse = pourcentage(VITESSE_MIN, VITESSE_MAX, perso.vitesse)
	pesquive = pourcentage(ESQ_MIN, ESQ_MAX, perso.esquive)

	if "OFFENSIF" in profiler(perso.pid):
		return (pvitesse, pesquive, pvie, pdefense)
	else:
		return (pvie, pdefense, pesquive, pvitesse)

# TODO : Traiter différement le cas ou intensite est nulle
def puissanceCapacite(perso):
	ratio = []
	for capacity in perso.capacites:
		cout = capacity.recharge + 1
		rentabilite = 0
		for effets in capacity.occurences:
			rentabilite += float(effets.probabilite) * effets.intensite

		ratio.append(rentabilite/cout)
	return *ratio,

def puissance(pid):
	perso = charge_personnage(pid, 0, 0)
	pStats = puissanceStats(perso)
	pCapac = puissanceCapacite(perso)
	return pCapac + pStats

def draft(listesChoix):
	
	equipe = []
	traités = []
	off,supp,prec,zone = 0,0,0,0
	
	for [p1,p2] in listesChoix:
		
		a1 = profiler(p1)
		a2 = profiler(p2)		
		
		# 1 - selection des privileges
		if '*' in a1 and not (p1 in equipe):
			traités.append([p1,p2])
			equipe.append(p1)
			
		elif '*' in a2 and not (p2 in equipe):
			traités.append([p1,p2])
			equipe.append(p2)
		
		# 2 - isoprofils 

		elif a1[0] == a2[0] : #(premiere lettre suffit)
			traités.append([p1,p2])
			if puissance(p1) > puissance(p2):
				equipe.append(p1)
			else:
				equipe.append(p2)
				
		
	
	# 3 - On regarde les perso restants
	persoRestants = [ [p1,p2] for [p1,p2] in listesChoix if not ([p1,p2] in traités) ]
	
	# 4 - Equilibrage des profils pour les persos restants
	
	# Comptabilise le nb d'off et de supp
	for p in equipe:
		a = profiler(p)
		if "OFFENSIF" in a:
			off += 1
		else:
			supp += 1
		if "PRECIS" in a:
			prec += 1
		else:
			zone += 1
			
	# On choisit les persoRestants
	for [p1,p2] in persoRestants:
		a1 = profiler(p1)
		a2 = profiler(p2)
	
		if off < supp :
			if "OFFENSIF" in a1:
				equipe.append(p1)
			else :
				equipe.append(p2)
			off += 1
		
		elif off == supp:
			if zone < prec:
				if "ZONE" in a1:
					equipe.append(p1)
				else:
					equipe.append(p2)
				zone += 1
			else:
				if "ZONE" in a1:
					equipe.append(p2)
				else:
					equipe.append(p1)
				prec += 1
			
		else:
			if "OFFENSIF" in a1:
				equipe.append(p2)
			else :
				equipe.append(p1)
			
			supp += 1
			
	return equipe

# tour de jeu

def respectRegles(etatJeu):
	persoJouant = etatJeu.doitJouer
	adversaire = 1 - persoJouant.equipe
	
	capacitesDispo_emplacement = []
	JoueurAttaquable_emplacement = []
	provocateurs = etatJeu.donne_provocateurs(adversaire)
	
	# capacités disponible
	for k in range(3):
		if persoJouant.capacites[k].attente == 0:
			capacitesDispo_emplacement.append(k)
		
	# adversaires attaquable
	if provocateurs == []:
		JoueurAttaquable_emplacement = [1,3,5,7,9]
	else:
		JoueurAttaquable_emplacement = provocateurs
		
	return (JoueurAttaquable_emplacement, capacitesDispo_emplacement)

def tour_de_jeu(etatJeu,memo):
	emplacementCibleAlliée = choice([1,3,5,7,9])
	a,b = respectRegles(etatJeu)
	emplacementCibleAdverse,emplacementCapacité = choice(a),choice(b)
		
	return emplacementCibleAdverse , emplacementCibleAlliée, emplacementCapacité, None

