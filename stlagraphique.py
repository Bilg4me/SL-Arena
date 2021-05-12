from stlacore import *
from copy import deepcopy
import pygame
from random import random, randrange
import sqlite3

# Statut du jeu
EJ_CHOIX_EQUIPE = 0
EJ_COMBAT = 1
EJ_VICTOIRE = 2
EJ_DEFAITE = 3
EJ_CHARGEMENT_ARENE = 4
EJ_CHANGE_TOUR = 5

# Constantes liées à l'affichage
FENETRE_LARGEUR = 1024
FENETRE_HAUTEUR = 500
FENETRE_CARRE = FENETRE_HAUTEUR//5
FENETRE_HAUTEUR_CONSOLE = 200

def interieur(rectangle, coords):
    x, y = coords
    return rectangle[0] <= x <= rectangle[0] + rectangle[2] and rectangle[1] <= y <= rectangle[1] + rectangle[3]

def affiche_choix_equipe(fenetre, equipe):
    return [] # renvoie une liste de couples (rectangle, reaction)
    
def traitement_clique(gui):
    x,y = pygame.mouse.get_pos()
    for rectangle, reaction in gui:
        if interieur(rectangle, (x,y)):
            reaction()
            return

def affiche_combat_vignette(fenetre, p, rectVignette, vaJouer=False):
    textenomombre = policePetite.render(p.nom, False, black)
    largeur = textenomombre.get_width()
    fenetre.blit(textenomombre,(2+rectVignette[0]+rectVignette[2]//2-largeur//2,2+rectVignette[1]))
    
    textenom = policePetite.render(p.nom, False, white if not vaJouer else orange)
    largeur = textenom.get_width()
    fenetre.blit(textenom,(rectVignette[0]+rectVignette[2]//2-largeur//2,rectVignette[1]))
    hauteurCumulee = textenom.get_height()
    
    largeurBarre = 8*FENETRE_CARRE//10
    hauteurBarre = FENETRE_CARRE//6
    
    rect = (rectVignette[0]+FENETRE_CARRE//10, rectVignette[1]+hauteurCumulee, largeurBarre, hauteurBarre)
    
    pygame.draw.rect(fenetre, black, (rect[0]+2, rect[1]+2, rect[2], rect[3]))
    pygame.draw.rect(fenetre, white, rect)
    pygame.draw.rect(fenetre, green, (rect[0]+2, rect[1]+2, (rect[2]-4)*p.vie//p.viebase, rect[3]-4))
    
    textepv = policeTresPetite.render(str(p.vie), False, black)
    largeur = textepv.get_width()
    fenetre.blit(textepv,(rect[0]+rect[2]//2-largeur//2,rect[1]))
    
    
    hauteurCumulee += rect[3] + 4
    
    rect = (rectVignette[0]+FENETRE_CARRE//10, rectVignette[1]+hauteurCumulee, largeurBarre, hauteurBarre)
    
    pygame.draw.rect(fenetre, black, (rect[0]+2, rect[1]+2, rect[2], rect[3]))
    pygame.draw.rect(fenetre, white, rect)
    pygame.draw.rect(fenetre, yellow, (rect[0]+2, rect[1]+2, (rect[2]-4)*p.jauge//MAX_JAUGE, rect[3]-4))

    hauteurCumulee += textepv.get_height()
    
    texterecharge = policeTresPetite.render(str(int(p.jauge*100/MAX_JAUGE))+"%", False, black)
    largeur = texterecharge.get_width()
    fenetre.blit(texterecharge,(rect[0]+rect[2]//2-largeur//2,rect[1]))
    
    largeurCumulee = 10
    for (eid, intensite, duree) in p.effets:
        texteEffet = policeTresPetite.render(symboles[eid]+"("+str(duree)+")", False, white)
        largeur = texteEffet.get_width()
        fenetre.blit(texteEffet, (rectVignette[0]+largeurCumulee, rectVignette[1]+hauteurCumulee))
        largeurCumulee+=largeur
        
def affiche_combat_capacite(fenetre, capacite, rect):
    pygame.draw.rect(fenetre, marron , (rect[0]-3, rect[1]-3, rect[2]+6, rect[3]+6))
    pygame.draw.rect(fenetre, cyan if capacite.attente==0 else grey, rect)
    textedescription = policePetite.render(capacite.description, False, black)
    largeur = textedescription.get_width()
    hauteur = textedescription.get_height()
    
    fenetre.blit(textedescription,(rect[0]+rect[2]//2-largeur//2,rect[1]))
    for i in range(capacite.recharge+1):
        pygame.draw.rect(fenetre, black, (rect[0]+10*(i+1), rect[1]+hauteur, 8, hauteur))
        pygame.draw.rect(fenetre, red if i > capacite.recharge-capacite.attente else green, (rect[0]+10*(i+1)+1, rect[1]+hauteur+1, 4, hauteur-4))
        
    hauteurCumulee = 0
    for occu in capacite.occurences:
        textedescription = policePetite.render(phrasesEffets[occu.eid]+" "+phrasesCibles[occu.ciblage]+(" (proba : "+str(occu.probabilite)+")" if occu.probabilite<1 else ""), False, [green, red][occu.cible])
        hauteur = textedescription.get_height()
        
        fenetre.blit(textedescription, (rect[0]+rect[2]+10, rect[1]+hauteurCumulee))
        hauteurCumulee += hauteur
    
def affiche_console(fenetre, historique):
    hauteurCumulee = 0
    for i in range(len(historique)-1, -1, -1):
        texteConsole = policePetite.render(historique[i][0], False, historique[i][1])
        hauteurCumulee += texteConsole.get_height()
        if hauteurCumulee >= FENETRE_HAUTEUR_CONSOLE:
            break
        fenetre.blit(texteConsole, (0,FENETRE_HAUTEUR + FENETRE_HAUTEUR_CONSOLE-hauteurCumulee))
    pygame.draw.rect(fenetre, marron, (0, FENETRE_HAUTEUR, FENETRE_LARGEUR, 4))

def choix_capacite(etatJeu, capacite, lanceur):
    global statut
    etatJeu.applique_capacite(capacite, lanceur)
    statut = EJ_CHANGE_TOUR
    
def affiche_combat(fenetre, etatJeu, doitJouer):
    pygame.draw.rect(fenetre, lightgreen, (0, 0, FENETRE_LARGEUR, FENETRE_HAUTEUR))
    fenetre.blit(fondCombat, (0, 0))
    rectanglesGui = []
    
    def applique(fonction, arguments):
        def f():
            return fonction(*arguments)
        return f
    
    equipeEnnemie = [etatJeu.equipes[EQ_JOUEUR], etatJeu.equipes[EQ_ADVERSAIRE]][1-doitJouer.equipe]
    
                
    for l in range(5):
        for c in range(2):
            rect = (c*FENETRE_CARRE,l*FENETRE_CARRE, FENETRE_CARRE, FENETRE_CARRE)
            pygame.draw.rect(fenetre, green if (l,c)==etatJeu.donne_cible_alliee(0) else blue if (l+c)%2==0 else cyan, rect)
            p = etatJeu.equipes[EQ_JOUEUR][emplacement((l,c))]
            if p!=None:
                rectanglesGui.append((rect, applique(etatJeu.change_cible_alliee,[(l,c), EQ_JOUEUR])))
                affiche_combat_vignette(fenetre, p, rect, p==doitJouer)
                
            rect = (FENETRE_LARGEUR-(c+1)*FENETRE_CARRE,l*FENETRE_CARRE, FENETRE_CARRE, FENETRE_CARRE)
            pygame.draw.rect(fenetre, red if (l,c)==etatJeu.donne_cible_adverse(0) else blue if (l+c)%2==0 else cyan, rect)
            p = etatJeu.equipes[EQ_ADVERSAIRE][emplacement((l,c))]
            if p!=None:
                provocateurs = etatJeu.donne_provocateurs(1-doitJouer.equipe)
                if provocateurs==[] or emplacement((l,c)) in provocateurs:
                    rectanglesGui.append((rect, applique(etatJeu.change_cible_adverse,[(l,c), EQ_JOUEUR])))
                affiche_combat_vignette(fenetre, p, rect, p==doitJouer)
                
    
    if doitJouer != None and doitJouer.equipe == EQ_JOUEUR:
        texteOmbre = policeGrande.render(doitJouer.nom, False, black)
        largeur = texteOmbre.get_width()
        fenetre.blit(texteOmbre,((FENETRE_LARGEUR-largeur)//2+2,2))
        
        texte = policeGrande.render(doitJouer.nom, False, orange)
        largeur = texte.get_width()
    
        fenetre.blit(texte,((FENETRE_LARGEUR-largeur)//2,0))
        
        
        for i in range(3):
            rect = (FENETRE_CARRE*5//2,100+i*(FENETRE_CARRE+50), FENETRE_CARRE*3//2, FENETRE_CARRE//2)
            affiche_combat_capacite(fenetre, doitJouer.capacites[i], rect)
            if doitJouer.capacites[i].attente == 0:
                rectanglesGui.append((rect, applique(choix_capacite,(etatJeu, doitJouer.capacites[i], doitJouer))))
    affiche_console(fenetre, etatJeu.historique)
    return rectanglesGui

def affiche_victoire(fenetre):
    pygame.draw.rect(fenetre, green, (0, 0, FENETRE_LARGEUR, FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE))    

    texteOmbre = policeTresGrande.render("VICTOIRE", False, black)
    largeur = texteOmbre.get_width()
    hauteur = texteOmbre.get_height()
    
    texte = policeTresGrande.render("VICTOIRE", False, white)
    largeur = texte.get_width()
    hauteur = texte.get_height()
    
    fenetre.blit(texteOmbre,((FENETRE_LARGEUR-largeur)//2+2,(FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE-hauteur)//2+2))
    fenetre.blit(texte,((FENETRE_LARGEUR-largeur)//2,(FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE-hauteur)//2))
    return []

def affiche_defaite(fenetre):
    pygame.draw.rect(fenetre, red, (0, 0, FENETRE_LARGEUR, FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE))    

    texteOmbre = policeTresGrande.render("DEFAITE", False, black)
    largeur = texteOmbre.get_width()
    hauteur = texteOmbre.get_height()
    
    texte = policeTresGrande.render("DEFAITE", False, white)
    largeur = texte.get_width()
    hauteur = texte.get_height()
    
    fenetre.blit(texteOmbre,((FENETRE_LARGEUR-largeur)//2+2,(FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE-hauteur)//2+2))
    fenetre.blit(texte,((FENETRE_LARGEUR-largeur)//2,(FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE-hauteur)//2))
    return []

def lance_jeu():
    global statut
    
    enCours = True

    etatJeu = EtatJeu()

    connexion = sqlite3.connect("stla.sqlite")
    curseur = connexion.cursor()
    dernierPersonnage = list(curseur.execute("SELECT MAX(pid) FROM capacites WHERE EXISTS (SELECT 1 FROM occurences WHERE occurences.cid = capacites.cid)"))[0][0]
    
    listesChoix = [[1+randrange(dernierPersonnage) for j in range(2)] for i in range(5)]
    # initialisation de l'IA
    choixJoueur = ia.draft(listesChoix)
    etatJeu.equipes[1] = initialise_equipe([None, choixJoueur[1], None, choixJoueur[3], None, choixJoueur[0], None, choixJoueur[2], None, choixJoueur[4]], 1)
    memoIA = None
    # choix du joueur = choix de l'IA pour faire simple
    etatJeu.equipes[0] = initialise_equipe([None, choixJoueur[1], None, choixJoueur[3], None, choixJoueur[0], None, choixJoueur[2], None, choixJoueur[4]], 0)
    statut = EJ_CHANGE_TOUR
    
    while enCours:
        fenetre.fill(black) 
        if statut == EJ_CHOIX_EQUIPE:
            gui = affiche_choix_equipe(fenetre, etatJeu)
        elif statut == EJ_CHANGE_TOUR:
            etatJeu.fin_de_tour()
            resultat = etatJeu.debut_de_tour()
            if resultat == VICTOIRE_J2 or resultat == EGALITE:
                statut = EJ_DEFAITE
            elif resultat == VICTOIRE_J1:
                statut = EJ_VICTOIRE
            else:
                j = etatJeu.doitJouer.equipe
                # si c'est le joueur adverse, jouer aléatoirement
                if j == EQ_ADVERSAIRE:
                    cibleAdverse, cibleAlliee, i, memoIA = ia.tour_de_jeu(deepcopy(etatJeu), memoIA)
                    etatJeu.change_cible_adverse(coords(cibleAdverse), j)
                    etatJeu.change_cible_alliee(coords(cibleAlliee), j)
                                    
                    if etatJeu.doitJouer.capacites[i].attente != 0:
                        i = 0
                    
                    etatJeu.applique_capacite(etatJeu.doitJouer.capacites[i], etatJeu.doitJouer)
                # si c'est le joueur, lui présenter l'interface de combat
                else:
                    statut = EJ_COMBAT
                continue
        elif statut == EJ_COMBAT:
            gui = affiche_combat(fenetre, etatJeu, etatJeu.doitJouer)
        elif statut == EJ_VICTOIRE:
            gui = affiche_victoire(fenetre)
        elif statut == EJ_DEFAITE:
            gui = affiche_defaite(fenetre)
            
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                enCours = False
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONUP:
                traitement_clique(gui)

pygame.init()

pygame.display.set_caption("Saint Louis' Arena")

pygame.font.init()

fondCombat = pygame.image.load("blackboard.jpg")

policeTresPetite = pygame.font.SysFont('Comic Sans MS', 12)
policePetite = pygame.font.SysFont('Comic Sans MS', 16)
policeGrande = pygame.font.SysFont('Comic Sans MS', 30)
policeTresGrande = pygame.font.SysFont('Comic Sans MS', 60)

fenetre = pygame.display.set_mode((FENETRE_LARGEUR, FENETRE_HAUTEUR+FENETRE_HAUTEUR_CONSOLE))

import stlaia as ia
lance_jeu()