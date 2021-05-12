from stlacore import *
from random import random, randrange
from copy import deepcopy

dernierHid = 0
def affiche_console(historique):
    global dernierHid
    for i in range(dernierHid, len(historique)):
        print(*historique[i][:-1])
    dernierHid = len(historique)

from itertools import permutations, product

def verifie_draft(choixJoueur, listesChoix):
    for possibilites in product(*listesChoix):
        if tuple(choixJoueur) in permutations(possibilites):
            return True
    return False


def lance_jeu(joueur1, joueur2):
    joueurs = [joueur1, joueur2]
    
    etatJeu = EtatJeu()
    
    dernierPersonnage = list(curseur.execute("SELECT MAX(pid) FROM capacites WHERE EXISTS (SELECT 1 FROM occurences WHERE occurences.cid = capacites.cid)"))[0][0]
    
    listesChoix = [[1+randrange(dernierPersonnage) for j in range(2)] for i in range(5)]
    
    for j in range(2):
        try:
            choixJoueur = joueurs[j].draft(listesChoix)
        except:
            print("Erreur à l'exécution du draft pour le joueur ", j)
            choixJoueur = [liste[0] for liste in listesChoix]
            
        # Draft incorrect, on remplace par le premier choix de chaque liste de choix
        if not verifie_draft(choixJoueur, listesChoix):
            print("Draft incorrect pour le joueur ", j)
            choixJoueur = [liste[0] for liste in listesChoix]
        etatJeu.equipes[j] = initialise_equipe([None, choixJoueur[1], None, choixJoueur[3], None, choixJoueur[0], None, choixJoueur[2], None, choixJoueur[4]], j)
    memo = [None, None]
    while True:
        resultat = etatJeu.debut_de_tour()
        if resultat != PRET_AU_COMBAT:
            # affiche_console(etatJeu.historique)
            return resultat
        j = etatJeu.doitJouer.equipe
        #try:
        if True:
            cibleAdverse, cibleAlliee, i, memo[j] = joueurs[j].tour_de_jeu(deepcopy(etatJeu), memo[j])
        #except:
            #print("Erreur à l'exécution du tour de jeu du joueur", j)
            #exit()
        etatJeu.change_cible_adverse(coords(cibleAdverse), j)
        etatJeu.change_cible_alliee(coords(cibleAlliee), j)
        
        
        if etatJeu.doitJouer.capacites[i].attente != 0:
            i = 0
        
        etatJeu.applique_capacite(etatJeu.doitJouer.capacites[i], etatJeu.doitJouer)
        
        etatJeu.fin_de_tour()
        # affiche_console(etatJeu.historique)
    


import stlaia, stlaiav2, stlaiav3, stlaiarandom
import stlahumain

for k in range(10):
	print(["v2","v1"][lance_jeu(stlaiav2,stlaia)], " gagne")
