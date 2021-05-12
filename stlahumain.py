# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 13:48:36 2020

@author: lj
"""

from stlacore import *

def draft(listesChoix):
    print(listesChoix)
    *composition, = map(int, input("Composition : séparés par des espaces?").split())
    return composition
    
def tour_de_jeu(etatJeu, memo):
    monEquipe = etatJeu.doitJouer.equipe
    for j in monEquipe, 1-monEquipe:
        print(["Equipe alliée", "Equipe adverse"][j!=monEquipe])
        for emplacement, personnage in enumerate(etatJeu.equipes[j]):
            if personnage!=None:
                print(emplacement, personnage.nom, personnage.vie, personnage.jauge//10, "%")
    print("Personnage à jouer:")
    print(etatJeu.doitJouer.emplacement, etatJeu.doitJouer.nom)
    for c, capacite in enumerate(etatJeu.doitJouer.capacites):
        print(c, capacite.description, "(Recharge :",capacite.recharge, ", Attente : ", capacite.attente,")")
    try:
        cibleAlliee = int(input("Cible alliee?"))
    except:
        cibleAlliee = 5
    
    try:
        cibleAdverse = int(input("Cible adverse?"))
    except:
        cibleAdverse = 5
    
    try:
        capacite = int(input("Capacite?"))
    except:
        capacite = 0
    return cibleAlliee, cibleAdverse, capacite, memo
